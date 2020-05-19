import os
import pyblish.api
import pyblish.util
from Qt.QtCore import Qt, QAbstractListModel, QModelIndex, QSize, QThread, Signal, QEvent
from Qt.QtGui import QColor
import samkit
from . import Docker, setup_ui


class FileListModel(QAbstractListModel):

    dropped = Signal()

    def __init__(self):
        super(FileListModel, self).__init__()
        self._files = []
        self._thread = None
        self.running = False

    def rowCount(self, parent):
        return len(self._files)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return self._files[index.row()]['display']
            elif role == Qt.TextColorRole:
                return self._files[index.row()]['color']
            elif role == Qt.SizeHintRole:
                return QSize(0, 20)

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
                file_name = os.path.splitext(file_name)[0]
                try:
                    project = samkit.get_data('project', id=samkit.getenv(samkit.OPT_PROJECT_ID))
                    project = project[0]['name']
                    if file_name.find(project) == 0:
                        episode, scene, suffix = file_name[(len(project)+1):].split('_', 2)
                        if suffix != 'anm':
                            raise IndexError
                        text_color = QColor(Qt.white)
                        skip = False
                        tags = samkit.get_data('tag', genus='shot', project_id=samkit.getenv(samkit.OPT_PROJECT_ID))
                        if episode not in [tag['name'] for tag in tags]:
                            raise IndexError
                        tag_id = [tag['id'] for tag in tags if tag['name'] == episode]
                    else:
                        raise IndexError
                except IndexError:
                    tag_id = ''
                    text_color = QColor(80, 80, 80)
                    skip = True
                except ValueError:
                    tag_id = ''
                    text_color = QColor(80, 80, 80)
                    skip = True

                self._files.append({
                    'source': file_path,
                    'name': file_name,
                    'tag_id': tag_id[0] if tag_id else '',
                    'display': file_name,
                    'color': text_color,
                    'skip': skip,
                })
                self.dropped.emit()

        self.dataChanged.emit(QModelIndex(), QModelIndex())
        return True

    def start(self, color=None, message='', current=0):
        if current > 0:
            prev = self._files[current-1]
            prev['color'] = color
            prev['display'] = prev['name'] + ' - ' + message
            self.running = False
        if current >= len(self._files):
            self.dropped.emit()
            self.dataChanged.emit(QModelIndex(), QModelIndex())
            return
        current_file = self._files[current]
        while current_file['skip']:
            current += 1
            if current >= len(self._files):
                self.dropped.emit()
                self.dataChanged.emit(QModelIndex(), QModelIndex())
                return
            current_file = self._files[current]
        print(current, current_file)
        current_file['color'] = QColor(Qt.yellow)
        current_file['display'] = current_file['name'] + ' - ' + 'processing...'
        self.running = True
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        self._thread = CommandThread(current_file, current+1)
        self._thread.completed.connect(self.start)
        self._thread.start()

    def clear(self):
        if not self.running:
            self._files = []
            self.dataChanged.emit(QModelIndex(), QModelIndex())


class BatchIntegrationUI(Docker):

    CONTROL_NAME = 'mtou_batch_control'
    DOCK_LABEL_NAME = 'MtoU Batch Integration'
    UI_PATH = '%s/ui/batch.ui' % samkit.MODULE_PATH

    def __init__(self, parent=None):
        super(BatchIntegrationUI, self).__init__(parent=parent)
        setup_ui(self, self.UI_PATH)

        model = FileListModel()
        self.ui.lv_file.setModel(model)
        self.ui.lv_file.setAcceptDrops(True)
        self.ui.lv_file.setDropIndicatorShown(True)
        self.ui.lv_file.installEventFilter(self)
        self.ui.lv_file.viewport().installEventFilter(self)
        self.ui.btn_start.setEnabled(False)
        self.ui.btn_start.clicked.connect(self.start)
        self.ui.btn_clear.clicked.connect(self.clear)
        model.dropped.connect(lambda: self.ui.btn_start.setEnabled(True))

    def eventFilter(self, source, event):
        if (
            source is self.ui.lv_file and
            event.type() == QEvent.KeyPress and
            event.modifiers() == Qt.NoModifier
        ) or (
            source is self.ui.lv_file.viewport() and
            event.type() == QEvent.MouseButtonPress and
            not self.ui.lv_file.indexAt(event.pos()).isValid()
        ):
            self.ui.lv_file.selectionModel().clear()
        return super(BatchIntegrationUI, self).eventFilter(source, event)

    def start(self):
        self.ui.btn_start.setEnabled(False)
        self.ui.lv_file.model().start()

    def clear(self):
        self.ui.btn_start.setEnabled(False)
        self.ui.lv_file.model().clear()


class CommandThread(QThread):

    completed = Signal(QColor, str, int)

    def __init__(self, current_file, next_index):
        super(CommandThread, self).__init__()
        self._file = current_file
        self._next = next_index
        self._plugins = []
        self._context = None

    def validate(self, task):
        print('Validating: %s - %s...' % (task['tag'], task['entity']))
        self._context = pyblish.util.validate(pyblish.util.collect(), self._plugins)
        for result in self._context.data['results']:
            if not result['success']:
                print(result)
                return QColor(Qt.red), 'Validation failed.', False
        return QColor(Qt.green), '', True

    def extract(self, task):
        print('Extracting: %s - %s...' % (task['tag'], task['entity']))
        self._context = pyblish.util.extract(self._context)
        return QColor(Qt.green), '', True

    def integrate(self, task):
        print('Integrating: %s - %s...' % (task['tag'], task['entity']))
        self._context.data['comment'] = 'Auto Message: Batch Integration'
        pyblish.util.integrate(self._context)
        return QColor(Qt.green), 'Done'

    def run(self):
        self.sleep(1)
        try:
            # Sync Database
            kwargs = {
                'name': self._file['name'].split('_')[-2],
                'tag_id': self._file['tag_id'],
            }
            shots = samkit.get_data('entity', **kwargs)
            if len(shots):
                kwargs['id'] = shots[0]['id']
                task = samkit.get_data(
                    'task',
                    stage='anm',
                    entity_id=kwargs['id'],
                )[0]
            else:
                name = self._file['name'].split('_')[-2]
                samkit.set_data('entity', name=name, info=name, tag_id=self._file['tag_id'])
                entity = samkit.get_data(
                    'entity',
                    project_id=samkit.executeInMainThreadWithResult(samkit.getenv, samkit.OPT_PROJECT_ID),
                    tag_id=self._file['tag_id'],
                    name=name,
                )[0]
                task = samkit.get_data(
                    'task',
                    stage='anm',
                    entity_id=entity['id'],
                )[0]

            if task['owner']:
                if task['owner'] != samkit.getenv(samkit.OPT_USERNAME):
                    self.completed.emit(
                        QColor(Qt.red),
                        '%s already checked out by %s.' % (task['entity'], task['owner']),
                        self._next,
                    )
                    return
            elif not samkit.executeInMainThreadWithResult(samkit.checkout, task, self._file['source']):
                self.completed.emit(
                    QColor(Qt.red),
                    'Source path unreachable.',
                    self._next,
                )
                return

            samkit.executeInMainThreadWithResult(samkit.open_file, task, True)
            samkit.executeInMainThreadWithResult(samkit.checkin, [task])
            pyblish.api.deregister_all_plugins()
            for plugin in pyblish.api.discover():
                if plugin.order < 0.5 or plugin.order >= 1.5:
                    pyblish.api.register_plugin(plugin)
                    continue
                family = task['stage'] if task['tag'] != 'SC' else 'ignore'
                if plugin.families == ['*'] or family in plugin.families:
                    self._plugins.append(plugin)

            color, message, success = samkit.executeInMainThreadWithResult(self.validate, task)
            if not success:
                self.completed.emit(color, message, self._next)
                return

            color, message, success = samkit.executeInMainThreadWithResult(self.extract, task)
            if not success:
                self.completed.emit(color, message, self._next)
                return

            color, message = samkit.executeInMainThreadWithResult(self.integrate, task)
            self.completed.emit(color, message, self._next)

        finally:
            pass
