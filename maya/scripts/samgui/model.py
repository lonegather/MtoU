import os

from Qt.QtCore import QAbstractListModel, QModelIndex, Qt, Signal
from Qt.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QIcon
from Qt.QtWidgets import QWidget

import pyblish.api
import pyblish.util
import samkit
from . import setup_ui, ImageHub


class GenusModel(QAbstractListModel):

    genusChanged = Signal(str)
    GenusRole = Qt.UserRole + 1
    IDRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super(GenusModel, self).__init__(parent)
        self._map = {
            Qt.DisplayRole: 'info',
            self.GenusRole: 'name',
            self.IDRole: 'id',
        }
        # DATA FORMAT: [id, name, info]
        self._data = []
        self.current_id = ''

    def update(self):
        self._data = samkit.get_data('genus')
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        self.notify(0)

    def notify(self, index):
        self.current_id = self._data[index]['id'] if self._data else ''
        self.genusChanged.emit(self.current_id)

    def rowCount(self, *_):
        return len(self._data)

    def data(self, index=None, role=Qt.DisplayRole):
        if not index:
            return self._data
        if self._data:
            return self._data[index.row()].get(self._map.get(role, None), None)


class TagModel(QAbstractListModel):

    tagChanged = Signal(str)
    TagRole = Qt.UserRole + 1

    def __init__(self, genus, parent=None):
        super(TagModel, self).__init__(parent)
        self._map = {
            Qt.DisplayRole: 'info',
            self.TagRole: 'name',
        }
        self._genus = genus
        # DATA FORMAT: [id, name, info, genus_id, genus_name, genus_info]
        self._data = []
        self.current_id = self._data[0]['id'] if self._data else ''
        self._genus.genusChanged.connect(self.update)

    def update(self, genus_id):
        self._data = samkit.get_data('tag', genus_id=genus_id, project_id=samkit.getenv(samkit.OPT_PROJECT_ID))
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        self.notify(0)

    def notify(self, index):
        self.current_id = self._data[index]['id'] if self._data else ''
        self.tagChanged.emit(self.current_id)

    def rowCount(self, *_):
        return len(self._data)

    def data(self, index=None, role=Qt.DisplayRole):
        if not index:
            return self._data
        if self._data:
            return self._data[index.row()].get(self._map.get(role, None), None)


class AssetModel(QAbstractListModel):

    GenusRole = Qt.UserRole + 1
    IconRole = Qt.UserRole + 2
    IdRole = Qt.UserRole + 3

    filtered = Signal()
    
    def __init__(self, tag, parent=None):
        super(AssetModel, self).__init__(parent)
        self._map = {
            Qt.DisplayRole: 'info',
            self.GenusRole: 'genus_name',
            self.IconRole: 'image',
            self.IdRole: 'id',
        }
        self._filter = ''
        # DATA FORMAT: [id, name, info, genus_id, genus_name, genus_info, tag_id, tag_name, tag_info, link, thumb]
        self._data = []
        self._data_filter = []
        self._tag = tag
        self._hub = ImageHub()
        self._tag.tagChanged.connect(self.update)
        self._hub.ImageRequested.connect(self.image_received)

    def update(self, tag_id=None):
        tag_id = tag_id if tag_id else self._tag.current_id
        self._data = samkit.get_data('entity', tag_id=tag_id)
        self.filter(self._filter)
        self._hub.get([asset['thumb'] for asset in self._data])

    def filter(self, txt):
        self._filter = txt
        keys = [k.lower() for k in txt.split(' ') if k]
        self._data_filter = []

        for d in self._data:
            match = True
            for k in keys:
                if not (k in d['name'].lower() or k in d['info'].lower()):
                    match = False
                    break
            if match:
                self._data_filter.append(d)

        self._data_filter.sort(key=lambda e: e['name'])

        self.filtered.emit()
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def rowCount(self, *_):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if len(self._data_filter) > index.row():
            return self._data_filter[index.row()].get(self._map.get(role, None), None)
    '''
    def supportedDropActions(self):
        return Qt.CopyAction

    def flags(self, index):
        default_flags = super(AssetModel, self).flags(index)
        if index.isValid():
            return default_flags
        return Qt.ItemIsDropEnabled | default_flags

    def mimeTypes(self):
        return ['text/uri-list']

    def dropMimeData(self, data, action, row, column, parent):
        new_file = []

        for url in data.urls() or list():
            file_path = url.toLocalFile()
            file_name = os.path.split(file_path)[1]
            if file_name.split('.')[-1] not in ["ma", "mb"]:
                continue

        return True
    '''
    def get_image(self, url):
        return self._hub.icon_set.get(url, self._hub.default_image)

    def image_received(self, icon_set):
        for url in icon_set:
            image = icon_set[url]
            for data in self._data:
                if data['thumb'] == url:
                    data['image'] = image

        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def get_wrapper_data(self):
        result = []
        for asset in self._data:
            result.append({
                'id': asset['id'],
                'name': asset['name'],
                'info': asset['info'],
                'image': asset.get('image', None),
            })
        return result


class PluginModel(QStandardItemModel):

    resultGenerated = Signal(object)

    def __init__(self, parent=None):
        super(PluginModel, self).__init__(parent)
        self._task = None

        pyblish.api.deregister_all_callbacks()
        pyblish.api.register_callback('validated', self.on_validated)

    def update(self, task):
        self.clear()
        self._task = task
        root = self.invisibleRootItem()
        pyblish.api.deregister_all_plugins()
        for plugin in pyblish.api.discover():
            if plugin.order < 0.5 or plugin.order >= 1.5:
                pyblish.api.register_plugin(plugin)
                continue
            family = task['stage'] if task['tag'] != 'SC' else 'ignore'
            if plugin.families == ['*'] or family in plugin.families:
                root.appendRow(PluginItem(plugin))

    def validate(self, index=None):
        plugins = []
        if not index:
            root = self.invisibleRootItem()
            for i in range(root.rowCount()):
                plugins.append(root.child(i).data(PluginItem.PluginRole))
        else:
            if not index.data(PluginItem.PluginRole):
                command = index.data(ObjectItem.CommandRole)
                if command:
                    command()
                return
            plugins = [index.data(PluginItem.PluginRole)]
        return pyblish.util.validate(pyblish.util.collect(), plugins)

    def extract(self):
        context = self.validate()
        for result in context.data['results']:
            if not result['success']:
                if samkit.get_confirm('Validation failed, export anyway?', 'warning'):
                    return pyblish.util.extract(pyblish.util.collect())
                return
        return pyblish.util.extract(context)

    def integrate(self, comment):
        context = self.validate()
        context.data['comment'] = comment
        return pyblish.util.integrate(context)

    def on_validated(self, context):
        root = self.invisibleRootItem()
        for result in context.data['results']:
            for i in range(root.rowCount()):
                root.child(i).sync(result)
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def all_validated(self):
        root = self.invisibleRootItem()
        for i in range(root.rowCount()):
            if not root.child(i).data(PluginItem.StateRole):
                return False
        return True

    def columnCount(self, *_):
        return 1


class PluginItem(QStandardItem):

    PluginRole = Qt.UserRole + 1
    StateRole = Qt.UserRole + 2

    def __init__(self, plugin):
        super(PluginItem, self).__init__(plugin.label)
        self._plugin = plugin
        self._color = '#ccc'
        self.setEditable(False)
        self.setFlags(self.flags() & ~Qt.ItemIsSelectable)

    def sync(self, result):
        if self._plugin is result['plugin']:
            for k, v in result.items():
                if k == 'success':
                    self._color = '#3f3' if v else '#f33'
                    while self.rowCount():
                        self.takeRow(0)
                    if not v:
                        item = ResultItem(result)
                        self.appendRow(item)
                        item.setup()

    def data(self, role=None):
        if role == Qt.ForegroundRole:
            return QBrush(QColor(self._color))
        elif role == self.PluginRole:
            return self._plugin
        elif role == self.StateRole:
            return self._color == '#3f3'

        return super(PluginItem, self).data(role)


class ResultItem(QStandardItem):

    UI_PATH = '%s/ui/result.ui' % samkit.MODULE_PATH
    WidgetRole = Qt.UserRole + 3

    def __init__(self, result):
        super(ResultItem, self).__init__(str(result['error']))
        self.setFlags(self.flags() & ~Qt.ItemIsSelectable)
        self._result = result
        self.widget = QWidget()
        setup_ui(self.widget, self.UI_PATH)
        self.widget.ui.tb_fix.setIcon(QIcon('%s/icons/fix.png' % samkit.MODULE_PATH))
        self.widget.ui.le_error.setText(str(result['error']))

        self.widget.ui.tb_fix.clicked.connect(self.fix)
        if not hasattr(result['plugin'], 'fix'):
            self.widget.ui.tb_fix.setEnabled(False)
            self.widget.ui.tb_fix.setIcon(QIcon('%s/icons/fix_disabled.png' % samkit.MODULE_PATH))

    def setup(self):
        for lr in self._result['records']:
            self.appendRow(ObjectItem(lr.msg))
        self.model().resultGenerated.emit(self.index())

    def fix(self, *_):
        if self._result['plugin'].fix([lr.msg for lr in self._result['records']]):
            self.model().validate(self.parent().index())

    def data(self, role=None):
        if role == Qt.ForegroundRole:
            return QBrush(QColor('#f33'))
        elif role == self.WidgetRole:
            return self.widget

        return super(ResultItem, self).data(role)


class ObjectItem(QStandardItem):

    CommandRole = Qt.UserRole + 4

    def __init__(self, obj):
        super(ObjectItem, self).__init__(obj)
        self._cmd = lambda: samkit.cmds.select(obj, r=True)
        self.setEditable(False)

    def data(self, role=None):
        if role == Qt.ForegroundRole:
            return QBrush(QColor('#ff3'))
        elif role == self.CommandRole:
            return self._cmd

        return super(ObjectItem, self).data(role)
