import os
import time
import threading
from datetime import datetime

import PySpin
from PIL import Image

import CamView.Settings as S
import CamView.FolderManagment as fm


# =========================
# GLOBAL STATE
# =========================
status_callback = lambda camera, status: None
stop_event = threading.Event()
acquisition_thread = None

cam = None
system = None


# =========================
# CAMERA INIT / CLEANUP
# =========================
def init_camera():
    global cam, system

    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    if cam_list.GetSize() == 0:
        raise RuntimeError("No FLIR cameras found")

    cam = cam_list.GetByIndex(0)
    cam.Init()

    reset_camera()


def disconnect():
    global cam, system

    stop_event.set()

    try:
        cam.EndAcquisition()
    except:
        pass

    try:
        cam.DeInit()
    except:
        pass

    try:
        system.ReleaseInstance()
    except:
        pass

    cam = None
    system = None


def reset_camera():
    """Loads camera default user settings safely"""
    try:
        cam.UserSetSelector.SetValue(PySpin.UserSetSelector_Default)
        cam.UserSetLoad()
    except:
        pass


# =========================
# SAFE MODE SWITCH HELPERS
# =========================
def _set_trigger_off():
    node = cam.GetNodeMap()
    trig_mode = PySpin.CEnumerationPtr(node.GetNode("TriggerMode"))
    trig_mode.SetIntValue(trig_mode.GetEntryByName("Off").GetValue())


def _set_software_trigger():
    node = cam.GetNodeMap()

    trig_selector = PySpin.CEnumerationPtr(node.GetNode("TriggerSelector"))
    trig_selector.SetIntValue(trig_selector.GetEntryByName("FrameStart").GetValue())

    trig_source = PySpin.CEnumerationPtr(node.GetNode("TriggerSource"))
    trig_source.SetIntValue(trig_source.GetEntryByName("Software").GetValue())

    trig_mode = PySpin.CEnumerationPtr(node.GetNode("TriggerMode"))
    trig_mode.SetIntValue(trig_mode.GetEntryByName("On").GetValue())


def _set_external_trigger():
    node = cam.GetNodeMap()

    trig_selector = PySpin.CEnumerationPtr(node.GetNode("TriggerSelector"))
    trig_selector.SetIntValue(trig_selector.GetEntryByName("FrameStart").GetValue())

    trig_source = PySpin.CEnumerationPtr(node.GetNode("TriggerSource"))
    trig_source.SetIntValue(trig_source.GetEntryByName("Line0").GetValue())

    trig_mode = PySpin.CEnumerationPtr(node.GetNode("TriggerMode"))
    trig_mode.SetIntValue(trig_mode.GetEntryByName("On").GetValue())


# =========================
# SINGLE IMAGE (FIXED)
# =========================
def take_single_image():
    global cam

    stop_event.set()  # ensure acquisition thread doesn't interfere
    time.sleep(0.1)

    _set_trigger_off()
    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)

    _set_software_trigger()

    cam.BeginAcquisition()
    time.sleep(0.05)

    node = cam.GetNodeMap()
    trigger_cmd = PySpin.CCommandPtr(node.GetNode("TriggerSoftware"))
    trigger_cmd.Execute()

    image_result = cam.GetNextImage(2000)

    if image_result.IsIncomplete():
        image_result.Release()
        cam.EndAcquisition()
        return None

    img = image_result.GetNDArray()

    image_result.Release()
    cam.EndAcquisition()

    return img


# =========================
# CONTINUOUS ACQUISITION THREAD (FIXED)
# =========================
def Start_acquisition():
    global cam

    stop_event.clear()
    status_callback("flir", "Initializing")

    _set_trigger_off()
    _set_external_trigger()

    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

    status_callback("flir", "Waiting for external trigger")

    while not stop_event.is_set():
        try:
            cam.BeginAcquisition()
        except:
            continue

        try:
            imgs = []

            for _ in range(3):
                img = cam.GetNextImage(1000)
                if img.IsIncomplete():
                    img.Release()
                    continue
                imgs.append(img.GetNDArray())
                img.Release()

            cam.EndAcquisition()

            prefix = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            save_dir = S.Directories[0]
            os.makedirs(save_dir, exist_ok=True)

            with S.counter_lock:
                idx = S.counter
                S.counter += 1

            labels = ["atoms", "dark", "background"]

            for i, im in enumerate(imgs):
                filename = os.path.join(
                    save_dir,
                    f"{prefix}_{idx:04d}_flir_{labels[i]}.tif"
                )
                Image.fromarray(im).save(filename)

            fm.MoveFiles()
            status_callback("flir", "Ready")

        except Exception:
            try:
                cam.EndAcquisition()
            except:
                pass


# =========================
# THREAD CONTROL
# =========================
def Start_acquisition_thread():
    global acquisition_thread

    acquisition_thread = threading.Thread(target=Start_acquisition, daemon=True)
    acquisition_thread.start()


def Stop_acquisition():
    stop_event.set()

    try:
        cam.EndAcquisition()
    except:
        pass