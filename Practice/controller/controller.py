import os
import cv2 as cv
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer
from view.ui_main import Ui_Form


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.callibration.clicked.connect(self.calibrate_camera)
        self.ui.camera.clicked.connect(self.detect_checker_board)
        self.ui.capture.clicked.connect(self.capture_camera)

        # Checkerboard properties
        self.CHESS_BOARD_DIM = (9, 6)
        self.criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # Image directory path
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
                else:
                    print("Checkerboard not detected.")

    def __del__(self):
        if self.cap is not None:
            self.cap.release()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

