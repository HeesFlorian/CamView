import sys
from PyQt5.QtWidgets import QApplication
from CamView.GUI import CamViewWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = CamViewWindow()
    mainWindow.show()
    sys.exit(app.exec_())