from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from pynput import mouse, keyboard
from threading import Thread
import time

from MouseEventsHandler import MouseEventsHandler
from Delegates import ToolButtonDelegate, ComboBoxDelegate


class CaptureMouseWidget(QDialog):

    mouseClicked = pyqtSignal(QPoint)
    aboutToClose = pyqtSignal()

    def __init__(self, parent=None):
        super(CaptureMouseWidget, self).__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.infoLabel = QLabel("Click to save the coordinates")
        self.coordinatesLabel = QLabel("(0,0)")
        self.layout = QVBoxLayout()
        self.point = QPoint(0,0)
        self.layout.addWidget(self.infoLabel)
        self.layout.addWidget(self.coordinatesLabel)

        self.setLayout(self.layout)

    def startCaptureMouse(self):
        # Collect events until released
        listener = mouse.Listener(
                on_move=self.on_move,
                on_click=self.on_click,
                on_scroll=self.on_scroll)
        listener.start()

    def on_move(self, x, y):
        self.coordinatesLabel.setText("("+str(x)+", "+str(y)+")")
        self.point.setX(x)
        self.point.setY(y)

    def on_click(self, x, y, button, pressed):
        self.point.setX(x)
        self.point.setY(y)
        if not pressed:
            self.mouseClicked.emit(self.point)
            self.aboutToClose.emit()
            self.close()
            # Stop listener
            return False

    def on_scroll(self, x, y, dx, dy):
        pass


class EventsTableModel(QAbstractTableModel):
    def __init__(self):
        super(EventsTableModel, self).__init__()
        self.__eventsHandler = None
        self.eventTypes = ["Click", "Move", "Drag"]
        self.buttons = ["Left", "Right"]

    def setEventsHandler(self, eventsHandler):
        self.beginResetModel()
        self.__eventsHandler = eventsHandler
        self.endResetModel()

    def rowCount(self, parent=None, *args, **kwargs):
        if self.__eventsHandler is not None:
            return len(self.__eventsHandler.eventsList)
        return 0

    def columnCount(self, parent=None, *args, **kwargs):
        return 6

    def headerData(self, section, orientation, role=None):
        headerLabels = ["", "X", "Y", "Event type", "Button", "Note"]
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return headerLabels[section]
        return QVariant()

    def data(self, index, role=None):
        row = index.row()
        column = index.column()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if column is 1:
                return self.__eventsHandler.eventsList[row].xPos
            elif column is 2:
                return self.__eventsHandler.eventsList[row].yPos
            elif column is 3:
                if role == Qt.DisplayRole:
                    return self.eventTypes[int(self.__eventsHandler.eventsList[row].eventType)]
                else:
                    return self.eventTypes
            elif column is 4:
                if role == Qt.DisplayRole:
                    return self.buttons[int(self.__eventsHandler.eventsList[row].button)]
                else:
                    return self.buttons
            elif column is 5:
                return self.__eventsHandler.eventsList[row].label
            else:
                return True
        elif role is Qt.ToolTipRole:
            if column is 0:
                return "Selecione o local na tela"
        return QVariant()

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled

    def setData(self, index, value, role=None):
        if role != Qt.EditRole:
            return False
        row = index.row()
        col = index.column()
        event = self.__eventsHandler.eventsList[row]
        if col is 1:
            event.xPos = value
        elif col is 2:
            event.yPos = value
        elif col is 3:
            if value in self.eventTypes:
                event.eventType = self.eventTypes.index(value)
        elif col is 4:
            if value in self.buttons:
                event.button = self.buttons.index(value)
        elif col is 5:
            event.label = value
        self.dataChanged.emit(index, index)
        self.layoutChanged.emit()
        return True


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Autoclicker")
        #self.setMinimumWidth(600)
        settings = QSettings()

        delay = settings.value("delay", 2000, type=int)
        interval = settings.value("interval", 1000, type=int)
        loops = settings.value("loops", 100, type=int)

        self.__mouseEventsHandler = MouseEventsHandler(delay, interval, loops)
        self.__tableModel = EventsTableModel()

        self.mainLayout = QVBoxLayout()

        self.delayLayout = QHBoxLayout()
        self.delayLabel = QLabel("Pre-delay(ms)")
        self.delaySpinBox = QSpinBox()
        self.delaySpinBox.setRange(0, 1e+9)
        self.delaySpinBox.setValue(delay)
        self.delayLayout.addWidget(self.delayLabel)
        self.delayLayout.addWidget(self.delaySpinBox)
        self.mainLayout.addLayout(self.delayLayout)

        self.intervalLayout = QHBoxLayout()
        self.intervalLabel = QLabel("Interval(ms)")
        self.intervalSpinBox = QSpinBox()
        self.intervalSpinBox.setRange(0, 1e+9)
        self.intervalSpinBox.setValue(interval)
        self.intervalLayout.addWidget(self.intervalLabel)
        self.intervalLayout.addWidget(self.intervalSpinBox)
        self.mainLayout.addLayout(self.intervalLayout)

        self.numberLoopsLayout = QHBoxLayout()
        self.numberLoopsLabel = QLabel("# of loops")
        self.numberLoopsSpinBox = QSpinBox()
        self.numberLoopsSpinBox.setRange(0, 1e+9)
        self.numberLoopsSpinBox.setValue(loops)
        self.numberLoopsLayout.addWidget(self.numberLoopsLabel)
        self.numberLoopsLayout.addWidget(self.numberLoopsSpinBox)
        self.mainLayout.addLayout(self.numberLoopsLayout)

        self.eventsGroupBox = QGroupBox("Click Events")
        self.eventsGroupBoxLayout = QVBoxLayout()
        self.clickEventsTable = QTableView()
        self.clickEventsTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.clickEventsTable.setSelectionMode(QAbstractItemView.SingleSelection)
        buttonDelegate = ToolButtonDelegate(self.clickEventsTable)
        buttonDelegate.setDefaultIcon(QIcon("./icons/target.png"))
        buttonDelegate.clicked.connect(self.setMouseLocation)
        self.clickEventsTable.setItemDelegateForColumn(0, buttonDelegate)
        comboBoxDelegate = ComboBoxDelegate(self.clickEventsTable)
        self.clickEventsTable.setItemDelegateForColumn(3, comboBoxDelegate)
        self.clickEventsTable.setItemDelegateForColumn(4, comboBoxDelegate)
        self.clickEventsTable.setColumnWidth(0, 30)
        self.clickEventsTable.setModel(self.__tableModel)
        self.eventsButtonsLayout = QHBoxLayout()
        self.clearButton = QPushButton("Clear events table")
        self.removeButton = QPushButton("Remove selected event")
        self.addEventButton = QPushButton("Add event")
        self.eventsButtonsLayout.addWidget(self.clearButton)
        self.eventsButtonsLayout.addWidget(self.removeButton)
        self.eventsButtonsLayout.addWidget(self.addEventButton)
        self.eventsGroupBoxLayout.addWidget(self.clickEventsTable)
        self.eventsGroupBoxLayout.addLayout(self.eventsButtonsLayout)
        self.eventsGroupBox.setLayout(self.eventsGroupBoxLayout)
        self.mainLayout.addWidget(self.eventsGroupBox)

        self.buttonsLayout = QHBoxLayout()
        self.stopButton = QPushButton("Stop (F10)")
        self.stopButton.setEnabled(False)
        self.startButton = QPushButton("Start (F11)")
        self.buttonsLayout.addWidget(self.stopButton)
        self.buttonsLayout.addWidget(self.startButton)
        self.mainLayout.addLayout(self.buttonsLayout)

        self.widget = QWidget()
        self.widget.setLayout(self.mainLayout)

        self.setCentralWidget(self.widget)

        self.createActions()
        self.createMenu()

        self.captureDialog = CaptureMouseWidget(self)
        self.currentPoint = QPoint(0,0)
        self.currentIndex = QModelIndex()

        self.keyboardListener = keyboard.Listener(on_press=self.on_press)
        self.keyboardListener.start()

        self.delaySpinBox.valueChanged.connect(self.spinValueChange)
        self.intervalSpinBox.valueChanged.connect(self.spinValueChange)
        self.numberLoopsSpinBox.valueChanged.connect(self.spinValueChange)
        self.addEventButton.clicked.connect(self.addNewEvent)
        self.removeButton.clicked.connect(self.removeSelectedEvent)
        self.captureDialog.mouseClicked.connect(self.getClickedPoint)
        self.captureDialog.aboutToClose.connect(self.treatClosingDialog)
        self.__tableModel.layoutChanged.connect(self.onDataChanged)
        self.startButton.clicked.connect(self.startAutoClicker)
        self.stopButton.clicked.connect(self.stopAutoClicker)
        self.clearButton.clicked.connect(self.clearEventTable)

    def spinValueChange(self, value):
        sender = self.sender()
        settings = QSettings()
        if sender == self.delaySpinBox:
            self.__mouseEventsHandler.setPreDelay(value)
            settings.setValue("delay", value)
        if sender == self.intervalSpinBox:
            self.__mouseEventsHandler.setInterval(value)
            settings.setValue("interval", value)
        if sender == self.numberLoopsSpinBox:
            self.__mouseEventsHandler.setLoops(value)
            settings.setValue("loops", value)

    def addNewEvent(self):
        self.__mouseEventsHandler.addEvent()
        self.__tableModel.setEventsHandler(self.__mouseEventsHandler)
        self.clickEventsTable.resizeColumnsToContents()

    def removeSelectedEvent(self):
        selectedRows = self.clickEventsTable.selectionModel().selectedIndexes()
        if len(selectedRows) > 0:
            event = self.__mouseEventsHandler.eventsList[selectedRows[0].row()]
            self.__mouseEventsHandler.removeEvent(event)
            self.__tableModel.setEventsHandler(self.__mouseEventsHandler)

    def clearEventTable(self):
        self.__mouseEventsHandler.clearEvents()
        self.__tableModel.setEventsHandler(self.__mouseEventsHandler)

    def setMouseLocation(self, index):
        self.currentIndex = index
        self.captureDialog.startCaptureMouse()
        self.captureDialog.setModal(True)
        self.captureDialog.show()

    def getClickedPoint(self, point):
        self.currentPoint = point

    def treatClosingDialog(self):
        row = self.currentIndex.row()
        event = self.__mouseEventsHandler.eventsList[row]
        event.xPos = self.currentPoint.x()
        event.yPos = self.currentPoint.y()
        self.__tableModel.setEventsHandler(self.__mouseEventsHandler)

    def onDataChanged(self):
        self.clickEventsTable.resizeColumnsToContents()

    def startAutoClicker(self):
        self.__mouseEventsHandler.generalInfo()
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        clickerThread = Thread(target=self.__mouseEventsHandler.runAutoClicker)
        clickerThread.start()
        threadChecker = Thread(target=self.checkThreadIsAlive,kwargs=dict(thread=clickerThread))
        threadChecker.start()

    def stopAutoClicker(self):
        self.__mouseEventsHandler.stop(True)

    def checkThreadIsAlive(self, thread):
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        while thread.isAlive():
            time.sleep(2)
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)

    def on_press(self, key):
        if key == keyboard.Key.f10:
            self.stopButton.click()
        elif key == keyboard.Key.f11:
            self.startButton.click()

    def createActions(self):
        self.openFileAction = QAction("Open mouse events", self)
        self.openFileAction.setShortcuts(QKeySequence.Open)
        self.openFileAction.setStatusTip("Open an existing file with events")
        self.openFileAction.triggered.connect(self.openFileMenuAction)
        self.saveFileAction = QAction("Save mouse events", self)
        self.saveFileAction.setShortcuts(QKeySequence.Save)
        self.saveFileAction.setStatusTip("Save a file with current events")
        self.saveFileAction.triggered.connect(self.saveFileMenuAction)

    def createMenu(self):
        self.fileMenu = self.menuBar().addMenu("File")
        self.fileMenu.addAction(self.openFileAction)
        self.fileMenu.addAction(self.saveFileAction)

    def openFileMenuAction(self):
        name, _ = QFileDialog.getOpenFileName(self, "Open File","","Mouse events file (*.mef)")
        self.__mouseEventsHandler.openEvents(name)
        self.__tableModel.setEventsHandler(self.__mouseEventsHandler)


    def saveFileMenuAction(self):
        saveFileDialog = QFileDialog(self, "Save File", QDir.homePath(),"Mouse events file (*.mef)")
        saveFileDialog.setAcceptMode(QFileDialog.AcceptSave)
        saveFileDialog.setDefaultSuffix("mef")
        if saveFileDialog.exec_():
            name = saveFileDialog.selectedFiles()[0]
            self.__mouseEventsHandler.saveEvents(name)


