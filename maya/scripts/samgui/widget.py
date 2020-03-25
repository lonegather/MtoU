from Qt.QtWidgets import QApplication, QWidget, QListView, QListWidgetItem, QMenu, QAction, QSplitter
from Qt.QtGui import QIcon, QPixmap
from Qt.QtCore import Signal, Qt

import samkit
from . import access, setup_ui, Docker
from .model import GenusModel, TagModel, AssetModel, PluginModel, PluginItem, ResultItem
from .delegate import AssetDelegate, TaskDelegate, PluginDelegate


class DockerMain(Docker):

    CONTROL_NAME = 'mtou_docker_control'
    DOCK_LABEL_NAME = 'MtoU'
    UI_PATH = '%s\\ui\\main.ui' % samkit.MODULE_PATH

    def __init__(self, parent=None):
        super(DockerMain, self).__init__(parent=parent)
        setup_ui(self, self.UI_PATH)

        self.connected = False
        self.authorized = False
        self.project_id = ''
        self.current_genus = ''
        self.current_tag = ''
        self.filter = ''
        self.detail_id = ''
        self.detail_thumb = ''
        self.history = []
        self.clipboard = QApplication.clipboard()

        genus_model = GenusModel()
        tag_model = TagModel(genus_model)
        asset_model = AssetModel(tag_model)
        plugin_model = PluginModel()

        self.ui.cb_genus.setModel(genus_model)
        self.ui.cb_tag.setModel(tag_model)
        self.ui.lv_asset.setModel(asset_model)
        self.ui.tv_plugin.setModel(plugin_model)
        self.ui.lv_asset.setItemDelegate(AssetDelegate())
        self.ui.lw_task.setItemDelegate(TaskDelegate())
        self.ui.tv_plugin.setItemDelegate(PluginDelegate())

        self.ui.le_filter.setClearButtonEnabled(True)
        self.ui.detail.setVisible(False)
        self.ui.submit.setVisible(False)
        self.ui.lv_asset.setWrapping(True)
        self.ui.lv_asset.setSpacing(3)
        self.ui.lv_asset.setResizeMode(QListView.Adjust)
        self.ui.lv_asset.setViewMode(QListView.IconMode)
        self.ui.lv_asset.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tb_add.setIcon(QIcon('%s\\icons\\add.png' % samkit.MODULE_PATH))
        self.ui.tb_delete.setIcon(QIcon('%s\\icons\\delete.png' % samkit.MODULE_PATH))
        self.ui.tb_refresh.setIcon(QIcon('%s\\icons\\refresh.png' % samkit.MODULE_PATH))
        self.ui.tb_connect.setIcon(QIcon('%s\\icons\\setting.png' % samkit.MODULE_PATH))
        self.ui.tb_batch.setIcon(QIcon('%s\\icons\\batch.png' % samkit.MODULE_PATH))
        self.ui.tb_submit.setIcon(QIcon('%s\\icons\\checkin.png' % samkit.MODULE_PATH))
        self.ui.tb_sync.setIcon(QIcon('%s\\icons\\sync.png' % samkit.MODULE_PATH))
        self.ui.tb_merge.setIcon(QIcon('%s\\icons\\merge.png' % samkit.MODULE_PATH))
        self.ui.tb_revert.setIcon(QIcon('%s\\icons\\revert.png' % samkit.MODULE_PATH))

        genus_model.dataChanged.connect(self.refresh_repository_genus)
        tag_model.dataChanged.connect(self.refresh_repository_tag)
        asset_model.dataChanged.connect(self.refresh_repository_asset)
        asset_model.filtered.connect(self.refresh_repository_asset)
        self.ui.cb_genus.currentIndexChanged.connect(genus_model.notify)
        self.ui.cb_tag.currentIndexChanged.connect(tag_model.notify)
        self.ui.tb_add.clicked.connect(lambda *_: self.open_detail())
        self.ui.tb_delete.clicked.connect(lambda *_: self.delete_entity())
        self.ui.tb_connect.clicked.connect(lambda *_: self.refresh_repository(force=True))
        self.ui.lv_asset.customContextMenuRequested.connect(self.refresh_repository_context_menu)
        self.ui.lv_asset.doubleClicked.connect(self.refresh_filter)
        self.ui.tb_refresh.clicked.connect(self.refresh_repository)
        self.ui.le_filter.textChanged.connect(lambda txt: asset_model.filter(txt))

        self.ui.le_name.textChanged.connect(lambda txt: self.ui.btn_apply.setEnabled(bool(self.ui.le_name.text())))
        self.ui.btn_apply.clicked.connect(self.commit_detail)
        self.ui.btn_cancel.clicked.connect(self.close_detail)
        self.ui.cb_thumb.clicked.connect(self.thumb_detail)
        self.clipboard.dataChanged.connect(self.thumb_detail)

        self.ui.lw_task.itemSelectionChanged.connect(self.refresh_history)
        self.ui.lw_task.doubleClicked.connect(self.open_workspace)
        self.ui.lw_version.itemSelectionChanged.connect(self.refresh_history_comment)
        self.ui.tb_submit.clicked.connect(lambda: self.ui.lw_task.currentItem().submit())
        self.ui.tb_merge.clicked.connect(lambda: self.ui.lw_task.currentItem().merge())
        self.ui.tb_revert.clicked.connect(lambda: self.ui.lw_task.currentItem().revert())
        self.ui.tb_sync.clicked.connect(lambda: self.ui.lw_task.currentItem().sync())

        self.ui.tv_plugin.clicked.connect(self.refresh_check_doc)
        self.ui.tv_plugin.doubleClicked.connect(self.validate)
        self.ui.btn_check.clicked.connect(lambda: self.ui.tv_plugin.model().validate())
        self.ui.btn_export.clicked.connect(lambda: self.ui.tv_plugin.model().extract())
        self.ui.btn_submit.clicked.connect(self.integrate)
        self.ui.btn_cancel_submit.clicked.connect(self.submit_cancel)
        plugin_model.resultGenerated.connect(self.set_result_widget)
        plugin_model.dataChanged.connect(self.refresh_check_state)
        self.ui.te_comment.textChanged.connect(self.refresh_check_state)

        samkit.scriptJob(event=['SceneOpened', self.refresh_workspace])
        samkit.evalDeferred(self.refresh_repository)

    def refresh_repository(self, force=False):
        self.project_id = ''
        self.ui.lbl_project.setStyleSheet('background-color: rgba(0, 0, 0, 0);')
        self.ui.lbl_project.setText('Retrieving...')

        access(force=force)

        self.connected = samkit.hasenv(samkit.OPT_HOST)
        self.authorized = samkit.hasenv(samkit.OPT_COOKIES)
        self.ui.lbl_project.setStyleSheet('color: #000000; background-color: #CC3333;')
        self.ui.lbl_project.setText('Server Connection Error')
        if self.connected:
            self.ui.lbl_project.setStyleSheet('color: #000000; background-color: #CCCC33;')
            self.ui.lbl_project.setText(samkit.getenv(samkit.OPT_PROJECT))
            self.project_id = samkit.getenv(samkit.OPT_PROJECT_ID)
        if self.authorized:
            self.ui.lbl_project.setStyleSheet('color: #000000; background-color: #33CC33;')
        self.ui.submit.setEnabled(self.authorized)
        self.ui.workspace.setVisible(self.authorized)
        self.ui.tb_add.setEnabled(self.authorized)
        self.ui.tb_delete.setEnabled(self.authorized)
        self.ui.cb_genus.model().update()
        self.refresh_workspace()

    def refresh_repository_genus(self, *_):
        self.ui.cb_genus.setCurrentIndex(0)

    def refresh_repository_tag(self, *_):
        self.ui.cb_tag.setCurrentIndex(0)
        self.ui.cb_tag.setVisible(False)
        self.ui.cb_tag.setVisible(True)
        self.ui.tb_add.setEnabled(self.ui.cb_tag.currentIndex() >= 0)
        self.ui.tb_delete.setEnabled(self.ui.cb_tag.currentIndex() >= 0)

    def refresh_repository_asset(self, *_):
        model = self.ui.lv_asset.model()
        self.ui.lv_asset.setModel(None)
        self.ui.lv_asset.setModel(model)

    def refresh_repository_context_menu(self, position):
        current_index = self.ui.lv_asset.currentIndex()
        data_task = []
        asset_id = current_index.data(AssetModel.IdRole)

        if asset_id:
            data_task = samkit.get_data('task', entity_id=asset_id)
        if not data_task:
            return

        menu = QMenu()
        edit_action = QAction('Edit...', menu)
        edit_action.triggered.connect(lambda *_: self.open_detail(asset_id))
        if self.authorized:
            menu.addAction(edit_action)
        for task in data_task:
            stage_menu = TaskMenu(task)
            stage_menu.Checked.connect(self.checkout_repository)
            stage_menu.Referred.connect(samkit.reference)
            menu.addMenu(stage_menu)
        menu.exec_(self.ui.lv_asset.mapToGlobal(position))

    def open_detail(self, entity_id=None):
        self.clipboard.clear()
        self.detail_id = entity_id
        genus = self.ui.cb_genus.currentText()
        tag = self.ui.cb_tag.currentText()
        prefix = 'Update' if entity_id else 'Add'
        self.ui.cb_genus.setEnabled(False)
        self.ui.cb_tag.setEnabled(False)
        self.ui.le_filter.setEnabled(False)
        self.ui.tb_refresh.setEnabled(False)
        self.ui.tb_add.setEnabled(False)
        self.ui.tb_delete.setEnabled(False)
        self.ui.tb_connect.setEnabled(False)
        self.ui.lv_asset.setEnabled(False)
        self.ui.detail.setVisible(True)
        self.ui.workspace.setVisible(False)
        self.ui.cb_thumb.setChecked(False)
        self.ui.le_name.setText('')
        self.ui.le_info.setText('')
        self.ui.lbl_add.setText(u'{prefix}  {genus} - {tag}'.format(**locals()))
        self.ui.btn_apply.setText(prefix)
        self.ui.btn_apply.setEnabled(bool(self.ui.le_name.text()))

        if not entity_id:
            self.detail_thumb = '/media/thumbs/default.png'
            return

        entity = samkit.get_data('entity', id=entity_id)[0]
        self.ui.le_name.setText(entity['name'])
        self.ui.le_info.setText(entity['info'])
        self.detail_thumb = entity['thumb']
        self.thumb_detail()

    def delete_entity(self):
        current_index = self.ui.lv_asset.currentIndex()
        asset_id = current_index.data(AssetModel.IdRole)
        samkit.set_data('entity', id=asset_id, delete=True)
        self.refresh_repository()

    def thumb_detail(self):
        data = self.clipboard.mimeData()
        if self.ui.cb_thumb.isChecked() and data.hasImage():
            image = data.imageData()
        else:
            model = self.ui.lv_asset.model()
            image = model.get_image(self.detail_thumb)

        self.ui.lbl_thumb.setPixmap(QPixmap.fromImage(image))

    def close_detail(self, *_):
        self.ui.cb_genus.setEnabled(True)
        self.ui.cb_tag.setEnabled(True)
        self.ui.le_filter.setEnabled(True)
        self.ui.tb_refresh.setEnabled(True)
        self.ui.tb_add.setEnabled(True)
        self.ui.tb_delete.setEnabled(True)
        self.ui.tb_connect.setEnabled(True)
        self.ui.lv_asset.setEnabled(True)
        self.ui.detail.setVisible(False)
        self.ui.workspace.setVisible(self.authorized)

    def commit_detail(self, *_):
        name = self.ui.le_name.text()
        info = self.ui.le_info.text()
        kwargs = {
            'name': name,
            'info': info,
            'tag_id': self.ui.cb_tag.model().current_id
        }
        if self.detail_id:
            kwargs['id'] = self.detail_id

        if self.ui.cb_thumb.isChecked():
            file_path = '%s\\%s.png' % (samkit.TMP_PATH, name)
            self.ui.lbl_thumb.pixmap().scaled(128, 128).save(file_path)
            kwargs['file'] = {'thumb': open(file_path, 'rb')}

        samkit.set_data('entity', **kwargs)
        self.refresh_repository()
        self.close_detail()

    def refresh_filter(self, *_):
        pass

    def refresh_workspace(self, *_):
        try:
            self.ui.tv_plugin.model().clear()
        except RuntimeError:
            pass
        self.ui.tb_submit.setEnabled(False)
        self.ui.tb_merge.setEnabled(False)
        self.ui.tb_revert.setEnabled(False)
        self.ui.tb_sync.setEnabled(False)
        while self.ui.lw_task.count():
            self.ui.lw_task.takeItem(0)
        if not samkit.hasenv(samkit.OPT_USERNAME):
            return

        data = samkit.get_data('task', owner=samkit.getenv(samkit.OPT_USERNAME))
        for task in data:
            item = TaskItem(task, self)
            item.setSizeHint(item.widget.sizeHint())
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.ui.lw_task.addItem(item)
            self.ui.lw_task.setItemWidget(item, item.widget)

    def checkout_repository(self, task):
        if samkit.checkout(task):
            self.refresh_workspace()

    def refresh_history(self, *_):
        self.ui.te_history.setText('')
        while self.ui.lw_version.count():
            self.ui.lw_version.takeItem(0)

        item = self.ui.lw_task.currentItem()
        if not item:
            return

        task = item.data(TaskItem.TASK)
        self.history = samkit.get_history(task)
        self.ui.tb_merge.setEnabled(True)
        self.ui.tb_revert.setEnabled(True)
        self.ui.tb_submit.setEnabled(samkit.get_context('id') == task['id'])
        self.ui.lw_version.addItems(map(lambda h: '%s - %s' % (h['version'], h['time']), self.history))
        self.ui.lw_version.setCurrentRow(0)
        self.refresh_history_comment()

    def refresh_history_comment(self, *_):
        index = self.ui.lw_version.currentRow()
        if index >= 0:
            self.ui.tb_sync.setEnabled(True)
            self.ui.te_history.setText(self.history[index]['comment'] if self.history else '')

    def open_workspace(self, *_):
        item = self.ui.lw_task.currentItem()
        samkit.open_file(item.data(TaskItem.TASK))

    def refresh_check_doc(self, index):
        doc = index.data(PluginItem.PluginRole).__doc__
        doc = doc if doc else 'No description'
        self.ui.lbl_doc.setText(doc.replace('    ', ''))

    def validate(self, index):
        self.ui.tv_plugin.setExpanded(index, False)
        self.ui.tv_plugin.model().validate(index)

    def integrate(self):
        self.ui.tv_plugin.model().integrate(self.ui.te_comment.toPlainText())
        self.ui.splitter.setVisible(True)
        self.ui.submit.setVisible(False)
        self.refresh_workspace()

    def submit_cancel(self):
        self.ui.splitter.setVisible(True)
        self.ui.submit.setVisible(False)

    def refresh_check_state(self, *_):
        model = self.ui.tv_plugin.model()
        comment = self.ui.te_comment.toPlainText()
        # self.ui.btn_export.setEnabled(model.all_validated())
        self.ui.btn_submit.setEnabled(bool(comment) and model.all_validated())

    def set_result_widget(self, index):
        self.ui.tv_plugin.setIndexWidget(index, index.data(ResultItem.WidgetRole))


class TaskMenu(QMenu):

    Checked = Signal(object)
    Referred = Signal(object)

    def __init__(self, task, parent=None):
        super(TaskMenu, self).__init__(parent)
        self.setTitle(task['stage_info'])

        reference_action = TaskReferenceAction(task, self)
        reference_action.Referred.connect(lambda data: self.Referred.emit(data))
        self.addAction(reference_action)
        if samkit.hasenv(samkit.OPT_USERNAME):
            checkout_action = TaskCheckoutAction(task, self)
            checkout_action.Checked.connect(lambda data: self.Checked.emit(data))
            self.addAction(checkout_action)


class TaskCheckoutAction(QAction):

    Checked = Signal(object)

    def __init__(self, task, parent=None):
        self._data = task
        label = 'Checked Out by %s' % task['owner'] if task['owner'] else 'Check Out'
        super(TaskCheckoutAction, self).__init__(label, parent)
        self.setEnabled(not bool(task['owner']))
        self.triggered.connect(lambda *_: self.Checked.emit(self._data))


class TaskReferenceAction(QAction):

    Referred = Signal(object)

    def __init__(self, task, parent=None):
        self._data = task
        super(TaskReferenceAction, self).__init__('Create Reference', parent)
        self.setEnabled(samkit.source_path_exists(task))
        self.triggered.connect(lambda *_: self.Referred.emit(self._data))


class TaskItem(QListWidgetItem):

    UI_PATH = '%s\\ui\\task.ui' % samkit.MODULE_PATH
    ID = Qt.UserRole + 1
    PATH = Qt.UserRole + 2
    TASK = Qt.UserRole + 3

    def __init__(self, task, widget):
        super(TaskItem, self).__init__()
        self.widget = QWidget()
        self._widget = widget
        self._data = task
        self._history = samkit.get_history(task)
        self._map = {
            self.ID: 'id',
            self.PATH: 'path',
        }

        setup_ui(self.widget, self.UI_PATH)
        self.widget.setFocusPolicy(Qt.NoFocus)
        self.widget.ui.lbl_name.setText('%s - %s' % (task['tag_info'], task['entity']))
        self.widget.ui.lbl_stage.setText(task['stage_info'])
        self.update_icon(samkit.get_context('id'))

    def submit(self, *_):
        samkit.open_file(self._data)
        samkit.checkin([self._data])
        self._widget.ui.tv_plugin.model().update(self._data)
        self._widget.ui.splitter.setVisible(False)
        self._widget.ui.submit.setVisible(True)
        self._widget.ui.btn_submit.setEnabled(False)

    def merge(self, *_):
        samkit.merge(self._data)
        self._widget.refresh_workspace()

    def sync(self, *_):
        item = self._widget.ui.lw_version.currentItem()
        version_txt = item.text()
        version = version_txt.split(' - ')[0]
        version = version if self._widget.ui.lw_version.currentRow() else 'latest'
        samkit.sync(self._data, version)

    def revert(self, *_):
        samkit.revert(self._data)
        self._widget.refresh_workspace()

    def data(self, role):
        if role in self._map:
            return self._data[self._map[role]]
        elif role == self.TASK:
            return self._data
        return None

    def update_icon(self, context=None):
        if samkit.local_path_exists(self._data):
            if context == self._data['id']:
                self.widget.ui.lbl_icon.setPixmap(QPixmap('%s\\icons\\bookmark.png' % samkit.MODULE_PATH))
            else:
                self.widget.ui.lbl_icon.setPixmap(QPixmap('%s\\icons\\checked.png' % samkit.MODULE_PATH))
        else:
            self.widget.ui.lbl_icon.setPixmap(QPixmap('%s\\icons\\unavailable.png' % samkit.MODULE_PATH))
