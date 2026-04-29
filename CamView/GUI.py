from PyQt5.QtWidgets import QMainWindow, QPushButton, QInputDialog, QMessageBox, QLabel, QVBoxLayout, QWidget, QLineEdit, QHBoxLayout, QFileDialog, QGroupBox, QGridLayout, QSpinBox, QDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
import json
import os
import numpy as np
import CamView.CameraAndor as CamA
import CamView.CameraPCO as CamP
import CamView.CameraFlir as CamF
import CamView.Settings as S

class CameraStatusSignal(QObject):
    status_changed = pyqtSignal(str, str)

class CamViewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_settings()
        S.counter = S.checkCounter()

        self.status_signal = CameraStatusSignal()
        self.status_signal.status_changed.connect(self.on_camera_status)
        CamA.status_callback = self.status_signal.status_changed.emit
        CamP.status_callback = self.status_signal.status_changed.emit
        CamF.status_callback = self.status_signal.status_changed.emit

        self.setWindowTitle('CamView')
        self.setGeometry(200, 150, 900, 520)

        self.save_path_label = QLabel(f"Temp save path: {S.Directories[0]}")
        self.final_path_label = QLabel(f"Final destination: {S.FinalPaths[0]}")
        self.save_path_button = QPushButton('Change save path')
        self.save_path_button.clicked.connect(self.change_save_directory)
        self.open_save_folder_button = QPushButton('Open Save Folder')
        self.open_save_folder_button.clicked.connect(self.open_save_folder)
        self.final_path_button = QPushButton('Change final path')
        self.final_path_button.clicked.connect(self.change_move_directory)
        self.open_final_folder_button = QPushButton('Open Final Folder')
        self.open_final_folder_button.clicked.connect(self.open_final_folder)

        self.andor_status = QLabel('Inactive')
        self.pco_status = QLabel('Inactive')
        self.flir_status = QLabel('Inactive')

        self.andor_status.setAlignment(Qt.AlignCenter)
        self.pco_status.setAlignment(Qt.AlignCenter)
        self.flir_status.setAlignment(Qt.AlignCenter)

        self.andor_start_button = QPushButton('Initialize Andor')
        self.andor_acquire_button = QPushButton('Start Acquisition')
        self.andor_stop_button = QPushButton('Stop Andor')
        self.pco_start_button = QPushButton('Initialize PCO')
        self.pco_acquire_button = QPushButton('Start Acquisition')
        self.pco_stop_button = QPushButton('Stop PCO')
        self.flir_start_button = QPushButton('Initialize FLIR')
        self.flir_acquire_button = QPushButton('Start Acquisition')
        self.flir_stop_button = QPushButton('Stop FLIR')

        self.andor_start_button.clicked.connect(self.initialize_andor)
        self.andor_acquire_button.clicked.connect(self.start_andor_acquisition)
        self.andor_stop_button.clicked.connect(self.stop_andor)
        self.pco_start_button.clicked.connect(self.activate_pco)
        self.pco_acquire_button.clicked.connect(self.start_pco_acquisition)
        self.pco_stop_button.clicked.connect(self.stop_pco)
        self.flir_start_button.clicked.connect(self.activate_flir)
        self.flir_acquire_button.clicked.connect(self.start_flir_acquisition)
        self.flir_stop_button.clicked.connect(self.stop_flir)

        self.andor_stop_button.setEnabled(False)
        self.andor_acquire_button.setEnabled(False)
        self.pco_stop_button.setEnabled(False)
        self.pco_acquire_button.setEnabled(False)
        self.flir_stop_button.setEnabled(False)
        self.flir_acquire_button.setEnabled(False)

        self.camera_poll_timer = QTimer(self)
        self.camera_poll_timer.setInterval(5000)
        self.camera_poll_timer.timeout.connect(self.detect_cameras)
        self.camera_poll_timer.start()
        QTimer.singleShot(100, self.detect_cameras)

        self.temp_update_timer = QTimer(self)
        self.temp_update_timer.setInterval(2000)  # Update every 2 seconds
        self.temp_update_timer.timeout.connect(self.update_andor_temp_fan)
        self.temp_update_timer.start()

        self.andor_exposure = QSpinBox()
        self.andor_exposure.setRange(1, 10000000)  # 1 µs to 10 s
        self.andor_exposure.setValue(S.ExposureA)
        self.andor_exposure.setSuffix(' µs')
        self.andor_exposure.valueChanged.connect(self.update_andor_exposure)

        self.pco_exposure = QSpinBox()
        self.pco_exposure.setRange(1, 10000000)  # 1 µs to 10 s
        self.pco_exposure.setValue(int(S.ExposureP * 1e6))
        self.pco_exposure.setSuffix(' µs')
        self.pco_exposure.valueChanged.connect(self.update_pco_exposure)

        self.flir_exposure = QSpinBox()
        self.flir_exposure.setRange(1, 10000000)  # 1 µs to 10 s
        self.flir_exposure.setValue(S.ExposureF)
        self.flir_exposure.setSuffix(' µs')
        self.flir_exposure.valueChanged.connect(self.update_flir_exposure)

        self.andor_gain = QSpinBox()
        self.andor_gain.setRange(0, 1000)
        self.andor_gain.setValue(S.GainA)
        self.andor_gain.valueChanged.connect(self.update_andor_gain)

        self.flir_gain = QSpinBox()
        self.flir_gain.setRange(0, 100)
        self.flir_gain.setValue(S.GainF)
        self.flir_gain.valueChanged.connect(self.update_flir_gain)

        self.andor_temp_label = QLabel('Temperature: --°C')
        self.andor_fan_label = QLabel('Fan: --')
        self.andor_live_view_button = QPushButton('Live View')
        self.andor_live_view_button.clicked.connect(self.show_andor_live_view)
        self.pco_live_view_button = QPushButton('Live View')
        self.pco_live_view_button.clicked.connect(self.show_pco_live_view)
        self.flir_live_view_button = QPushButton('Live View')
        self.flir_live_view_button.clicked.connect(self.show_flir_live_view)
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.close)

        self.andor_live_view_button.setEnabled(False)
        self.pco_live_view_button.setEnabled(False)
        self.flir_live_view_button.setEnabled(False)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.save_path_label)
        top_layout.addWidget(self.save_path_button)
        top_layout.addWidget(self.open_save_folder_button)
        top_layout.addWidget(self.final_path_label)
        top_layout.addWidget(self.final_path_button)
        top_layout.addWidget(self.open_final_folder_button)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.create_camera_group('Andor Camera', self.andor_status, self.andor_exposure, self.andor_gain, self.andor_temp_label, self.andor_fan_label, self.andor_start_button, self.andor_acquire_button, self.andor_stop_button, self.andor_live_view_button))
        layout.addWidget(self.create_camera_group('PCO Camera', self.pco_status, self.pco_exposure, None, None, None, self.pco_start_button, self.pco_acquire_button, self.pco_stop_button, self.pco_live_view_button))
        layout.addWidget(self.create_camera_group('FLIR Camera', self.flir_status, self.flir_exposure, self.flir_gain, None, None, self.flir_start_button, self.flir_acquire_button, self.flir_stop_button, self.flir_live_view_button))
        layout.addWidget(self.close_button, alignment=Qt.AlignRight)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def create_camera_group(self, title, status_label, exposure_widget, gain_widget, temp_label, fan_label, start_button, acquire_button, stop_button, live_view_button):
        group = QGroupBox(title)
        grid = QGridLayout()
        grid.addWidget(QLabel('Status:'), 0, 0)
        grid.addWidget(status_label, 0, 1, 1, 2)
        grid.addWidget(QLabel('Exposure (µs):'), 1, 0)
        grid.addWidget(exposure_widget, 1, 1, 1, 2)
        row = 2
        if gain_widget is not None:
            grid.addWidget(QLabel('Gain:'), row, 0)
            grid.addWidget(gain_widget, row, 1, 1, 2)
            row += 1
        if temp_label is not None:
            grid.addWidget(temp_label, row, 0, 1, 2)
            row += 1
        if fan_label is not None:
            grid.addWidget(fan_label, row, 0, 1, 2)
            row += 1
        grid.addWidget(start_button, row, 0)
        if acquire_button is not None:
            grid.addWidget(acquire_button, row, 1)
            grid.addWidget(stop_button, row, 2)
            grid.addWidget(live_view_button, row, 3)
        else:
            grid.addWidget(stop_button, row, 1)
            grid.addWidget(live_view_button, row, 2)
        group.setLayout(grid)
        return group

    def load_settings(self):
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                save_dir = settings.get('Directories', [S.Directories[0]])
                final_dir = settings.get('FinalPaths', [S.FinalPaths[0]])
                S.Directories = [save_dir[0]]
                S.FinalPaths = [final_dir[0]]
        except Exception:
            pass

    def save_settings(self):
        settings = {
            'Directories': S.Directories,
            'FinalPaths': S.FinalPaths
        }
        with open('settings.json', 'w') as file:
            json.dump(settings, file)

    def detect_cameras(self):
        # Andor camera detection
        try:
            if CamA.get_cameras_number() == 0:
                self.andor_start_button.setEnabled(False)
                self.andor_acquire_button.setEnabled(False)
                self.andor_status.setText('No Andor camera found')
            else:
                # Enable initialize button if not initialized
                if not self.andor_stop_button.isEnabled():
                    self.andor_start_button.setEnabled(True)
                    self.andor_acquire_button.setEnabled(False)
                if self.andor_status.text().startswith('No Andor') or self.andor_status.text().endswith('check failed'):
                    self.andor_status.setText('Inactive')
        except Exception:
            self.andor_start_button.setEnabled(False)
            self.andor_acquire_button.setEnabled(False)
            self.andor_status.setText('Andor check failed')

        # PCO camera detection
        try:
            if CamP.get_cameras_number() == 0:
                self.pco_start_button.setEnabled(False)
                self.pco_status.setText('No PCO camera found')
            else:
                self.pco_start_button.setEnabled(True)
                if self.pco_status.text().startswith('No PCO') or self.pco_status.text().endswith('check failed'):
                    self.pco_status.setText('Inactive')
        except Exception:
            self.pco_start_button.setEnabled(False)
            self.pco_status.setText('PCO check failed')

        # FLIR camera detection
        try:
            if CamF.get_cameras_number() == 0:
                self.flir_start_button.setEnabled(False)
                self.flir_status.setText('No FLIR camera found')
            else:
                self.flir_start_button.setEnabled(True)
                if self.flir_status.text().startswith('No FLIR') or self.flir_status.text().endswith('check failed'):
                    self.flir_status.setText('Inactive')
        except Exception:
            self.flir_start_button.setEnabled(False)
            self.flir_status.setText('FLIR check failed')

    def change_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Save Directory')
        if directory:
            S.Directories = [directory]
            self.save_path_label.setText(f"Master save path: {directory}")
    def open_save_folder(self):
        try:
            os.startfile(S.Directories[0])
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Cannot open folder:\n{e}')
    def change_move_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Final Destination')
        if directory:
            S.FinalPaths = [directory]
            self.final_path_label.setText(f"Final destination: {directory}")

    def open_final_folder(self):
        try:
            os.startfile(S.FinalPaths[0])
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Cannot open folder:\n{e}')

    def on_camera_status(self, camera, status):
        if camera == 'andor':
            self.andor_status.setText(status)
            if status.startswith('Error') or status == 'Stopped':
                # Camera is still initialized, so enable acquire button
                if hasattr(self, 'andor_acquire_button'):
                    self.andor_acquire_button.setEnabled(True)
                self.andor_stop_button.setEnabled(False)
            elif status == 'Ready and waiting for trigger':
                # Acquisition started, disable acquire button
                if hasattr(self, 'andor_acquire_button'):
                    self.andor_acquire_button.setEnabled(False)
        elif camera == 'pco':
            self.pco_status.setText(status)
            if status.startswith('Error') or status == 'Stopped':
                self.pco_start_button.setEnabled(True)
                self.pco_stop_button.setEnabled(False)
        elif camera == 'flir':
            self.flir_status.setText(status)
            if status.startswith('Error') or status == 'Stopped':
                self.flir_start_button.setEnabled(True)
                self.flir_stop_button.setEnabled(False)

    def initialize_andor(self):
        if CamA.get_cameras_number() > 0:
            self.andor_status.setText('Initializing')
            try:
                CamA.initialize_camera()
                self.andor_status.setText('Initialized')
                self.andor_start_button.setEnabled(False)
                self.andor_acquire_button.setEnabled(True)
                self.andor_stop_button.setEnabled(True)
                self.andor_live_view_button.setEnabled(True)
            except Exception as e:
                QMessageBox.warning(self, 'Andor Error', f'Cannot initialize Andor camera:\n{e}')
                self.andor_status.setText(f'Error: {e}')
        else:
            QMessageBox.information(self, 'Error', 'No Andor camera connected!')

    def start_andor_acquisition(self):
        try:
            CamA.Start_acquisition_thread()
            self.andor_status.setText('Ready and waiting for trigger')
            self.andor_acquire_button.setEnabled(False)
            self.andor_live_view_button.setEnabled(False)
        except Exception as e:
            QMessageBox.warning(self, 'Andor Error', f'Cannot start acquisition:\n{e}')
            self.andor_status.setText(f'Error: {e}')

    def stop_andor(self):
        CamA.Stop_acquisition()
        self.andor_status.setText('Stopping')
        self.andor_start_button.setEnabled(True)
        self.andor_acquire_button.setEnabled(False)
        self.andor_stop_button.setEnabled(False)
        try:
            CamA.disconnect()
        except Exception:
            pass

    def activate_pco(self):
        if CamP.get_cameras_number() > 0:
            self.pco_status.setText('Initializing')
            try:
                CamP.init_camera()
                self.pco_status.setText('Initialized')
                self.pco_start_button.setEnabled(False)
                self.pco_acquire_button.setEnabled(True)
                self.pco_stop_button.setEnabled(True)
                self.pco_live_view_button.setEnabled(True)
            except Exception as e:
                QMessageBox.warning(self, 'PCO Error', f'Cannot activate PCO camera:\n{e}')
                self.pco_status.setText(f'Error: {e}')
        else:
            QMessageBox.information(self, 'Error', 'No PCO camera connected!')

    def start_pco_acquisition(self):
        try:
            CamP.Start_acquisition_thread()
            self.pco_status.setText('Ready and waiting for trigger')
            self.pco_start_button.setEnabled(False)
            self.pco_live_view_button.setEnabled(False)
        except Exception as e:
            QMessageBox.warning(self, 'PCO Error', f'Cannot start acquisition:\n{e}')
            self.pco_status.setText(f'Error: {e}')

    def stop_pco(self):
        CamP.Stop_acquisition()
        self.pco_status.setText('Stopping')
        self.pco_start_button.setEnabled(True)
        self.pco_stop_button.setEnabled(False)
        try:
            CamP.disconnect()
        except Exception:
            pass

    def activate_flir(self):
        if CamF.get_cameras_number() > 0:
            self.flir_status.setText('Initializing')
            try:
                CamF.init_camera()
                self.flir_status.setText('Initialized')
                self.flir_start_button.setEnabled(False)
                self.flir_acquire_button.setEnabled(True)
                self.flir_stop_button.setEnabled(True)
                self.flir_live_view_button.setEnabled(True)
            except Exception as e:
                QMessageBox.warning(self, 'FLIR Error', f'Cannot activate FLIR camera:\n{e}')
                self.flir_status.setText(f'Error: {e}')
        else:
            QMessageBox.information(self, 'Error', 'No FLIR camera connected!')

    def start_flir_acquisition(self):
        try:
            CamF.prepare_external_trigger()
            CamF.Start_acquisition_thread()
            self.flir_status.setText('Ready and waiting for trigger')
            self.flir_start_button.setEnabled(False)
            self.flir_live_view_button.setEnabled(False)
        except Exception as e:
            QMessageBox.warning(self, 'FLIR Error', f'Cannot start acquisition:\n{e}')
            self.flir_status.setText(f'Error: {e}')

    def stop_flir(self):
        CamF.Stop_acquisition()
        self.flir_status.setText('Stopping')
        self.flir_start_button.setEnabled(True)
        self.flir_stop_button.setEnabled(False)

    def update_andor_exposure(self, value):
        S.ExposureA = value

    def update_pco_exposure(self, value):
        S.ExposureP = value / 1e6

    def update_flir_exposure(self, value):
        S.ExposureF = value

    def update_andor_gain(self, value):
        S.GainA = value

    def show_andor_live_view(self):
        self._show_live_view(CamA, "Andor")

    def show_pco_live_view(self):
        self._show_live_view(CamP, "PCO")

    def show_flir_live_view(self):
        self._show_live_view(CamF, "FLIR")

    def _show_live_view(self, camera_module, camera_name):
        try:
            # Check if camera is initialized
            if not hasattr(camera_module, 'cam') or camera_module.cam is None:
                QMessageBox.warning(self, 'Camera Not Initialized', f'Please activate the {camera_name} camera first.')
                return
            
            # Take a snapshot using the camera's take_single_image function
            image = camera_module.take_single_image()
            
            if image is None:
                QMessageBox.warning(self, 'Live View Error', f'Failed to capture image from {camera_name}.')
                return
            
            # Convert numpy array to QImage
            if image.dtype != np.uint8:
                # Normalize to 0-255
                image_min = image.min()
                image_max = image.max()
                if image_max > image_min:
                    image = ((image - image_min) / (image_max - image_min) * 255).astype(np.uint8)
                else:
                    image = np.zeros_like(image, dtype=np.uint8)
            
            height, width = image.shape
            bytes_per_line = width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale pixmap to fit in a reasonable window
            max_size = 800
            if pixmap.width() > max_size or pixmap.height() > max_size:
                pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Create dialog to show image
            dialog = QDialog(self)
            dialog.setWindowTitle(f'Live View - {camera_name} Camera')
            dialog.setModal(False)
            
            layout = QVBoxLayout()
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            layout.addWidget(image_label)
            
            close_button = QPushButton('Close')
            close_button.clicked.connect(dialog.close)
            layout.addWidget(close_button, alignment=Qt.AlignCenter)
            
            dialog.setLayout(layout)
            dialog.show()
            
        except Exception as e:
            QMessageBox.warning(self, 'Live View Error', f'Failed to capture image from {camera_name}:\n{str(e)}')

    def update_andor_exposure(self, value):
        S.ExposureA = value

    def update_pco_exposure(self, value):
        S.ExposureP = value / 1e6

    def update_flir_exposure(self, value):
        S.ExposureF = value

    def update_andor_gain(self, value):
        S.GainA = value

    def update_flir_gain(self, value):
        S.GainF = value

    def update_andor_temp_fan(self):
        if self.andor_stop_button.isEnabled():  # Camera is active
            try:
                temp, cooler, fan_mode = CamA.get_Temp()
                self.andor_temp_label.setText(f'Temperature: {temp}°C')
                fan_status = 'On' if fan_mode == 0 else 'Off'
                self.andor_fan_label.setText(f'Fan: {fan_status}')
            except Exception:
                self.andor_temp_label.setText('Temperature: --°C')
                self.andor_fan_label.setText('Fan: --')
        else:
            self.andor_temp_label.setText('Temperature: --°C')
            self.andor_fan_label.setText('Fan: --')

    def edit_pco_exposure(self):
        value, ok = QInputDialog.getInt(self, 'Exposure', 'Enter value (µs):', int(float(self.pco_exposure.text())))
        if ok:
            self.pco_exposure.setText(str(value))
            S.ExposureP = value / 1e6

    def edit_flir_exposure(self):
        value, ok = QInputDialog.getInt(self, 'Exposure', 'Enter value (µs):', int(float(self.flir_exposure.text())))
        if ok:
            self.flir_exposure.setText(str(value))
            S.ExposureF = value

    def closeEvent(self, event):
        self.camera_poll_timer.stop()
        self.temp_update_timer.stop()
        self.save_settings()
        CamA.Stop_acquisition()
        CamP.Stop_acquisition()
        CamF.Stop_acquisition()
        try:
            CamA.disconnect()
        except Exception:
            pass
        try:
            CamP.disconnect()
        except Exception:
            pass
        try:
            CamF.disconnect()
        except Exception:
            pass
        event.accept()
