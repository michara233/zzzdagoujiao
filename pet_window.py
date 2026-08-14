#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pet_window.py - 桌宠窗口类
继承 QLabel，实现无边框、置顶、透明背景、拖动、图片缩放、位置预设、
全屏显示与渐变出场等功能。

窗口标志使用 Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool：
  - FramelessWindowHint：无边框
  - WindowStaysOnTopHint：始终置顶
  - Tool：不在任务栏显示

鼠标穿透：使用 Qt.WindowTransparentForInput 窗口标志动态切换。
渐变出场：使用 QGraphicsOpacityEffect + QPropertyAnimation 对透明度做 0→1 动画。
"""

import os

from PyQt5.QtCore import (
    Qt,
    QPoint,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
)
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import (
    QLabel,
    QApplication,
    QGraphicsOpacityEffect,
)

from config_manager import resolve_path

# 默认边距（像素，非全屏时预设位置使用）
MARGIN = 50


class PetWindow(QLabel):
    """桌宠窗口：负责显示、缩放、拖动、位置、全屏与渐入动画。"""

    def __init__(self, config_manager):
        """
        :param config_manager: ConfigManager 实例，用于读取/保存实时配置（位置拖动后回写）。
        """
        super().__init__()

        self.config_manager = config_manager

        # 基础窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明

        # GIF 动画对象（若图片为 GIF）
        self._movie = None

        # 拖动相关状态
        self._dragging = False
        self._drag_offset = QPoint()

        # 渐变出场相关
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        # 位置变化后的回调（由 main.py 注入，用于通知主程序保存位置）
        self.on_position_changed = None

        # 根据当前配置初始化
        self.apply_config()

    # ---------------------------------------------------------------- 配置应用
    def apply_config(self):
        """根据当前配置刷新图片、尺寸、位置与鼠标穿透状态。"""
        cfg = self.config_manager.config

        # 1) 加载图片（全屏/普通模式不同缩放方式）
        self._load_image(
            cfg.get("image_path", ""),
            int(cfg.get("image_width", 300)),
            int(cfg.get("image_height", 300)),
            bool(cfg.get("fullscreen", True)),
        )

        # 2) 刷新窗口标志（鼠标穿透）
        self._apply_mouse_penetration(bool(cfg.get("mouse_penetration", False)))

        # 3) 刷新位置（全屏时直接铺满主屏幕）
        self._apply_position(bool(cfg.get("fullscreen", True)))

    # ---------------------------------------------------------------- 图片加载
    def _load_image(self, image_path, width, height, fullscreen):
        """加载并缩放图片。全屏时铺满主屏幕，普通模式按配置尺寸缩放。"""
        # 先停止旧动画
        if self._movie is not None:
            self._movie.stop()
            self.setMovie(None)
            self._movie = None

        # 相对路径解析为基于程序目录的绝对路径（打包后为 exe 同目录）
        image_path = resolve_path(image_path)

        # 确定目标缩放尺寸
        if fullscreen:
            screen = QApplication.primaryScreen()
            if screen is None:
                target_w, target_h = width, height
            else:
                geo = screen.geometry()
                target_w, target_h = geo.width(), geo.height()
        else:
            target_w, target_h = width, height

        if not image_path or not os.path.exists(image_path):
            # 无有效图片：显示透明占位
            self.setPixmap(QPixmap())
            if fullscreen:
                self.resize(target_w, target_h)
            return

        ext = os.path.splitext(image_path)[1].lower()

        # GIF 使用 QMovie 实现动画
        if ext == ".gif":
            movie = QMovie(image_path)
            if movie.isValid():
                first = movie.currentPixmap()
                if first.isNull():
                    self.setPixmap(QPixmap())
                    self.resize(target_w, target_h)
                    return
                scaled_size = self._scale_size(first.size(), target_w, target_h, fullscreen)
                movie.setScaledSize(scaled_size)
                self.setMovie(movie)
                self._movie = movie
                movie.start()
                self.resize(scaled_size)
            else:
                self.setPixmap(QPixmap())
                self.resize(target_w, target_h)
            return

        # 静态图片使用 QPixmap
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.setPixmap(QPixmap())
            self.resize(target_w, target_h)
            return

        scaled = pixmap.scaled(
            target_w,
            target_h,
            Qt.KeepAspectRatioByExpanding if fullscreen else Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.setPixmap(scaled)

        # 全屏时窗口铺满屏幕；普通模式调整到图片实际尺寸
        if fullscreen:
            self.resize(target_w, target_h)
        else:
            self.resize(scaled.size())

    def _scale_size(self, source_size, target_w, target_h, fullscreen):
        """计算缩放后的尺寸。全屏用 Expanding 填满，普通用 KeepAspectRatio 适配。"""
        sw, sh = source_size.width(), source_size.height()
        if sw <= 0 or sh <= 0:
            return QSize(target_w, target_h)
        if fullscreen:
            scale = max(target_w / sw, target_h / sh)
        else:
            scale = min(target_w / sw, target_h / sh)
        return QSize(int(sw * scale), int(sh * scale))

    # ---------------------------------------------------------------- 位置
    def _apply_position(self, fullscreen):
        """全屏时铺满主屏幕；否则按预设位置（或自定义坐标）放置。"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return

        if fullscreen:
            geo = screen.geometry()  # 全局坐标
            self.move(geo.x(), geo.y())
            return

        avail = screen.availableGeometry()  # 可用屏幕区域（排除任务栏）
        preset = self.config_manager.get("position_preset", "center")
        custom_x = int(self.config_manager.get("custom_x", 0) or 0)
        custom_y = int(self.config_manager.get("custom_y", 0) or 0)

        w = self.width()
        h = self.height()

        if preset == "custom":
            x = custom_x
            y = custom_y
        elif preset == "bottom_right":
            x = avail.right() - w + 1 - MARGIN
            y = avail.bottom() - h + 1 - MARGIN
        elif preset == "bottom_left":
            x = avail.left() + MARGIN
            y = avail.bottom() - h + 1 - MARGIN
        elif preset == "top_right":
            x = avail.right() - w + 1 - MARGIN
            y = avail.top() + MARGIN
        elif preset == "top_left":
            x = avail.left() + MARGIN
            y = avail.top() + MARGIN
        else:  # center
            x = avail.left() + (avail.width() - w) // 2
            y = avail.top() + (avail.height() - h) // 2

        self.move(x, y)

    # ---------------------------------------------------------------- 鼠标穿透
    def _apply_mouse_penetration(self, enabled: bool):
        """动态切换鼠标穿透。穿透开启后，窗口不响应鼠标事件。"""
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowTransparentForInput
        else:
            flags &= ~Qt.WindowTransparentForInput
        self.setWindowFlags(flags)

    # ---------------------------------------------------------------- 拖动
    def mousePressEvent(self, event):
        """鼠标按下：记录拖动起始偏移（穿透开启时不会收到此事件）。"""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动：拖动窗口跟随鼠标。"""
        if self._dragging and (event.buttons() & Qt.LeftButton):
            new_pos = event.globalPos() - self._drag_offset
            self.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放：结束拖动，并将新位置保存到配置（切换为自定义坐标）。"""
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            pos = self.pos()
            # 将当前位置保存为“自定义”坐标
            self.config_manager.set("position_preset", "custom")
            self.config_manager.set("custom_x", pos.x())
            self.config_manager.set("custom_y", pos.y())
            self.config_manager.save()
            if self.on_position_changed:
                self.on_position_changed(pos.x(), pos.y())
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # ---------------------------------------------------------------- 显示/隐藏（含渐变）
    def show_pet(self):
        """显示桌宠，并以渐入动画出场（全屏时铺满屏幕）。"""
        self._fade_anim.stop()

        # 全屏模式先确保铺满主屏幕
        if bool(self.config_manager.get("fullscreen", True)):
            self._apply_position(True)

        fade = int(self.config_manager.get("fade_in_ms", 500))
        self._opacity_effect.setOpacity(0.0)
        self.show()
        self.raise_()

        if fade > 0:
            self._fade_anim.setDuration(fade)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()
        else:
            self._opacity_effect.setOpacity(1.0)

    def hide_pet(self):
        """隐藏桌宠，并复位透明度以便下次渐入。"""
        self._fade_anim.stop()
        self._opacity_effect.setOpacity(1.0)
        self.hide()