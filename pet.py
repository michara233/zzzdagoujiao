import sys
import time
import psutil
import win32gui
import win32process
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, Qt

# ================= 配置区域 =================
# 要检测的程序进程名，例如 chrome.exe、msedge.exe、notepad.exe
TARGET_PROCESSES = ["chrome.exe", "msedge.exe", "firefox.exe"]

# 要检测的窗口标题关键词，例如打开 B 站时标题通常包含“哔哩哔哩”
TARGET_TITLE_KEYWORDS = ["哔哩哔哩", "B站", "YouTube", "GitHub"]

# 检测间隔，单位毫秒（保持 1000 即可，因为计时单位是秒）
CHECK_INTERVAL = 1000

# 连续检测到目标多少秒后才显示桌宠
THRESHOLD_SECONDS = 30 * 60   # 30 分钟，你可以改成 5*60 测试

# 桌宠图片路径
IMAGE_PATH = "pet.png"

# 是否只检测前台窗口（True：仅当前台窗口是目标时才计时；False：只要目标进程在运行就计时）
CHECK_FOREGROUND = True
# ==========================================


def get_foreground_process_name():
    """获取当前前台窗口所属的进程名"""
    hwnd = win32gui.GetForegroundWindow()
    if hwnd == 0:
        return ""
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        return psutil.Process(pid).name().lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def get_foreground_window_title():
    """获取当前前台窗口标题"""
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)


def check_target():
    """检查当前是否满足目标条件（前台窗口或进程存在）"""
    if CHECK_FOREGROUND:
        # 模式一：检测前台窗口
        proc_name = get_foreground_process_name()
        if proc_name in TARGET_PROCESSES:
            return True

        title = get_foreground_window_title()
        for keyword in TARGET_TITLE_KEYWORDS:
            if keyword.lower() in title.lower():
                return True
        return False
    else:
        # 模式二：检测目标进程是否在运行（不管前台后台）
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() in TARGET_PROCESSES:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False


class PetWindow(QLabel):
    def __init__(self, image_path):
        super().__init__()

        # 无边框、置顶、不在任务栏显示
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        # 透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 加载图片，可以缩放
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(
            300, 300,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(pixmap)
        self.adjustSize()

        # 用于累计连续检测到目标的秒数
        self.active_seconds = 0

        # 初始隐藏
        self.hide()

        # 移动到屏幕右下角，可以自己改位置
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.width() - self.width() - 50,
            screen.height() - self.height() - 50
        )

    def show_pet(self):
        if not self.isVisible():
            self.show()

    def hide_pet(self):
        if self.isVisible():
            self.hide()


def main():
    app = QApplication(sys.argv)
    pet = PetWindow(IMAGE_PATH)

    def update():
        if check_target():
            pet.active_seconds += 1
        else:
            # 目标消失，计时清零，桌宠隐藏
            pet.active_seconds = 0
            pet.hide_pet()

        # 达到阈值才显示桌宠
        if pet.active_seconds >= THRESHOLD_SECONDS:
            pet.show_pet()
        else:
            pet.hide_pet()

    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(CHECK_INTERVAL)

    # 启动时先检测一次
    update()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()