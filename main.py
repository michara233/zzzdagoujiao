#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - 桌宠程序入口
初始化 QApplication、加载配置、创建系统托盘、桌宠窗口、检测定时器与音效播放器。

依赖安装（在项目目录下执行）：
    pip install PyQt5 psutil pywin32

运行方式：
    python main.py

文件结构说明：
    main.py            程序入口，串联所有模块
    config_manager.py  配置读写（config.json）
    detector.py        目标检测（前台窗口/运行进程）
    pet_window.py      桌宠窗口（无边框、置顶、透明、可拖动、可穿透）
    sound_player.py    音效播放封装（PyQt5.QtMultimedia）
    settings_dialog.py 设置对话框
    tray_icon.py       系统托盘管理
"""

import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication

from config_manager import ConfigManager
from detector import Detector, is_windows
from overlay import ScreenDimOverlay
from pet_window import PetWindow
from sound_player import SoundPlayer
from settings_dialog import SettingsDialog
from tray_icon import TrayIcon


class PetApp:
    """主应用：负责各模块的组织协调与检测逻辑。"""

    def __init__(self, app: QApplication):
        self.app = app

        # 退出标记，防止 QApplication.quit 递归调用
        self._quitting = False

        # 1) 加载配置
        self.config_manager = ConfigManager()
        self.config_manager.load()

        # 2) 检测器
        self.detector = Detector(self.config_manager)

        # 3) 音效播放器
        self.sound_player = SoundPlayer()

        # 3.5) 全屏变暗遮罩
        self.screen_overlay = ScreenDimOverlay(self.config_manager)

        # 4) 桌宠窗口（初始隐藏）
        self.pet_window = PetWindow(self.config_manager)
        self.pet_window.hide()
        # 拖动后保存位置后，刷新主程序眼中的位置（无需额外处理）
        self.pet_window.on_position_changed = self._on_pet_position_changed

        # 5) 手动显示桌宠标记（用于托盘“显示/隐藏”手动覆盖）
        self.manual_visible = False

        # 本连续目标周期内是否已自动触发显示（防止取消后立即重弹）
        self.auto_triggered = False

        # 累计连续存在秒数
        self.active_seconds = 0

        # 6) 检测定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_tick)
        self._restart_timer_interval()

        # 6.5) 显示持续时间定时器（display_duration_ms > 0 时到时自动隐藏）
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._auto_hide_pet)

        # 7) 系统托盘
        self.tray = TrayIcon(
            app,
            callback_toggle_pet=self.toggle_pet_manual,
            callback_open_settings=self.open_settings,
            callback_hide_pet=self.hide_pet_now,
            callback_quit=self.quit_app,
        )
        self.tray.show()

        # 8) 保存设置对话框引用（避免被垃圾回收）
        self.settings_dialog = None

        # 非 Windows 平台提示
        if not is_windows():
            print("[提示] 当前非 Windows 平台，检测功能不可用（仅展示 GUI）。")

    # ------------------------------------------------------------------ 定时逻辑
    def _restart_timer_interval(self):
        """根据配置中的检测间隔重启定时器。"""
        interval = int(self.config_manager.get("check_interval_ms", 1000))
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(interval)

    def _on_tick(self):
        """定时检测目标，决定累计/重置与桌宠显示/隐藏。"""
        target_active = self.detector.is_target_active()

        # 手动显示模式下，桌宠完全由手动控制，自动逻辑不干预显示
        if self.manual_visible:
            if target_active:
                self.active_seconds += 1
            else:
                self.active_seconds = 0
            self.tray.setToolTip(f"桌宠程序（当前累计 {self.active_seconds} 秒）")
            return

        if target_active:
            # 连续存在：累计秒数 +1
            self.active_seconds += 1

            threshold = int(self.config_manager.get("threshold_seconds", 1800))

            # 达到阈值立即触发，且本周期尚未触发过（防止取消后立即重弹）
            if self.active_seconds >= threshold and not self.auto_triggered:
                if not self.pet_window.isVisible():
                    self.auto_triggered = True
                    # 先显示遮罩，再显示桌宠（桌宠置顶）
                    self.screen_overlay.show()
                    self.pet_window.show_pet()
                    # 显示时播放一次音效
                    sound_path = self.config_manager.get("sound_path", "")
                    self.sound_player.play(sound_path)
                    # 若配置了显示持续时间，则到时自动隐藏
                    self._start_hide_timer()
        else:
            # 目标消失：重置计时、隐藏桌宠、停止音效，并允许下个周期重新触发
            if self.active_seconds > 0 or self.pet_window.isVisible() or self.auto_triggered:
                self.active_seconds = 0
                self.auto_triggered = False
                self.pet_window.hide_pet()
                self.screen_overlay.hide()
                self.sound_player.stop()
                self.hide_timer.stop()

        # 更新托盘提示（可选，用于调试显示累计秒数）
        self.tray.setToolTip(f"桌宠程序（当前累计 {self.active_seconds} 秒）")

    # ------------------------------------------------------------------ 自动隐藏
    def _start_hide_timer(self):
        """根据 display_duration_ms 启动单次自动隐藏定时器（0 则不启动）。"""
        self.hide_timer.stop()
        try:
            duration = int(self.config_manager.get("display_duration_ms", 0))
        except (ValueError, TypeError):
            duration = 0
        if duration > 0:
            self.hide_timer.start(duration)

    def _auto_hide_pet(self):
        """显示持续时间到，自动隐藏桌宠、遮罩并停止音效；随后重新计时，可再次触发（循环提醒）。"""
        self.manual_visible = False
        self.auto_triggered = False  # 允许重新计时、重新触发
        self.active_seconds = 0
        self.pet_window.hide_pet()
        self.screen_overlay.hide()
        self.sound_player.stop()

    # ------------------------------------------------------------------ 配置应用
    def apply_config(self):
        """应用当前配置到桌宠窗口、遮罩与定时器（保存设置后立即调用）。"""
        self.pet_window.apply_config()
        self.screen_overlay.apply_config()
        self._restart_timer_interval()

        # 若桌宠当前正显示，按新的显示时长重新计时，避免“调整时长后图片一直存在”
        if self.pet_window.isVisible():
            self._start_hide_timer()

    # ------------------------------------------------------------------ 托盘回调
    def toggle_pet_manual(self):
        """手动切换桌宠显示/隐藏（含遮罩联动）。"""
        if self.pet_window.isVisible():
            self.manual_visible = False
            self.auto_triggered = True  # 抑制本周期自动重弹
            self.hide_timer.stop()
            self.pet_window.hide_pet()
            self.screen_overlay.hide()
            self.sound_player.stop()
        else:
            self.manual_visible = True
            self.pet_window.apply_config()  # 确保位置/图片为最新配置
            self.screen_overlay.show()
            self.pet_window.show_pet()
            # 手动显示同样遵循显示时长配置
            self._start_hide_timer()

    def hide_pet_now(self):
        """立即取消显示：隐藏桌宠、遮罩并停止音效，并抑制本周期自动重弹。"""
        self.manual_visible = False
        self.auto_triggered = True
        self.active_seconds = 0
        self.hide_timer.stop()
        self.pet_window.hide_pet()
        self.screen_overlay.hide()
        self.sound_player.stop()

    def open_settings(self):
        """打开设置对话框（关闭时仅关闭对话框，不退出程序）。"""
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(
                self.config_manager,
                self.sound_player,
                hide_callback=self.hide_pet_now,
            )
            # 保存后立即应用配置（accept 信号）
            self.settings_dialog.accepted.connect(self._on_settings_saved)

        # 每次都重新加载当前配置显示
        self.settings_dialog._load_values()
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def _on_settings_saved(self):
        """设置对话框点击“保存”后回调：立即应用新配置。"""
        self.apply_config()
        # 修改阈值后立即按新阈值判断——下一次定时检测会使用新阈值；
        # 若当前已累计超过新阈值，下一次 tick 立即触发显示。
        self.active_seconds = min(
            self.active_seconds,
            int(self.config_manager.get("threshold_seconds", 1800)),
        )

    def _on_pet_position_changed(self, x, y):
        """桌宠拖动后回调（本程序不需要额外处理，位置已写入配置）。"""
        pass

    # ------------------------------------------------------------------ 退出
    def quit_app(self):
        """安全退出：停止定时器、释放音效、退出应用。"""
        if self._quitting:
            return
        self._quitting = True

        # 停止定时器
        self.timer.stop()
        self.hide_timer.stop()

        # 隐藏并释放桌宠
        self.pet_window.hide_pet()

        # 隐藏并释放遮罩
        self.screen_overlay.release()

        # 释放音效资源
        self.sound_player.release()

        # 退出 Qt 事件循环
        self.app.quit()


def main():
    # 高 DPI 支持（在创建 QApplication 前启用，保持桌宠清晰）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭设置窗口不退出程序

    pet_app = PetApp(app)

    # 启动后直接显示设置前端，方便用户配置；关闭设置窗口后程序仍驻留系统托盘
    pet_app.open_settings()

    # 让程序在无主窗口时继续运行（由系统托盘驱动）
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())