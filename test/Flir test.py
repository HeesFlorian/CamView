from time import time
import time

import PySpin

camSys = PySpin.System.GetInstance()
camList = camSys.GetCameras()
cam = camList.GetByIndex(0)
cam.Init()
cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)
cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
cam.BeginAcquisition()
time.sleep(0.1)
cam.TriggerSoftware.Execute()
time.sleep(0.1)
image = cam.GetNextImage(1000)
cam.EndAcquisition()
cam.DeInit()

print(image)