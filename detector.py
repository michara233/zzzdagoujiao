#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detector.py - 检测模块
负责获取 Windows 前台窗口的进程名、窗口标题，并判断目标是否满足条件。

检测目标类型（满足任一即视为“目标存在”）：
  1. 前台窗口所属进程名在用户配置的进程名列表中（如 chrome.exe）。
  2. 前台窗口标题包含用户配置的关键词列表中的任意一个。

同时支持“检测所有运行进程”模式：
  - 只要目标进程在系统中运行（无论是否前台）即计为存在；
  - 此时不检测窗口标题（仅进程名）。

依赖：pywin32（win32gui、win32process）、psutil。
"""

import os
import sys
import psutil

# Windows 专属模块（非 Windows 平台无法导入）
IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    try:
        import win32gui
        import win32process
    except ImportError:
        IS_WINDOWS = False


def is_windows():
    """返回当前是否为 Windows 平台。"""
    return IS_WINDOWS


def get_foreground_process_name():
    """
    获取当前前台窗口所属进程名（如 'chrome.exe'）。
    失败或非 Windows 时返回空字符串。
    """
    if not IS_WINDOWS:
        return ""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return ""
        # 通过窗口句柄获取线程/进程 ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return ""
        # 优先使用进程名（.name()），失败时回退 exe 文件名
        try:
            proc = psutil.Process(pid)
            name = proc.name() or ""
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            name = ""
        if not name:
            # 回退：通过 exe 路径取文件名
            try:
                exe = psutil.Process(pid).exe() or ""
                name = os.path.basename(exe)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                name = ""
        return name.lower()
    except Exception as e:
        print(f"[检测] 获取前台进程名失败: {e}")
        return ""


def get_foreground_window_title():
    """
    获取当前前台窗口标题。
    失败或非 Windows 时返回空字符串。
    """
    if not IS_WINDOWS:
        return ""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return ""
        title = win32gui.GetWindowText(hwnd)
        return title or ""
    except Exception as e:
        print(f"[检测] 获取前台窗口标题失败: {e}")
        return ""


def get_running_process_names():
    """
    获取系统中所有正在运行的进程名集合（小写，用于“检测所有运行进程”模式）。
    失败时返回空集合。
    """
    names = set()
    try:
        for proc in psutil.process_iter():
            try:
                name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            if name:
                names.add(name.lower())
    except Exception as e:
        print(f"[检测] 枚举进程失败: {e}")
    return names


def normalize_entries(values):
    """
    将用户输入的进程名/关键词列表清洗：去除空项、去除首尾空格并转为小写（用于比较）。
    :param values: 原始字符串列表
    :return: 清洗后的小写字符串列表
    """
    result = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            result.append(text.lower())
    return result


class Detector:
    """目标检测器：根据配置判断目标当前是否存在。"""

    def __init__(self, config_manager):
        """
        :param config_manager: ConfigManager 实例，用于读取实时配置。
        """
        self.config_manager = config_manager

    def is_target_active(self):
        """
        判断目标是否处于“存在”状态。
        - 前台模式：进程名在列表中 或 窗口标题包含任一关键词。
        - 所有进程模式：任一目标进程在系统运行（仅进程名，不检测标题）。
        :return: bool
        """
        if not IS_WINDOWS:
            return False

        # 每次实时读取配置，保证动态修改立即生效
        target_processes = normalize_entries(
            self.config_manager.get("target_processes", [])
        )
        target_keywords = normalize_entries(
            self.config_manager.get("target_title_keywords", [])
        )
        check_foreground = self.config_manager.get("check_foreground_only", True)

        if check_foreground:
            # --- 前台窗口模式 ---
            process_name = get_foreground_process_name()
            # 条件一：进程名匹配
            if process_name and process_name in target_processes:
                return True

            # 条件二：窗口标题包含任一关键词
            if target_keywords:
                title = get_foreground_window_title().lower()
                for keyword in target_keywords:
                    if keyword in title:
                        return True
            return False
        else:
            # --- 检测所有运行进程模式（仅进程名） ---
            if not target_processes:
                return False
            running_names = get_running_process_names()
            for proc in target_processes:
                if proc in running_names:
                    return True
            return False