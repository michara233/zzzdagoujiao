#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
settings_dialog.py - 设置对话框类（简约风格）
包含所有配置控件，打开时加载当前配置，保存时写回 ConfigManager。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QMessageBox,
    QScrollArea,
    QSlider,
    QWidget,
)

from config_manager import POSITION_PRESETS

# 简约风格全局样式表
STYLE_SHEET = """
QDialog {
    background-color: #F6F7FB;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    color: #2B2F36;
}

QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #EBEDF2;
    border-radius: 12px;
}

QLabel {
    color: #2B2F36;
    background: transparent;
}
QLabel#title {
    font-size: 20px;
    font-weight: 600;
    color: #1F2430;
}
QLabel#subtitle {
    font-size: 12px;
    color: #8A919F;
}
QLabel#groupTitle {
    font-size: 14px;
    font-weight: 600;
    color: #1F2430;
}
QLabel#hint {
    font-size: 12px;
    color: #8A919F;
}

QLineEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #F7F8FA;
    border: 1px solid #E1E4EA;
    border-radius: 8px;
    padding: 7px 10px;
    selection-background-color: #4A90D9;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #4A90D9;
    background-color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E1E4EA;
    border-radius: 8px;
    selection-background-color: #EAF2FB;
    selection-color: #2B2F36;
    outline: none;
}

QPushButton {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    background-color: transparent;
}
QPushButton#primaryBtn {
    background-color: #4A90D9;
    color: #FFFFFF;
    border: 1px solid #4A90D9;
}
QPushButton#primaryBtn:hover {
    background-color: #3D7FC4;
    border-color: #3D7FC4;
}
QPushButton#primaryBtn:pressed {
    background-color: #3570AD;
    border-color: #3570AD;
}
QPushButton#ghostBtn {
    background-color: #FFFFFF;
    color: #4A90D9;
    border: 1px solid #C9D6E8;
}
QPushButton#ghostBtn:hover {
    background-color: #F0F6FC;
    border-color: #4A90D9;
}
QPushButton#ghostBtn:pressed {
    background-color: #E4EFFA;
}

QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #C9D0DA;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #4A90D9;
    border-color: #4A90D9;
}
"""


class SettingsDialog(QDialog):
    """设置对话框：编辑所有配置项（简约风格 UI）。"""

    def __init__(self, config_manager, sound_player, hide_callback=None, parent=None):
        """
        :param config_manager: ConfigManager 实例
        :param sound_player: SoundPlayer 实例（用于“测试播放”）
        :param hide_callback: 立即取消显示的回调
        :param parent: 父窗口
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.sound_player = sound_player
        self.hide_callback = hide_callback

        self.setWindowTitle("桌宠设置")
        self.setMinimumSize(560, 640)
        self.resize(560, 700)
        self.setStyleSheet(STYLE_SHEET)

        self._build_ui()
        self._load_values()

    # ------------------------------------------------------------------ UI 构建
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 顶部标题头部
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(28, 24, 28, 18)
        header_layout.setSpacing(2)

        title = QLabel("桌宠设置")
        title.setObjectName("title")
        subtitle = QLabel("检测目标窗口或进程，达到阈值后弹出桌宠")
        subtitle.setObjectName("subtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        # 可滚动内容区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 6, 28, 20)
        content_layout.setSpacing(14)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # ---------- 卡片1：桌宠外观 ----------
        appearance_body = self._add_card_header(content_layout, "桌宠外观")
        form = QFormLayout(appearance_body)
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        # 图片路径
        image_row = QHBoxLayout()
        image_row.setSpacing(8)
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setPlaceholderText("选择一张本地图片（PNG/JPG/GIF）")
        self.image_browse_btn = QPushButton("浏览")
        self.image_browse_btn.setObjectName("ghostBtn")
        self.image_browse_btn.setCursor(Qt.PointingHandCursor)
        self.image_browse_btn.clicked.connect(self._browse_image)
        image_row.addWidget(self.image_path_edit, 1)
        image_row.addWidget(self.image_browse_btn)
        form.addRow("图片", image_row)

        # 图片尺寸
        size_row = QHBoxLayout()
        size_row.setSpacing(8)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 4096)
        self.width_spin.setSuffix(" px")
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 4096)
        self.height_spin.setSuffix(" px")
        size_row.addWidget(QLabel("宽"))
        size_row.addWidget(self.width_spin)
        size_row.addWidget(QLabel("高"))
        size_row.addWidget(self.height_spin)
        size_row.addStretch(1)
        form.addRow("尺寸", size_row)

        # ---------- 卡片2：触发音效 ----------
        sound_body = self._add_card_header(content_layout, "触发音效")
        form = QFormLayout(sound_body)
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        sound_row = QHBoxLayout()
        sound_row.setSpacing(8)
        self.sound_path_edit = QLineEdit()
        self.sound_path_edit.setPlaceholderText("选择一段音频（WAV/MP3），可留空")
        self.sound_browse_btn = QPushButton("浏览")
        self.sound_browse_btn.setObjectName("ghostBtn")
        self.sound_browse_btn.setCursor(Qt.PointingHandCursor)
        self.sound_browse_btn.clicked.connect(self._browse_sound)
        self.sound_test_btn = QPushButton("试听")
        self.sound_test_btn.setObjectName("ghostBtn")
        self.sound_test_btn.setCursor(Qt.PointingHandCursor)
        self.sound_test_btn.clicked.connect(self._test_sound)
        sound_row.addWidget(self.sound_path_edit, 1)
        sound_row.addWidget(self.sound_browse_btn)
        sound_row.addWidget(self.sound_test_btn)
        form.addRow("音效", sound_row)

        # ---------- 卡片3：触发时机 ----------
        timing_body = self._add_card_header(content_layout, "触发时机")
        form = QFormLayout(timing_body)
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        threshold_row = QHBoxLayout()
        threshold_row.setSpacing(8)
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 86400)
        self.threshold_spin.setSuffix(" 秒")
        self.threshold_minutes_label = QLabel("= 0 分钟")
        self.threshold_minutes_label.setObjectName("hint")
        self.threshold_spin.valueChanged.connect(self._update_minutes_label)
        threshold_row.addWidget(self.threshold_spin)
        threshold_row.addWidget(self.threshold_minutes_label)
        threshold_row.addStretch(1)
        form.addRow("时长阈值", threshold_row)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(200, 60000)
        self.interval_spin.setSuffix(" 毫秒")
        form.addRow("检测间隔", self.interval_spin)

        # ---------- 卡片4：检测目标 ----------
        target_body = self._add_card_header(content_layout, "检测目标")
        form = QFormLayout(target_body)
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.processes_edit = QTextEdit()
        self.processes_edit.setPlaceholderText("chrome.exe\nmsedge.exe\nnotepad.exe")
        self.processes_edit.setFixedHeight(76)
        proc_hint = QLabel("每个进程名占一行")
        proc_hint.setObjectName("hint")
        proc_box = QVBoxLayout()
        proc_box.addWidget(self.processes_edit)
        proc_box.addWidget(proc_hint)
        form.addRow("进程名", proc_box)

        self.keywords_edit = QTextEdit()
        self.keywords_edit.setPlaceholderText("哔哩哔哩\nYouTube\nGitHub")
        self.keywords_edit.setFixedHeight(76)
        kw_hint = QLabel("窗口标题包含任一关键词即触发")
        kw_hint.setObjectName("hint")
        kw_box = QVBoxLayout()
        kw_box.addWidget(self.keywords_edit)
        kw_box.addWidget(kw_hint)
        form.addRow("标题关键词", kw_box)

        self.foreground_only_check = QCheckBox("仅检测前台窗口（取消勾选则检测所有运行进程）")
        self.foreground_only_check.setChecked(True)
        form.addRow("检测模式", self.foreground_only_check)

        # ---------- 卡片5：位置与交互 ----------
        pos_body = self._add_card_header(content_layout, "位置与交互")
        form = QFormLayout(pos_body)
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.position_combo = QComboBox()
        for preset_key, preset_label in POSITION_PRESETS.items():
            self.position_combo.addItem(preset_label, preset_key)
        self.position_combo.currentIndexChanged.connect(self._on_position_changed)
        form.addRow("桌宠位置", self.position_combo)

        # 自定义坐标
        custom_row = QHBoxLayout()
        custom_row.setSpacing(8)
        self.custom_x_spin = QSpinBox()
        self.custom_x_spin.setRange(-10000, 10000)
        self.custom_x_spin.setSuffix(" px")
        self.custom_y_spin = QSpinBox()
        self.custom_y_spin.setRange(-10000, 10000)
        self.custom_y_spin.setSuffix(" px")
        custom_row.addWidget(QLabel("X"))
        custom_row.addWidget(self.custom_x_spin)
        custom_row.addWidget(QLabel("Y"))
        custom_row.addWidget(self.custom_y_spin)
        custom_row.addStretch(1)
        self.custom_position_widget = QWidget()
        custom_layout = QVBoxLayout(self.custom_position_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addLayout(custom_row)
        form.addRow("自定义坐标", self.custom_position_widget)

        self.mouse_penetration_check = QCheckBox("鼠标穿透（桌宠不响应鼠标事件）")
        form.addRow("鼠标", self.mouse_penetration_check)

        self.darken_check = QCheckBox("桌宠弹出时屏幕变暗")
        self.darken_check.setChecked(True)
        form.addRow("屏幕变暗", self.darken_check)

        # 变暗不透明度滑杆
        darken_row = QHBoxLayout()
        darken_row.setSpacing(8)
        self.darken_slider = QSlider()
        self.darken_slider.setOrientation(Qt.Horizontal)
        self.darken_slider.setRange(0, 100)
        self.darken_slider.setTickInterval(10)
        self.darken_opacity_label = QLabel("50%")
        self.darken_opacity_label.setMinimumWidth(40)
        self.darken_opacity_label.setObjectName("hint")
        self.darken_slider.valueChanged.connect(self._update_darken_label)
        darken_row.addWidget(self.darken_slider)
        darken_row.addWidget(self.darken_opacity_label)
        form.addRow("变暗程度", darken_row)

        self.fullscreen_check = QCheckBox("图片全屏显示")
        self.fullscreen_check.setChecked(True)
        form.addRow("全屏", self.fullscreen_check)

        # 渐变出场速度滑杆
        fade_row = QHBoxLayout()
        fade_row.setSpacing(8)
        self.fade_slider = QSlider()
        self.fade_slider.setOrientation(Qt.Horizontal)
        self.fade_slider.setRange(0, 5000)
        self.fade_slider.setTickInterval(100)
        self.fade_slider.setSingleStep(50)
        self.fade_label = QLabel("500 毫秒")
        self.fade_label.setMinimumWidth(70)
        self.fade_label.setObjectName("hint")
        self.fade_slider.valueChanged.connect(self._update_fade_label)
        fade_row.addWidget(self.fade_slider)
        fade_row.addWidget(self.fade_label)
        form.addRow("渐变速度", fade_row)

        # 显示持续时间
        duration_row = QHBoxLayout()
        duration_row.setSpacing(8)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 86400000)
        self.duration_spin.setSuffix(" 毫秒")
        self.duration_spin.setSingleStep(1000)
        self.duration_spin.setSpecialValueText("一直显示")
        duration_row.addWidget(self.duration_spin)
        duration_row.addStretch(1)
        form.addRow("显示时长", duration_row)

        # ---------- 底部按钮 ----------
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(28, 0, 28, 24)
        footer_layout.setSpacing(10)

        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setObjectName("ghostBtn")
        self.reset_btn.clicked.connect(self._reset)

        self.hide_btn = QPushButton("取消显示")
        self.hide_btn.setObjectName("ghostBtn")
        self.hide_btn.clicked.connect(self._hide_now)

        self.close_btn = QPushButton("关闭")
        self.close_btn.setObjectName("ghostBtn")
        self.close_btn.clicked.connect(self.close)

        self.save_btn = QPushButton("保存")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._save)

        footer_layout.addStretch(1)
        footer_layout.addWidget(self.reset_btn)
        footer_layout.addWidget(self.hide_btn)
        footer_layout.addWidget(self.close_btn)
        footer_layout.addWidget(self.save_btn)
        root.addWidget(footer)

    def _add_card_header(self, content_layout, title):
        """创建一个卡片 QFrame，并返回卡片内容区 QWidget（供 QFormLayout 作为父对象使用）。"""
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 18)
        card_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("groupTitle")
        card_layout.addWidget(title_label)

        # 内容区容器：后续用 QFormLayout(body_widget) 填充
        body_widget = QWidget()
        card_layout.addWidget(body_widget)

        content_layout.addWidget(card)
        return body_widget

    # ------------------------------------------------------------------ 值加载/保存
    def _load_values(self):
        """从当前配置加载到控件。"""
        cfg = self.config_manager.config

        self.image_path_edit.setText(cfg.get("image_path", ""))
        self.sound_path_edit.setText(cfg.get("sound_path", ""))

        self.threshold_spin.setValue(int(cfg.get("threshold_seconds", 1800)))
        self.interval_spin.setValue(int(cfg.get("check_interval_ms", 1000)))

        self.processes_edit.setPlainText(
            "\n".join(str(x) for x in cfg.get("target_processes", []))
        )
        self.keywords_edit.setPlainText(
            "\n".join(str(x) for x in cfg.get("target_title_keywords", []))
        )

        self.foreground_only_check.setChecked(bool(cfg.get("check_foreground_only", True)))

        self.width_spin.setValue(int(cfg.get("image_width", 300)))
        self.height_spin.setValue(int(cfg.get("image_height", 300)))

        self.custom_x_spin.setValue(int(cfg.get("custom_x", 0) or 0))
        self.custom_y_spin.setValue(int(cfg.get("custom_y", 0) or 0))

        self.mouse_penetration_check.setChecked(bool(cfg.get("mouse_penetration", False)))

        self.darken_check.setChecked(bool(cfg.get("darken_screen", True)))
        try:
            darken_opacity = int(cfg.get("darken_opacity", 50))
        except (ValueError, TypeError):
            darken_opacity = 50
        self.darken_slider.setValue(darken_opacity)
        self._update_darken_label(darken_opacity)

        self.fullscreen_check.setChecked(bool(cfg.get("fullscreen", True)))
        try:
            fade_ms = int(cfg.get("fade_in_ms", 500))
        except (ValueError, TypeError):
            fade_ms = 500
        self.fade_slider.setValue(fade_ms)
        self._update_fade_label(fade_ms)

        try:
            duration_ms = int(cfg.get("display_duration_ms", 0))
        except (ValueError, TypeError):
            duration_ms = 0
        self.duration_spin.setValue(duration_ms)

        preset = cfg.get("position_preset", "bottom_right")
        index = self.position_combo.findData(preset)
        if index < 0:
            index = 0
        self.position_combo.setCurrentIndex(index)

        self._on_position_changed(self.position_combo.currentIndex())
        self._update_minutes_label(self.threshold_spin.value())

    def _multiline_to_list(self, text):
        """将多行文本框内容解析为去除空字符串的列表。"""
        result = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                result.append(line)
        return result

    def _save(self):
        """收集控件值、写回配置并保存，立即生效（由主程序刷新应用）。"""
        position_preset = self.position_combo.currentData() or "bottom_right"

        data = {
            "image_path": self.image_path_edit.text().strip(),
            "sound_path": self.sound_path_edit.text().strip(),
            "threshold_seconds": self.threshold_spin.value(),
            "target_processes": self._multiline_to_list(self.processes_edit.toPlainText()),
            "target_title_keywords": self._multiline_to_list(self.keywords_edit.toPlainText()),
            "check_foreground_only": self.foreground_only_check.isChecked(),
            "check_interval_ms": self.interval_spin.value(),
            "image_width": self.width_spin.value(),
            "image_height": self.height_spin.value(),
            "position_preset": position_preset,
            "custom_x": self.custom_x_spin.value(),
            "custom_y": self.custom_y_spin.value(),
            "mouse_penetration": self.mouse_penetration_check.isChecked(),
            "darken_screen": self.darken_check.isChecked(),
            "darken_opacity": self.darken_slider.value(),
            "fullscreen": self.fullscreen_check.isChecked(),
            "fade_in_ms": self.fade_slider.value(),
            "display_duration_ms": self.duration_spin.value(),
        }

        self.config_manager.update(data)
        self.accept()

    def _reset(self):
        """恢复默认配置并刷新控件。"""
        reply = QMessageBox.question(
            self,
            "恢复默认",
            "确定要将所有设置恢复为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.config_manager.reset_default()
            self._load_values()

    # ------------------------------------------------------------------ 控件交互
    def _browse_image(self):
        """浏览选择图片文件。"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有文件 (*.*)",
        )
        if path:
            self.image_path_edit.setText(path)

    def _browse_sound(self):
        """浏览选择音频文件。"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音效",
            "",
            "音频文件 (*.wav *.mp3 *.ogg);;所有文件 (*.*)",
        )
        if path:
            self.sound_path_edit.setText(path)

    def _test_sound(self):
        """测试播放当前音效路径。"""
        path = self.sound_path_edit.text().strip()
        if not path:
            QMessageBox.information(self, "提示", "请先选择音效文件。")
            return
        self.sound_player.play(path)

    def _hide_now(self):
        """立即取消显示（调用主程序回调）。"""
        if self.hide_callback:
            self.hide_callback()

    def _on_position_changed(self, index):
        """位置预设变化：自定义时显示 X/Y 输入框。"""
        preset = self.position_combo.itemData(index)
        self.custom_position_widget.setVisible(preset == "custom")

    def _update_minutes_label(self, value):
        """更新分钟换算提示。"""
        minutes = value / 60.0
        self.threshold_minutes_label.setText(f"= {minutes:g} 分钟")

    def _update_darken_label(self, value):
        """更新变暗不透明度百分比提示。"""
        self.darken_opacity_label.setText(f"{value}%")

    def _update_fade_label(self, value):
        """更新渐变速度标签。"""
        if value <= 0:
            self.fade_label.setText("无渐变")
        else:
            self.fade_label.setText(f"{value} 毫秒")
