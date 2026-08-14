#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_manager.py - 配置读写模块
使用 json 模块保存/加载配置，默认配置见 DEFAULT_CONFIG。
配置文件保存在程序同目录下的 config.json。
"""

import json
import os
import sys


def _get_base_dir():
    """
    获取程序的基准目录：
    - PyInstaller 打包为 exe 后，使用 sys.executable 所在目录（config.json 与 exe 同级）；
    - 源码运行时，使用本文件所在目录。
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


# 程序同目录下的配置文件路径（打包后为 exe 同目录）
CONFIG_FILE = os.path.join(_get_base_dir(), "config.json")

def resolve_path(path):
    """
    解析相对路径为基于程序目录的绝对路径（打包后为 exe 同目录）。
    若 path 为空或已是绝对路径，则原样返回。
    """
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return os.path.join(_get_base_dir(), path)


# 内置默认配置
DEFAULT_CONFIG = {
    "image_path": "dagou.png",
    "sound_path": "dagoujiao.MP3",
    "threshold_seconds": 5,
    "target_processes": ["chrome.exe"],
    "target_title_keywords": ["哔哩哔哩", "YouTube", "GitHub"],
    "check_foreground_only": True,
    "check_interval_ms": 1000,
    "image_width": 300,
    "image_height": 300,
    "position_preset": "center",
    "custom_x": 0,
    "custom_y": 0,
    "mouse_penetration": False,
    "darken_screen": True,
    "darken_opacity": 50,
    "fullscreen": True,
    "fade_in_ms": 500,
    "display_duration_ms": 3000,
}

# 预设位置名称（用于 GUI 显示）
POSITION_PRESETS = {
    "bottom_right": "右下",
    "bottom_left": "左下",
    "top_right": "右上",
    "top_left": "左上",
    "center": "居中",
    "custom": "自定义",
}


class ConfigManager:
    """配置管理器：负责配置的加载、保存、校验与恢复默认值。"""

    def __init__(self, file_path=CONFIG_FILE):
        self.file_path = file_path
        self.config = dict(DEFAULT_CONFIG)  # 深拷贝默认配置（值均为不可变对象）

    def load(self):
        """从 JSON 文件加载配置；文件不存在或损坏时回退到默认配置并重建文件。"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # 只合并已知键，过滤非法键，并保留默认值的缺失键
                    merged = dict(DEFAULT_CONFIG)
                    for key in DEFAULT_CONFIG:
                        if key in data:
                            merged[key] = data[key]
                    self.config = self._normalize(merged)
                else:
                    self.config = dict(DEFAULT_CONFIG)
            else:
                self.config = dict(DEFAULT_CONFIG)
                self.save()
        except (json.JSONDecodeError, OSError, TypeError):
            # 文件损坏或读取失败：回退默认并重建
            self.config = dict(DEFAULT_CONFIG)
            try:
                self.save()
            except OSError:
                pass

    def save(self):
        """将当前配置写入 JSON 文件（格式化输出，便于阅读）。"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[配置] 保存失败: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def update(self, data: dict):
        """批量更新配置并做规范化校验，然后保存。"""
        for key, value in data.items():
            if key in self.config:
                self.config[key] = value
        self.config = self._normalize(self.config)
        self.save()

    def reset_default(self):
        """恢复默认配置并保存。"""
        self.config = dict(DEFAULT_CONFIG)
        self.save()

    def _normalize(self, cfg: dict) -> dict:
        """规范化配置：确保各字段类型与取值范围合法。"""
        # 阈值：正整数
        try:
            cfg["threshold_seconds"] = max(1, int(cfg["threshold_seconds"]))
        except (ValueError, TypeError):
            cfg["threshold_seconds"] = DEFAULT_CONFIG["threshold_seconds"]

        # 检测间隔：正整数毫秒，最小 200ms
        try:
            cfg["check_interval_ms"] = max(200, int(cfg["check_interval_ms"]))
        except (ValueError, TypeError):
            cfg["check_interval_ms"] = DEFAULT_CONFIG["check_interval_ms"]

        # 图片尺寸：正整数
        for dim in ("image_width", "image_height"):
            try:
                cfg[dim] = max(1, int(cfg[dim]))
            except (ValueError, TypeError):
                cfg[dim] = DEFAULT_CONFIG[dim]

        # 自定义坐标：整数
        for coord in ("custom_x", "custom_y"):
            try:
                cfg[coord] = int(cfg[coord])
            except (ValueError, TypeError):
                cfg[coord] = DEFAULT_CONFIG[coord]

        # 列表字段：确保为字符串列表
        for list_key in ("target_processes", "target_title_keywords"):
            value = cfg.get(list_key)
            if not isinstance(value, list):
                cfg[list_key] = list(DEFAULT_CONFIG[list_key])
            else:
                cfg[list_key] = [str(item) for item in value]

        # 布尔字段
        for bool_key in ("check_foreground_only", "mouse_penetration", "darken_screen", "fullscreen"):
            if not isinstance(cfg.get(bool_key), bool):
                cfg[bool_key] = DEFAULT_CONFIG[bool_key]

        # 遮罩不透明度：0~100 的整数
        try:
            cfg["darken_opacity"] = max(0, min(100, int(cfg["darken_opacity"])))
        except (ValueError, TypeError):
            cfg["darken_opacity"] = DEFAULT_CONFIG["darken_opacity"]

        # 渐入时长：0~5000 毫秒整数
        try:
            cfg["fade_in_ms"] = max(0, min(5000, int(cfg["fade_in_ms"])))
        except (ValueError, TypeError):
            cfg["fade_in_ms"] = DEFAULT_CONFIG["fade_in_ms"]

        # 显示持续时间：0~86400000 毫秒整数（0 表示一直显示直到目标消失）
        try:
            cfg["display_duration_ms"] = max(0, min(86400000, int(cfg["display_duration_ms"])))
        except (ValueError, TypeError):
            cfg["display_duration_ms"] = DEFAULT_CONFIG["display_duration_ms"]

        # 字符串字段
        for str_key in ("image_path", "sound_path", "position_preset"):
            if not isinstance(cfg.get(str_key), str):
                cfg[str_key] = DEFAULT_CONFIG[str_key]

        # 预设位置合法性
        if cfg["position_preset"] not in POSITION_PRESETS:
            cfg["position_preset"] = "bottom_right"

        return cfg