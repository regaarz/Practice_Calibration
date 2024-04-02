import os
import cv2 as cv
import numpy as np
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QTransform
from PyQt6.QtWidgets import QWidget, QApplication, QFileDialog, QSlider
from .ui_calib import Ui_Form
from src.plugin_interface import PluginInterface


class MainWindow(QWidget):
    def __init__(self, model):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.model = model
        self.set_stylesheet()

        self.ui.calibration.clicked.connect(self.calibrate_camera)
        self.ui.camera.clicked.connect(self.detect_checker_board)
        self.ui.capture.clicked.connect(self.capture_camera)

        self.ui.spinBox_X.valueChanged.connect(self.update_dimensi_papan_catur)
        self.ui.spinBox_Y.valueChanged.connect(self.update_dimensi_papan_catur)
        self.criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.image_dir_path = "images"
        if not os.path.isdir(self.image_dir_path):
            os.makedirs(self.image_dir_path)
            print(f'"{self.image_dir_path}" Directory is created')
        else:
            print(f'"{self.image_dir_path}" Directory already Exists.')

        # Image counter
        self.image_counter = 0
        self.cap = None
        self.camera_started = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def set_stylesheet(self):
        self.ui.label.setStyleSheet("font-size:64px;")
        self.ui.label.setStyleSheet(self.model.style_label())

    def update_dimensi_papan_catur(self):
        # Ambil nilai dari spinbox x dan y
        x_value = self.ui.spinBox_X.value()
        y_value = self.ui.spinBox_Y.value()

        # Perbarui CHESS_BOARD_DIM sesuai dengan nilai spinbox
        self.CHESS_BOARD_DIM = (x_value, y_value)
    def load_calibration_data(self):
        # Prepare object points
        SQUARE_SIZE = 14  # millimeters
        obj_3D = np.zeros((self.CHESS_BOARD_DIM[0] * self.CHESS_BOARD_DIM[1], 3), np.float32)
        obj_3D[:, :2] = np.mgrid[0:self.CHESS_BOARD_DIM[0], 0:self.CHESS_BOARD_DIM[1]].T.reshape(-1, 2)
        obj_3D *= SQUARE_SIZE

        # Arrays to store object points and image points
        obj_points_3D = []
        img_points_2D = []

        files = os.listdir(self.image_dir_path)
        for file in files:
            imagePath = os.path.join(self.image_dir_path, file)
            image = cv.imread(imagePath)
            grayScale = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
            ret, corners = cv.findChessboardCorners(image, self.CHESS_BOARD_DIM, None)
            if ret:
                obj_points_3D.append(obj_3D)
                corners2 = cv.cornerSubPix(grayScale, corners, (11, 11), (-1, -1),
                                           self.criteria)  # Menyesuaikan ukuran jendela
                img_points_2D.append(corners2)

        cv.destroyAllWindows()

        # Check if images found for calibration
        if not obj_points_3D:
            return None, None, None, None

        # Perform camera calibration
        ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(
            obj_points_3D, img_points_2D, grayScale.shape[::-1], None, None
        )

        # Save calibration data
        calib_data_path = "../calib_data"
        if not os.path.isdir(calib_data_path):
            os.makedirs(calib_data_path)
        np.savez(
            f"{calib_data_path}/MultiMatrix",
            camMatrix=mtx,
            distCoef=dist,
            rVector=rvecs,
            tVector=tvecs,
        )

        return mtx, dist, rvecs, tvecs

    def calibrate_camera(self):
        # Load calibration data
        camMatrix, distCof, rVector, tVector = self.load_calibration_data()

        # Check if no images found for calibration

        # Update UI labels
        self.ui.label_camMatrix.setText(str(camMatrix))
        self.ui.label_distCof.setText(str(distCof))
        self.ui.label_rVector.setText(str(rVector))
        self.ui.label_tVector.setText(str(tVector))


    def detect_checker_board(self):
        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Failed to open camera.")
            return
        else:
            print("Camera opened successfully")

        # Start timer to update frame
        self.timer.start(10)
        self.camera_started = True  # Set camera status to started

    def update_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)  # Konversi ke skala abu-abu
                ret, corners = cv.findChessboardCorners(gray, self.CHESS_BOARD_DIM)
                if ret:
                    corners = cv.cornerSubPix(gray, corners, (3, 3), (-1, -1),
                                              self.criteria)  # Menyesuaikan ukuran jendela
                    frame = cv.drawChessboardCorners(frame, self.CHESS_BOARD_DIM, corners, ret)

                # Resize frame to fit label_cam
                frame_resized = cv.resize(frame, (self.ui.cam.width(), self.ui.cam.height()))

                # Convert frame to QImage
                h, w, ch = frame_resized.shape
                bytes_per_line = ch * w
                q_img = QImage(frame_resized.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)

                # Convert QImage to QPixmap
                pixmap = QPixmap.fromImage(q_img)

                # Display frame on label_cam
                self.ui.cam.setPixmap(pixmap)
                self.ui.cam.setScaledContents(True)

    def capture_camera(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Check if checkerboard is detected
                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                ret, _ = cv.findChessboardCorners(gray, self.CHESS_BOARD_DIM)
                if ret:
                    # Increment image counter and create a filename
                    self.image_counter += 1
                    filename = f"{self.image_dir_path}/image_{self.image_counter}.jpg"

                    # Save the frame as an image
                    cv.imwrite(filename, frame)
                    print(f"Image saved: {filename}")
                    self.ui.status.setText("Image saved: " + filename)  # assuming ui.status is your status label
                    self.ui.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    print("Checkerboard not detected.")
                    self.ui.status.setText("Checkerboard not detected")
                    self.ui.status.setAlignment(Qt.AlignmentFlag.AlignCenter)



    def __del__(self):
        self.close_camera()

    def closeEvent(self, event):
        self.close_camera()
        event.accept()

class WebCalib(PluginInterface):
    def __init__(self):
        super().__init__()
        self.widget = None
        self.description = "This is a plugins application"

    def set_plugin_widget(self, model):
        self.widget = MainWindow(model)
        return self.widget

    def set_icon_apps(self):
        return "web.png"

    def change_stylesheet(self):
        self.widget.set_stylesheet()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    interface = WebCalib()
    interface.show()
    sys.exit(app.exec())
