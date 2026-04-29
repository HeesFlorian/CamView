import PySpin
import time
import numpy as np


def configure_software_trigger(cam):
    nodemap = cam.GetNodeMap()

    # Ensure trigger mode OFF before configuring
    trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
    trigger_mode.SetIntValue(trigger_mode.GetEntryByName('Off').GetValue())

    # Set trigger selector
    trigger_selector = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSelector'))
    trigger_selector.SetIntValue(trigger_selector.GetEntryByName('FrameStart').GetValue())

    # Set software trigger source
    trigger_source = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSource'))
    trigger_source.SetIntValue(trigger_source.GetEntryByName('Software').GetValue())

    # Turn trigger mode ON
    trigger_mode.SetIntValue(trigger_mode.GetEntryByName('On').GetValue())


def take_image(cam):
    nodemap = cam.GetNodeMap()

    cam.BeginAcquisition()

    time.sleep(0.05)  # let camera arm

    # Fire software trigger
    trigger_cmd = PySpin.CCommandPtr(nodemap.GetNode('TriggerSoftware'))
    trigger_cmd.Execute()

    # Grab image (timeout 2000 ms)
    image_result = cam.GetNextImage(2000)

    if image_result.IsIncomplete():
        print("❌ Image incomplete")
        image_result.Release()
        cam.EndAcquisition()
        return None

    image = image_result.GetNDArray()

    image_result.Release()
    cam.EndAcquisition()

    return image


def main():
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    if cam_list.GetSize() == 0:
        print("❌ No cameras found")
        return

    cam = cam_list.GetByIndex(0)

    try:
        cam.Init()
        print("✅ Camera initialized")

        configure_software_trigger(cam)
        print("✅ Software trigger configured")

        img = take_image(cam)

        if img is None:
            print("❌ No image received")
        else:
            print("✅ Image captured!")
            print("Shape:", img.shape)
            print("Dtype:", img.dtype)
            print("Min/Max:", np.min(img), np.max(img))

    except Exception as e:
        print("❌ Error:", e)

    finally:
        try:
            cam.DeInit()
        except Exception:
            pass
        del cam
        cam_list.Clear()
        system.ReleaseInstance()
        print("🧹 Clean exit")


if __name__ == "__main__":
    main()