from models.plugins_model.auto_write_init import update_init_file_for_import
import sys

if not sys.platform.startswith('win'):
    try:
        update_init_file_for_import()
    except:
        print("has problems with auto_write_init plugin model")

from PyQt6 import QtCore, QtGui
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMainWindow, QGraphicsDropShadowEffect, QApplication
from views.ui_splash_screen import Ui_SplashScreen
from views.main_moilapp import Ui_MainWindow

from models.model_main import Model
from controllers.control_main import Controller

# os.environ["QT_FONT_DPI"] = "96"  # FIX Problem for High DPI and Scale above 100%
# Handle high resolution displays:
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)




class MainWindow:
    def __init__(self):
        model = Model()
        ui = Ui_MainWindow()
        self.win = Controller(ui, model)
        self.win.show()


class SplashScreen(QMainWindow):
    def __init__(self):

        QMainWindow.__init__(self)
        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)
        self.main = None

        q_rectangle = self.frameGeometry()
        center_position = self.screen().availableGeometry().center()
        q_rectangle.moveCenter(center_position)
        self.move(q_rectangle.topLeft())

        self.counter = 0

        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.ui.dropShadowFrame.setGraphicsEffect(self.shadow)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.open_main_window)

        self.timer.start(17)

        self.ui.label_description.setText("<strong>WELCOME !!!!!</strong>")
        QtCore.QTimer.singleShot(500,
                                 lambda: self.ui.label_description.setText("<strong>LOADING</strong> DATABASE"))
        QtCore.QTimer.singleShot(1000,
                                 lambda: self.ui.label_description.setText(
                                     "<strong>LOADING</strong> USER INTERFACE"))

        QtCore.QTimer.singleShot(1500,
                                 lambda: self.ui.label_description.setText(
                                     "<strong>LOADING</strong> Finish !!"))
        self.show()

    def open_main_window(self):
        """
        Updates the progress bar and opens the main window when the progress bar reaches 100.

        If the progress bar reaches 100, the timer is stopped and the main window is opened.

        """
        self.ui.progressBar.setValue(self.counter)

        if self.counter > 100:
            self.timer.stop()
            self.main = MainWindow()
            self.close()
        self.counter += 1


if __name__ == "__main__":
    app = QApplication([])
    window = SplashScreen()
    # window = MainWindow()
    app.exec()
