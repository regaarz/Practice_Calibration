import os
import cv2
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QTransform
from PyQt6.QtWidgets import QWidget, QApplication, QFileDialog, QSlider
from .ui_main import Ui_Form
from src.plugin_interface import PluginInterface
from src.models.take_photo import detect_checker_board

class Controller(QWidget):
    def __init__(self, model):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.model = model
        self.set_stylesheet()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.image_paths_1 = []
        self.image_paths_2 = []
        self.current_image_index_1 = 0
        self.current_image_index_2 = 0
        self.mirror_enabled_1 = False
        self.mirror_enabled_2 = False

        self.ui.zoom_slider.setRange(25, 500)
        self.ui.zoom_slider.setSliderPosition(100)
        self.ui.zoom_slider.valueChanged.connect(self.set_zoom)

        self.ui.zoom_slider_2.setRange(25, 500)
        self.ui.zoom_slider_2.setSliderPosition(100)
        self.ui.zoom_slider_2.valueChanged.connect(self.set_zoom_2)

        #mengatur kamera
        self.ui.open_cam.clicked.connect(self.start_camera)
        self.ui.close.clicked.connect(self.close_camera)
        self.ui.capture.clicked.connect(self.capture_image)

        #gambar
        self.ui.pushButton.clicked.connect(self.load_image_1)
        self.ui.open.clicked.connect(self.load_image_1)
        self.ui.next.clicked.connect(self.next_image_1)
        self.ui.previous.clicked.connect(self.previous_image_1)

        self.ui.open_2.clicked.connect(self.load_image_2)
        self.ui.next_2.clicked.connect(self.next_image_2)
        self.ui.previous_2.clicked.connect(self.previous_image_2)

        self.ui.mirror.clicked.connect(self.toggle_mirror_1)
        self.ui.mirror_2.clicked.connect(self.toggle_mirror_2)
        self.ui.reset_mirror_1.clicked.connect(self.reset_mirror_1)
        self.ui.reset_mirror_2.clicked.connect(self.reset_mirror_2)

        self.ui.pushButton_5.clicked.connect(self.load_image_1)

        self.cap = None
        self.camera_started = False

    def set_stylesheet(self):
        self.ui.label.setStyleSheet("font-size:64px;")
        self.ui.label.setStyleSheet(self.model.style_label())

    def load_image_1(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory Containing Images")
        if directory:
            image_files = [os.path.join(directory, file) for file in os.listdir(directory) if
                           file.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            if image_files:
                self.image_paths_1.extend(image_files)
                self.show_image_1(image_files[self.current_image_index_1])

    def load_image_2(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory Containing Images")
        if directory:
            image_files = [os.path.join(directory, file) for file in os.listdir(directory) if
                           file.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            if image_files:
                if self.current_image_index_1 >= len(image_files):
                    self.current_image_index_1 = 0  #
                self.image_paths_2.extend(image_files)
                self.show_image_2(image_files[self.current_image_index_2])

    def next_image_1(self):
        if self.image_paths_1:
            self.current_image_index_1 = (self.current_image_index_1 + 1) % len(self.image_paths_1)
            self.show_image_1(self.image_paths_1[self.current_image_index_1])

    def next_image_2(self):
        if self.image_paths_2:
            self.current_image_index_2 = (self.current_image_index_2 + 1) % len(self.image_paths_2)
            self.show_image_2(self.image_paths_2[self.current_image_index_2])

    def previous_image_1(self):
        if self.image_paths_1:
            self.current_image_index_1 = (self.current_image_index_1 - 1) % len(self.image_paths_1)
            self.show_image_1(self.image_paths_1[self.current_image_index_1])

    def previous_image_2(self):
        if self.image_paths_2:
            self.current_image_index_2 = (self.current_image_index_2 - 1) % len(self.image_paths_2)
            self.show_image_2(self.image_paths_2[self.current_image_index_2])

    def show_image_1(self, file, zoom_factor=1):
        pixmap = QtGui.QPixmap(file)
        if self.mirror_enabled_1:
            # Jika mirror diaktifkan, terapkan transformasi gambar secara horizontal
            pixmap = pixmap.transformed(QtGui.QTransform().scale(-1, 1))
        # Hitung ukuran pixmap yang telah diperbesar sesuai dengan faktor zoom
        scaled_pixmap = pixmap.scaled(pixmap.size() * zoom_factor, Qt.AspectRatioMode.KeepAspectRatio)
        # Atur pixmap yang diperbesar ke label tempat gambar ditampilkan
        self.ui.label_3.setPixmap(scaled_pixmap)
        self.ui.mirror.setChecked(self.mirror_enabled_1)

    def show_image_2(self, file, zoom_factor=1):
        pixmap = QPixmap(file)
        if self.mirror_enabled_2:
            # Jika mirror diaktifkan, terapkan transformasi gambar secara horizontal
            pixmap = pixmap.transformed(QtGui.QTransform().scale(-1, 1))
        scaled_pixmap = pixmap.scaled(pixmap.size() * zoom_factor, Qt.AspectRatioMode.KeepAspectRatio)
        self.ui.label_26.setPixmap(scaled_pixmap)
        self.ui.mirror_2.setChecked(self.mirror_enabled_2)

    def set_zoom(self, value):
        if self.image_paths_1:
            # Ubah ukuran gambar sesuai dengan faktor zoom yang diberikan
            zoom_factor = value / 100
            pixmap = QtGui.QPixmap(self.image_paths_1[self.current_image_index_1])
            new_width = int(pixmap.width() * zoom_factor)
            new_height = int(pixmap.height() * zoom_factor)
            new_size = QtCore.QSize(new_width, new_height)
            scaled_pixmap = pixmap.scaled(new_size, Qt.AspectRatioMode.KeepAspectRatio)
            # Atur pixmap yang diperbesar ke label tempat gambar ditampilkan
            self.ui.label_3.setPixmap(scaled_pixmap)  # Perbaikan di sini

    def set_zoom_2(self, value):
        if self.image_paths_2:
            # Ubah ukuran gambar sesuai dengan faktor zoom yang diberikan
            zoom_factor = value / 100
            pixmap = QtGui.QPixmap(self.image_paths_2[self.current_image_index_2])  # Menggunakan image_paths_2 dan current_image_index_2
            new_width = int(pixmap.width() * zoom_factor)
            new_height = int(pixmap.height() * zoom_factor)
            new_size = QtCore.QSize(new_width, new_height)
            scaled_pixmap = pixmap.scaled(new_size, Qt.AspectRatioMode.KeepAspectRatio)
            # Atur pixmap yang diperbesar ke label tempat gambar ditampilkan
            self.ui.label_26.setPixmap(scaled_pixmap)  # Mengatur label_26

    def toggle_mirror_1(self): #fungsi mirror gambar 1
        self.mirror_enabled_1 = self.ui.mirror.isChecked()
        self.show_image_1(self.image_paths_1[self.current_image_index_1])

    def toggle_mirror_2(self): #fungsi mirror gambar 2
        self.mirror_enabled_2 = self.ui.mirror_2.isChecked()
        self.show_image_2(self.image_paths_2[self.current_image_index_2])

    def reset_mirror_1(self): #fungsi reset gambar 1
        self.mirror_enabled_1 = False
        self.ui.mirror.setChecked(False)
        self.show_image_1(self.image_paths_1[self.current_image_index_1])

    def reset_mirror_2(self): #fungsi reset gambar 2
        self.mirror_enabled_2 = False
        self.ui.mirror_2.setChecked(False)
        self.show_image_2(self.image_paths_2[self.current_image_index_2])

    def start_camera(self): #memulai kamera
        if not self.camera_started:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Failed to open camera.")
                return
            else:
                print("Camera opened successfully")
            self.timer.start(10)
            self.camera_started = True

    def capture_image(self):
        if self.camera_started and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                save_dir = f"/home/regaarz/FTDC/moilapp/src/plugins/moilapp-plugin-hello-world/captured_images"
                os.makedirs(save_dir, exist_ok=True)  # Ensure directory exists
                num_existing_images = len([name for name in os.listdir(save_dir) if name.startswith("captured_image")])
                file_name = f"captured_image_{num_existing_images + 1}.jpg"
                save_path = os.path.join(save_dir, file_name)
                print("Saving captured image to:", save_path)
                cv2.imwrite(save_path, frame)

    def update_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame_resized = cv2.resize(frame, (561, 440))
                image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                h, w, ch = image.shape
                bytes_per_line = ch * w
                convert_to_qt_format = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                p = QPixmap.fromImage(convert_to_qt_format).scaled(561, 440, Qt.AspectRatioMode.KeepAspectRatio)
                self.ui.label_25.setPixmap(p)

    def close_camera(self):
        if self.camera_started:
            print("camera stopped")
            self.timer.stop()
            self.cap.release()
            self.camera_started = False


    def __del__(self):
        self.close_camera()

    def closeEvent(self, event):
        self.close_camera()
        event.accept()

class WebInterface(PluginInterface):
    def __init__(self):
        super().__init__()
        self.widget = None
        self.description = "This is a plugins application"

    def set_plugin_widget(self, model):
        self.widget = Controller(model)
        return self.widget

    def set_icon_apps(self):
        return "web.png"

    def change_stylesheet(self):
        self.widget.set_stylesheet()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    interface = WebInterface()
    interface.show()
    sys.exit(app.exec())