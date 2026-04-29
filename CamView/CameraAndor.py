# Functions for the Andor Camera

from pylablib import par
par[r"devices/dlls/andor_sdk2"] = r"C:\Program Files\Andor SDK"
from pylablib.devices import Andor
import os
import time
import threading
from PIL import Image
from datetime import datetime
import CamView.Settings as S
import CamView.FolderManagment as fm

status_callback = lambda camera, status: None
stop_event = threading.Event()
acquisition_thread = None


def get_cameras_number():
    return Andor.get_cameras_number_SDK2()


def init_camera():
    global cam
    try:
        disconnect()
    except Exception:
        pass
    cam = Andor.AndorSDK2Camera()
    cam.set_fan_mode(0)


def initialize_camera():
    """Initialize camera without starting acquisition"""
    global cam
    try:
        disconnect()
    except Exception:
        pass
    cam = Andor.AndorSDK2Camera()
    cam.set_fan_mode(0)
    # Camera is now initialized but not in acquisition mode


def disconnect():
    global cam
    try:
        cam.close()
    except Exception:
        pass
    cam = None


def get_Temp():
    return int(cam.get_temperature()), cam.get_settings()["cooler"], cam.get_settings()["fan_mode"]


def enable_cooling():
    cam.set_fan_mode(0)


def Set_Temp(Temp):
    cam.set_temperature(int(Temp))
    print(f"Temp set to {Temp}")


def get_series_prefix():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def take_single_image():
    cam.set_exposure(S.ExposureA / 1e6)
    cam.set_EMCCD_gain(S.GainA)
    cam.set_trigger_mode('software')
    cam.start_acquisition()
    cam.send_software_trigger()
    cam.wait_for_frame(since='start', nframes=1, timeout=10)
    image = cam.read_newest_image()
    cam.stop_acquisition()  # Stop acquisition after taking the image
    print("Single image captured")
    print(f"Image shape: {image.shape}, dtype: {image.dtype}")
    return image


def Start_acquisition():
    status_callback('andor', 'Initializing')
    cam.set_acquisition_mode(5)
    cam.set_trigger_mode('ext')
    cam.set_read_mode('image')
    cam.setup_shutter('auto')
    cam.set_exposure(S.ExposureA / 1e6)
    cam.set_EMCCD_gain(S.GainA)

    while not stop_event.is_set():
        status_callback('andor', 'Waiting for external trigger')
        cam.start_acquisition('cont')

        try:
            cam.wait_for_frame(since='start', nframes=3, timeout=None)
        except Exception as e:
            if stop_event.is_set():
                break
            continue

        if stop_event.is_set():
            break

        Images = cam.read_multiple_images((0, 3))
        prefix = get_series_prefix()
        with S.counter_lock:
            run_index = S.counter
            S.counter += 1

        save_dir = S.Directories[0]
        os.makedirs(save_dir, exist_ok=True)

        number = f"{run_index:04d}"
        cameratype = 'andor'
        types = ['atoms', 'dark', 'background']

        for i, image in enumerate(Images):
            filename = os.path.join(save_dir, f"{prefix}_{number}_{cameratype}_{types[i]}.tif")
            Image.fromarray(image).save(filename)

        fm.MoveFiles()
        status_callback('andor', 'Ready and waiting for trigger')

    try:
        cam.stop_acquisition()
    except Exception:
        pass
    status_callback('andor', 'Stopped')


def Start_acquisition_thread():
    global acquisition_thread
    stop_event.clear()
    acquisition_thread = threading.Thread(target=Start_acquisition)
    acquisition_thread.daemon = True
    acquisition_thread.start()


def Stop_acquisition():
    global acquisition_thread
    stop_event.set()
    try:
        cam.stop_acquisition()
    except Exception:
        pass
    if acquisition_thread is not None and acquisition_thread.is_alive():
        acquisition_thread.join(timeout=1)
