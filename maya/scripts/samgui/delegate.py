from Qt.QtWidgets import QStyledItemDelegate, QStyle
from Qt.QtGui import QPen, QColor
from Qt.QtCore import QSize, Qt

from .model import AssetModel


class AssetDelegate(QStyledItemDelegate):

    ITEM_WIDTH = 100
    ITEM_HEIGHT = 130

    def __init__(self, parent=None):
        super(AssetDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        item_rect = option.rect.adjusted(1, 1, -1, -1)
        icon_rect = option.rect.adjusted(10, 10, -10, self.ITEM_WIDTH - self.ITEM_HEIGHT - 10)
        label_rect = item_rect.adjusted(0, self.ITEM_WIDTH, 0, 0)
        image = index.data(AssetModel.IconRole)
        painter.save()
        painter.setPen(QPen(QColor(0, 0, 0, 255)))
        painter.drawRect(item_rect)
        if option.state & QStyle.State_Selected:
            painter.fillRect(item_rect, QColor(82, 133, 166))
        if image:
            painter.drawImage(icon_rect, image)
        painter.setPen(QPen(QColor(200, 200, 200, 255)))
        painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignHCenter, index.data())
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(self.ITEM_WIDTH, self.ITEM_HEIGHT)


class TaskDelegate(QStyledItemDelegate):

    ITEM_WIDTH = 100
    ITEM_HEIGHT = 39

    def __init__(self, parent=None):
        super(TaskDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        # option.state = QStyle.State_None
        # option.rect = option.rect.adjusted(1, 8, -228, -68)
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(100, 100, 100, 255))
        super(TaskDelegate, self).paint(painter, option, index)

    def sizeHint(self, option, index):
        return QSize(self.ITEM_WIDTH, self.ITEM_HEIGHT)


class PluginDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(PluginDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        super(PluginDelegate, self).paint(painter, option, index)

    def sizeHint(self, option, index):
        return QSize(300, 30)
