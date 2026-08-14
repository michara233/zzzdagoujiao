#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sound_player.py - 音效播放封装类

说明：本模块选用 PyQt5 自带的 QtMultimedia（QMediaPlayer）播放音效，理由：
  1. QMediaPlayer 支持 WAV、MP3 等多种常见格式（QSoundEffect 仅支持 WAV）。
  2. QMediaPlayer 属于 PyQt5 内置模块，无需额外第三方依赖（pygame 在 Python 3.13+
     环境下常因缺少预编译 wheel 而无法安装）。
  3. 播放失败时静默降级，不影响桌宠显示。

注意：QMediaPlayer 必须在 QApplication 创建之后使用（本程序在 main.py 中先创建
QApplication 再实例化 SoundPlayer，满足该要求）。
"""

import os

from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from config_manager import resolve_path


class SoundPlayer:
    """音效播放器封装。负责创建 QMediaPlayer、播放单次音效与释放资源。"""

    def __init__(self):
        # 持有持久实例，播放期间保持存活，避免被垃圾回收导致声音中断
        self._player = QMediaPlayer()

    def play(self, sound_path: str):
        """
        播放指定音频文件一次（不循环）。
        若文件不存在、无法加载，则静默忽略，不报错。
        """
        # 未配置音效或路径为空：静默显示桌宠
        if not sound_path:
            return

        # 相对路径解析为基于程序目录的绝对路径（打包后为 exe 同目录）
        sound_path = resolve_path(sound_path)

        # 文件不存在：静默返回
        if not os.path.exists(sound_path):
            print(f"[音效] 文件不存在，跳过播放: {sound_path}")
            return

        try:
            # 先停止上一次播放，再加载新音频
            self._player.stop()
            media = QMediaContent(QUrl.fromLocalFile(sound_path))
            self._player.setMedia(media)
            self._player.setVolume(100)
            self._player.play()
        except Exception as e:
            print(f"[音效] 播放失败: {e}")

    def stop(self):
        """停止正在播放的音效。"""
        try:
            self._player.stop()
        except Exception:
            pass

    def release(self):
        """释放播放器资源（程序退出时调用）。"""
        self.stop()
        try:
            self._player.setMedia(QMediaContent())
        except Exception:
            pass