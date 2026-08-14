#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
overlay.py - 全屏变暗遮罩模块
当桌宠弹出时，在屏幕（含多显示器）上覆盖一层半透明黑色遮罩，
营造"屏幕变暗"的效果。遮罩鼠标穿透，不阻断用户操作；桌宠显示在遮罩之上。

实现要点：
  - 为每个 QScreen 创建一个无边框、置顶、透明背景的遮罩窗口，覆盖各自屏幕。
  - 在 paintEvent 中绘制半透明黑色，不透明度由配置 darken_opacity 控制。
  - 遮罩使用 Qt.WindowTransparentForInput，鼠标点击会穿透到下层。
  - 桌宠窗口同为置顶，显示时序上遮罩先显示、桌宠后显示并 raise_，保证桌宠在上层。
"""

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QApplication, QWidget


class DimOverlay(QWidget):
    """单个屏幕的变暗遮罩窗口。"""

    def __init__(self, geometry: QRect):
        super().__init__()
        self.setGeometry(geometry)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput  # 鼠标穿透：不响应/不阻断鼠标
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._opacity = 0.50  # 0~1 浮点，默认 50%

    def set_opacity(self, opacity: float):
        """设置遮罩不透明度（0~1）。"""
        self._opacity = max(0.0, min(1.0, opacity))
        self.update()

    def paintEvent(self, event):
        """绘制半透明黑色覆盖层。"""
        painter = QPainter(self)
        alpha = int(self._opacity * 255)
        painter.fillRect(self.rect(), QColor(0, 0, 0, alpha))
        painter.end()


class ScreenDimOverlay:
    """管理所有屏幕遮罩窗口的集合。"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.overlays = []

    def _opacity_from_config(self) -> float:
        """从配置读取不透明度（0~100）并换算为 0~1 浮点。"""
        try:
            percent = int(self.config_manager.get("darken_opacity", 50))
        except (ValueError, TypeError):
            percent = 50
        return max(0, min(100, percent)) / 100.0

    def show(self):
        """按当前配置显示遮罩（若未开启变暗则不显示）。"""
        if not bool(self.config_manager.get("darken_screen", True)):
            return

        screens = QApplication.screens()
        if not screens:
            return

        opacity = self._opacity_from_config()

        # 确保遮罩数量与屏幕数量一致
        while len(self.overlays) < len(screens):
            self.overlays.append(None)

        for i, screen in enumerate(screens):
            geo = screen.geometry()  # 屏幕全局坐标区域
            if self.overlays[i] is None:
                self.overlays[i] = DimOverlay(geo)
            else:
                self.overlays[i].setGeometry(geo)
            self.overlays[i].set_opacity(opacity)
            self.overlays[i].show()
            self.overlays[i].raise_()

    def hide(self):
        """隐藏所有遮罩。"""
        for overlay in self.overlays:
            if overlay is not None:
                overlay.hide()

    def apply_config(self):
        """配置变化后刷新（不透明度/开关）。若当前可见则即时更新。"""
        if any(o is not None and o.isVisible() for o in self.overlays):
            self.show()
        else:
            self.hide()

    def release(self):
        """释放所有遮罩窗口（退出时调用）。"""
        for overlay in self.overlays:
            if overlay is not None:
                overlay.close()
        self.overlays = []