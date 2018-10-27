from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class ToolButtonDelegate(QItemDelegate):

    clicked = pyqtSignal(QModelIndex)

    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)
        self.__icon = QIcon()

    def setDefaultIcon(self, icon):
        self.__icon = icon

    def createEditor(self, parent, option, index):
        but = QPushButton(str(index.data()), parent)
        return but

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        # editor.setCurrentIndex(int(index.model().data(index)))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())

    def currentIndexChanged(self):
        self.commitData.emit(self.sender())

    def paint(self, painter, option, index):

        if index.data() is None or not index.data():
            QItemDelegate.paint(self, painter, option, index)
            return

        style = QStyleOptionButton()
        style.arrowType = Qt.NoArrow
        style.rect = option.rect
        style.palette = option.palette
        icon = index.data(Qt.DecorationRole)
        if icon is not None:
            style.icon = icon.value()
        else:
            style.icon = self.__icon
        style.iconSize = QSize(16,16)
        if index.flags() & Qt.ItemIsEnabled:
            style.state = QStyle.State_Enabled | QStyle.State_Raised
        else:
            style.state = QStyle.State_Raised
        QApplication.style().drawControl(QStyle.CE_PushButton, style, painter)

    def editorEvent(self, event, model, option, index):
        if (index.flags() & Qt.ItemIsEnabled) == 0:
            return False
        type = event.type()
        if type == QEvent.MouseButtonRelease:
            model.setData(index, True)
            self.clicked.emit(index)
            event.accept()
            return True
        return False


class ComboBoxDelegate(QStyledItemDelegate):
    """
        A delegate that places a fully functioning QComboBox in every
        cell of the column to which it's applied
    """
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        if index.data() is None or index.data(Qt.EditRole) is None:
            return None
        return QComboBox(parent)

    def setEditorData(self, editor, index):
        if editor is None:
            return
        editor.clear()
        editor.addItems(index.data(Qt.EditRole))
        editor.setCurrentText(index.data(Qt.DisplayRole))
        editor.showPopup()

    def setModelData(self, editor, model, index):
        if editor is None:
            return
        model.setData(index, editor.currentText(), Qt.EditRole)