from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import sys

from MainWindow import MainWindow


app = QApplication(sys.argv)

QCoreApplication.setOrganizationName("Myself")
QCoreApplication.setApplicationName("Autoclicker")

window = MainWindow()
window.show()

app.exec_()