# Functions for the PCO / Pixelfly Camera

from pylablib import par
from pylablib.devices import PCO
par[r'devices/dlls/pco_sc2'] = r"C:\Program Files\Andor SDK"
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
    return PCO.get_cameras_number()


def init_camera():
    global cam
    try:
        disconnect()
    except Exception:
        pass
    cam = PCO.PCOSC2Camera()


def disconnect():
    global cam
    try:
        cam.close()
    except Exception:
        pass
    cam = None


def get_Temp():
    return int(cam.get_temperature()[1])


def get_series_prefix():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def take_single_image():
    cam.set_exposure(S.ExposureF)
    cam.set_trigger_mode('software')
    cam.start_acquisition()
    cam.send_software_trigger()
    image = cam.read_image()
    return image


def Start_acquisition():
    status_callback('pco', 'Initializing')
    cam.setup_acquisition()
    cam.set_trigger_mode('ext')
    cam.set_exposure(S.ExposureP)
    status_callback('pco', 'Waiting for external trigger')

    while not stop_event.is_set():
        cam.start_acquisition()

        try:
            cam.wait_for_frame(since='start', nframes=3, timeout=10)
        except Exception:
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
        cameratype = 'pco'
        types = ['atoms', 'dark1', 'noatoms']

        for i, image in enumerate(Images):
            filename = os.path.join(save_dir, f"{cameratype}_{prefix}_{number}_{types[i]}.tif")
            Image.fromarray(image).save(filename)

        fm.MoveFiles()
        status_callback('pco', 'Ready and waiting for trigger')

    try:
        cam.stop_acquisition()
    except Exception:
        pass
    status_callback('pco', 'Stopped')


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
