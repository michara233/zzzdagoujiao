#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tray_icon.py - 系统托盘管理
创建系统托盘图标与右键菜单：
  - 显示/隐藏桌宠
  - 打开设置
  - 退出程序
"""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt


def create_tray_icon_pixmap(size=64):
    """
    生成一个简单的圆形图标（像素绘制）作为托盘图标。
    若无需图标可返回 null QIcon；这里用代码绘制避免依赖外部图片文件。
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 画一个橙色圆形
    painter.setBrush(QColor("#ff9800"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)

    # 画两个白色眼睛
    painter.setBrush(QColor("#ffffff"))
    painter.drawEllipse(int(size * 0.28), int(size * 0.35), int(size * 0.14), int(size * 0.14))
    painter.drawEllipse(int(size * 0.58), int(size * 0.35), int(size * 0.14), int(size * 0.14))

    # 画黑色瞳孔
    painter.setBrush(QColor("#000000"))
    painter.drawEllipse(int(size * 0.32), int(size * 0.39), int(size * 0.06), int(size * 0.06))
    painter.drawEllipse(int(size * 0.62), int(size * 0.39), int(size * 0.06), int(size * 0.06))

    # 画微笑
    painter.setPen(QColor("#000000"))
    painter.drawArc(
        int(size * 0.3),
        int(size * 0.45),
        int(size * 0.4),
        int(size * 0.3),
        0,
        180 * 16,
    )
    painter.end()

    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标封装。"""

    def __init__(self, app, callback_toggle_pet, callback_open_settings, callback_hide_pet, callback_quit, parent=None):
        """
        :param app: QApplication 实例
        :param callback_toggle_pet: 切换桌宠显示/隐藏的回调
        :param callback_open_settings: 打开设置对话框的回调
        :param callback_hide_pet: 立即取消（隐藏）桌宠的回调
        :param callback_quit: 退出程序的回调
        :param parent: 父对象
        """
        super().__init__(parent)

        self.callback_toggle_pet = callback_toggle_pet
        self.callback_open_settings = callback_open_settings
        self.callback_hide_pet = callback_hide_pet
        self.callback_quit = callback_quit

        # 设置图标与提示
        self.setIcon(create_tray_icon_pixmap())
        self.setToolTip("桌宠程序")

        # 构建菜单
        self._build_menu()

        # 双击托盘图标打开设置
        self.activated.connect(self._on_activated)

    def _build_menu(self):
        """构建右键菜单。"""
        menu = QMenu()

        self.toggle_action = QAction("显示/隐藏桌宠", self)
        self.toggle_action.triggered.connect(self.callback_toggle_pet)

        self.hide_action = QAction("立即取消显示", self)
        self.hide_action.triggered.connect(self.callback_hide_pet)

        self.settings_action = QAction("打开设置", self)
        self.settings_action.triggered.connect(self.callback_open_settings)

        self.quit_action = QAction("退出程序", self)
        self.quit_action.triggered.connect(self.callback_quit)

        menu.addAction(self.toggle_action)
        menu.addAction(self.hide_action)
        menu.addAction(self.settings_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        """双击托盘图标时打开设置。"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.callback_open_settings()
        elif reason == QSystemTrayIcon.Trigger:
            # 单击也可打开设置（可选）
            pass