import os
import shutil
from datetime import datetime
import CamView.Settings as S


def MoveFiles():
    source = S.Directories[0]
    destination = S.FinalPaths[0]

    os.makedirs(source, exist_ok=True)
    date_folder = datetime.now().strftime('%Y-%m-%d')
    final_dest = os.path.join(destination, date_folder)
    os.makedirs(final_dest, exist_ok=True)

    for name in os.listdir(source):
        source_path = os.path.join(source, name)
        if os.path.isfile(source_path):
            destination_path = os.path.join(final_dest, name)
            try:
                shutil.move(source_path, destination_path)
                print(f"moved to {destination_path}")
            except Exception as e:
                print(f"Failed to move {source_path}: {e}")


def checkFiles():
    MoveFiles()
