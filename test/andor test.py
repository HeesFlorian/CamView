# Functions for the Andor Camera

from pylablib import par
par[r"devices/dlls/andor_sdk2"] = r"C:\Program Files\Andor SDK"
from pylablib.devices import Andor
import os
import time
import threading
from PIL import Image
from datetime import datetime

status_callback = lambda camera, status: None
stop_event = threading.Event()
acquisition_thread = None


def get_cameras_number():
    return Andor.get_cameras_number_SDK2()

print("Number of cameras:", get_cameras_number())