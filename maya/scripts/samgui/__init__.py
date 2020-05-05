import os
import json
import pickle
import requests
from requests.exceptions import ConnectionError
from Qt.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from Qt.QtWidgets import QDialog, QWidget, QVBoxLayout, QSizePolicy, QFileDialog
from Qt.QtGui import QImage, QIcon
from Qt.QtCore import QObject, Signal, QUrl, Qt, QThread
from Qt.QtCompat import loadUi, wrapInstance

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.OpenMayaUI import MQtUtil
from maya import cmds

import samkit


def get_main_window():
    maya_win_ptr = MQtUtil.mainWindow()
    return wrapInstance(long(maya_win_ptr), QWidget)


def get_auth():
    dialog = AuthDialog(get_main_window())
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_info()
    else:
        return '*', '', '', '', '', '', ''


def access(force=False):
    host = cmds.optionVar(q=samkit.OPT_HOST)
    project_local = cmds.optionVar(q=samkit.OPT_PROJECT_ID)
    project_data = samkit.get_data('project')
    project_server = [prj['id'] for prj in project_data]
    cookies = pickle.loads(cmds.optionVar(q=samkit.OPT_COOKIES)) \
        if cmds.optionVar(exists=samkit.OPT_COOKIES) \
        else None

    if force or not host or (project_local not in project_server):
        print('Get host and user info from user.')
        host, project, prj_id, prj_root, workspace, username, password = get_auth()
        if host == '*':
            return samkit.AUTH_ABORT

        result = samkit.AUTH_SUCCESS if samkit.auth_stats(host) else samkit.login(host, username, password)

        cmds.optionVar(sv=(samkit.OPT_HOST, host))
        cmds.optionVar(sv=(samkit.OPT_PROJECT, project))
        cmds.optionVar(sv=(samkit.OPT_PROJECT_ID, prj_id))
        cmds.optionVar(sv=(samkit.OPT_PROJECT_ROOT, prj_root))
        cmds.optionVar(sv=(samkit.OPT_WORKSPACE, workspace))

        if result == samkit.CONNECT_FAILED:
            samkit.clear_ov()

        return result
    else:
        print('Retrieve host and cookies from optionVar.')
        for prj in project_data:
            if prj['id'] == project_local:
                cmds.optionVar(sv=(samkit.OPT_PROJECT, prj['info']))
                cmds.optionVar(sv=(samkit.OPT_PROJECT_ROOT, prj['root']))
        if not cookies:
            return samkit.AUTH_FAILED
        samkit.samcon.session.cookies.update(cookies)
        try:
            if not samkit.auth_stats(host):
                cmds.optionVar(remove=samkit.OPT_USERNAME)
                cmds.optionVar(remove=samkit.OPT_COOKIES)
                return samkit.AUTH_FAILED
            else:
                return samkit.AUTH_SUCCESS
        except ConnectionError:
            samkit.clear_ov()
            return samkit.CONNECT_FAILED


def setup_ui(container, ui):
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    container.ui = loadUi(ui)
    layout.addWidget(container.ui)


class Docker(MayaQWidgetDockableMixin, QWidget):

    _windows = {}
    CONTROL_NAME = 'docker_control'
    DOCK_LABEL_NAME = 'Docker'

    @classmethod
    def setup(cls, dockable=True, floating=True, area='left', restore=False):
        if cls._windows.get(cls, None) is None and dockable:
            docker = '%sWorkspaceControl' % cls.CONTROL_NAME
            if cmds.workspaceControl(docker, exists=True):
                cmds.deleteUI(docker)
            cls._windows[cls] = cls()
            cls._windows[cls].setObjectName(cls.CONTROL_NAME)
        elif not dockable:
            cls._windows[cls] = cls()
            cls._windows[cls].setObjectName(cls.CONTROL_NAME)

        if restore:
            restored_control = MQtUtil.getCurrentParent()
            mixin_ptr = MQtUtil.findControl(cls.CONTROL_NAME)
            MQtUtil.addWidgetToMayaLayout(long(mixin_ptr), long(restored_control))
        else:
            cls._windows[cls].show(
                area=area,
                dockable=dockable,
                floating=floating,
                label=cls.DOCK_LABEL_NAME,
                uiScript='%s.setup(restore=True)' % cls
            )

        return cls._windows[cls]

    def __init__(self, parent=None):
        super(Docker, self).__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setWindowTitle(self.DOCK_LABEL_NAME)
        self.setAttribute(Qt.WA_DeleteOnClose)


class AuthDialog(QDialog):

    UI_PATH = '%s/ui/auth.ui' % samkit.MODULE_PATH

    def __init__(self, parent=None):
        super(AuthDialog, self).__init__(parent)
        setup_ui(self, self.UI_PATH)
        self.project_id = []
        self.project_root = []
        self.host = ''

        self.setWindowTitle(self.ui.windowTitle())
        self.ui.tb_browse.setIcon(QIcon('%s/icons/folder.png' % samkit.MODULE_PATH))

        server = cmds.optionVar(q=samkit.OPT_HOST)
        server = server if server else ':'
        host = server.split(':')[0]
        port = server.split(':')[1]
        self.ui.le_host.setText(host)
        self.ui.le_port.setText(port if port else '8000')

        workspace = cmds.optionVar(q=samkit.OPT_WORKSPACE)
        if not os.path.exists(str(workspace)):
            workspace = cmds.workspace(q=True, directory=True)
            workspace = os.path.normpath(workspace)
            workspace = os.path.dirname(workspace)
        self.ui.le_workspace.setText(workspace)

        self.ui.accepted.connect(self.accept)
        self.ui.rejected.connect(self.reject)
        self.ui.btn_test.clicked.connect(self.conn_apply)
        self.ui.btn_login.clicked.connect(self.auth_apply)
        self.ui.tb_browse.clicked.connect(self.browse)

    def refresh(self):
        authed = samkit.auth_stats(self.host)
        username = cmds.optionVar(q=samkit.OPT_USERNAME)
        username = str(username) if username else ''
        self.ui.le_usr.setText(username)
        self.ui.le_usr.setReadOnly(authed)
        self.ui.lbl_pwd.setVisible(not authed)
        self.ui.le_pwd.setVisible(not authed)
        self.ui.le_pwd.setText('')
        self.ui.btn_login.setText('Logout' if authed else 'Login')

    def conn_apply(self, *_):
        self.project_id = []
        self.project_root = []
        self.host = '%s:%s' % (self.ui.le_host.text(), self.ui.le_port.text())
        while self.ui.cb_project.count():
            self.ui.cb_project.removeItem(0)
        url = 'http://%s/api/project' % self.host
        try:
            result = requests.get(url)
            projects = json.loads(result.text)
            for p in projects:
                self.ui.cb_project.addItem(p['info'])
                self.project_id.append(p['id'])
                self.project_root.append(p['root'])
            self.ui.btn_test.setStyleSheet('color: #000000; background-color: #33CC33')
            self.ui.wgt_workspace.setEnabled(True)
            self.refresh()
        except ConnectionError:
            self.ui.btn_test.setStyleSheet('color: #000000; background-color: #CC3333')
        except ValueError:
            self.ui.btn_test.setStyleSheet('color: #000000; background-color: #CC3333')
        finally:
            self.ui.bbox.setEnabled(True)

    def auth_apply(self, *_):
        username = self.ui.le_usr.text()
        password = self.ui.le_pwd.text()
        if self.ui.btn_login.text() == 'Logout':
            samkit.logout()
        else:
            samkit.login(self.host, username, password)
        self.refresh()

    def browse(self, *_):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dialog.setDirectory(self.ui.le_workspace.text())
        if dialog.exec_():
            path = dialog.selectedFiles()[0]
            self.ui.le_workspace.setText(path)

    def get_info(self):
        host = self.ui.le_host.text()
        port = self.ui.le_port.text()
        prj_id = self.project_id[self.ui.cb_project.currentIndex()] if len(self.project_id) else ''
        prj_root = self.project_root[self.ui.cb_project.currentIndex()] if len(self.project_root) else ''
        workspace = self.ui.le_workspace.text()

        if not os.path.exists(workspace):
            workspace = cmds.workspace(q=True, directory=True)
            workspace = os.path.normpath(workspace)
            workspace = os.path.dirname(workspace)

        return '%s:%s' % (host, port) if (host and port) else '', \
               self.ui.cb_project.currentText(), \
               prj_id, \
               prj_root, \
               workspace, \
               self.ui.le_usr.text(), \
               self.ui.le_pwd.text()


class ImageHub(QObject):

    ImageRequested = Signal(dict)
    manager = QNetworkAccessManager()
    manager_default = QNetworkAccessManager()
    icon_set = {}

    def __init__(self, parent=None):
        super(ImageHub, self).__init__(parent)
        self.ready = False
        self.default_image = QImage()
        self.manager.finished.connect(self.on_finished)
        self.manager_default.finished.connect(self.on_default_finished)

        req = QNetworkRequest(QUrl('http://%s/media/thumbs/default.png' % cmds.optionVar(q=samkit.OPT_HOST)))
        self.manager_default.get(req)

    def get(self, urls):
        self.icon_set = {}
        for url in urls:
            self.icon_set[url] = None

        if self.ready:
            self.request()

    def request(self):
        for url, image in self.icon_set.items():
            if not image:
                host = cmds.optionVar(q=samkit.OPT_HOST)
                req = QNetworkRequest(QUrl('http://%s%s' % (host, url)))
                self.manager.get(req)
                break

    def on_finished(self, reply):
        url = reply.url().path()
        image = QImage()

        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            image.loadFromData(data)
        else:
            image = self.default_image

        self.icon_set[url] = image
        self.ImageRequested.emit(self.icon_set)
        self.request()

    def on_default_finished(self, reply):
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            self.default_image.loadFromData(data)
            self.ready = True
            self.request()


class RequestThread(QThread):

    acquired = Signal(list)

    def __init__(self, url):
        super(RequestThread, self).__init__()
        self._url = url

    def run(self):
        pass
