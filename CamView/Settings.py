import os
import re
import threading

# Global parameters and runtime state
counter = 0
counter_lock = threading.Lock()

# Camera settings
ExposureP = 0.001  # [s]
ExposureA = 1000  # [µs]
ExposureF = 1000  # [µs]
GainA = 100  # EMCCD gain
GainF = 0
FormatF = None
try:
    import PySpin
    FormatF = PySpin.PixelFormat_Mono8
except Exception:
    pass

# Master storage paths
Directories = [r"C:\ProgramData\CamView\IMG"]
FinalPaths = [r"C:\ProgramData\CamView\Final"]


def checkCounter():
    os.makedirs(FinalPaths[0], exist_ok=True)
    regex = re.compile(r'^\d{4}_(\d+)_.*\\.tif$', re.IGNORECASE)
    counter_values = []
    for name in os.listdir(FinalPaths[0]):
        if os.path.isfile(os.path.join(FinalPaths[0], name)):
            match = regex.match(name)
            if match:
                counter_values.append(int(match.group(1)))
    return max(counter_values) + 1 if counter_values else 0
