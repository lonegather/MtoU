import os
from Qt.QtWidgets import QMainWindow, QSizePolicy
from Qt.QtCore import Qt, QAbstractListModel, QModelIndex, QSize
import samkit
from . import Docker, setup_ui


class FileListModel(QAbstractListModel):

    def __init__(self):
        super(FileListModel, self).__init__()
        self._files = []

    def rowCount(self, parent):
        return len(self._files)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return self._files[index.row()]['name']
            elif role == Qt.SizeHintRole:
                return QSize(0, 30)

    def supportedDropActions(self):
        return Qt.CopyAction

    def flags(self, index):
        default_flags = super(FileListModel, self).flags(index)
        return Qt.ItemIsDropEnabled | default_flags

    def mimeTypes(self):
        return ['text/uri-list']

    def dropMimeData(self, data, action, row, column, parent):
        for url in data.urls() or list():
            file_path = url.toLocalFile()
            file_name = os.path.split(file_path)[1]
            if file_name.split('.')[-1].lower() not in ["ma", "mb"]:
                continue
            for f in self._files:
                if f['source'] == file_path:
                    break
            else:
                self._files.append({"name": file_name, "source": file_path})

        self.dataChanged.emit(QModelIndex(), QModelIndex())
        return True


class BatchIntegrationUI(Docker):

    CONTROL_NAME = 'mtou_batch_control'
    DOCK_LABEL_NAME = 'MtoU Batch Integration'
    UI_PATH = '%s/ui/batch.ui' % samkit.MODULE_PATH

    def __init__(self, parent=None):
        super(BatchIntegrationUI, self).__init__(parent=parent)
        setup_ui(self, self.UI_PATH)

        self.ui.lv_file.setModel(FileListModel())
        self.ui.lv_file.setAcceptDrops(True)
        self.ui.lv_file.setDropIndicatorShown(True)
