# Functions for the PCO / Pixelfly Camera

from pylablib import par
from pylablib.devices import PCO
par[r'devices/dlls/pco_sc2'] = r"C:\Program Files\Andor SDK"

def get_cameras_number():
    return PCO.get_cameras_number()

print("Number of cameras:", get_cameras_number())