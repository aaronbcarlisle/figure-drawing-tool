#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
:author:
    acarlisle

:description:
    Figure Drawing Tool, used for cycling through images for either gesture
    or long timed drawings

:to use:
    python figure_drawing_tool.py
"""

# built-in
from __future__ import annotations
import os
import sys
import random
import tempfile
from pathlib import Path
from typing import Optional

# third-party
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QLCDNumber, QSizePolicy,
    QFileDialog, QMessageBox, QApplication, QFrame, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, QTimer, QFile, QSize, QSettings
from PySide6.QtGui import (
    QPixmap, QPainter, QImageReader, QPaintEvent, QResizeEvent,
    QKeySequence, QShortcut, QTransform, QMouseEvent, QCloseEvent
)

from icons import create_icon, create_pixmap, save_icon


def resource_path(relative_path: str) -> str:
    """Get path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class FigureDrawingTool(QWidget):
    # Constants
    DEFAULT_WIDTH = 420
    DEFAULT_HEIGHT = 700
    MIN_WIDTH = 400
    MIN_HEIGHT = 300
    CLOCK_UPDATE_INTERVAL_MS = 1000
    MAX_HISTORY_SIZE = 50
    SETTINGS_ORG = "FigureDrawingTool"
    SETTINGS_APP = "FigureDrawingTool"

    def __init__(self) -> None:
        super().__init__()

        # Initialize timer references to None (fixes attribute errors)
        self.image_timer: Optional[QTimer] = None
        self.clock_timer: Optional[QTimer] = None
        self.elapse_time_seconds: int = 0
        self.remaining_seconds: int = 0

        # Image management
        self.image_list: list[str] = []
        self.image_index: int = 0
        self.current_image_path: Optional[str] = None

        # Image history for Previous button
        self.image_history: list[str] = []
        self.history_index: int = -1

        # State tracking
        self.is_running: bool = False
        self.is_paused: bool = False
        self.is_flipped_h: bool = False
        self.is_flipped_v: bool = False

        # Get supported image formats
        self.supported_extensions: set[str] = {
            bytes(fmt).decode().lower()
            for fmt in QImageReader.supportedImageFormats()
        }

        self._build_ui()
        self._setup_shortcuts()
        self._load_settings()

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Load stylesheet
        style_sheet_file = QFile(resource_path('dark.qss'))
        style_sheet_file.open(QFile.OpenModeFlag.ReadOnly)
        self.setStyleSheet(str(style_sheet_file.readAll(), encoding='utf-8'))

        # Window setup
        self.setWindowTitle("Figure Drawing Tool")
        self.setObjectName("FigureDrawingTool")
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Directory selection row
        self._build_directory_row()

        # Time settings row
        self._build_time_settings_row()

        # Image canvas (takes up remaining space)
        self._build_image_canvas()

        # Player controls
        self._build_player_controls()

        self.show()

    def _build_directory_row(self) -> None:
        """Build the image directory selection row."""
        layout = QHBoxLayout()
        self.main_layout.addLayout(layout)

        # Folder icon label
        self.image_label = QLabel()
        self.image_label.setPixmap(create_pixmap("folder_open", size=20))
        self.image_label.setToolTip("Image Directory")

        self.image_directory = QLineEdit()
        self.image_directory.setPlaceholderText("Select image folder...")
        self.image_directory.setStyleSheet("background-color: #090909;")

        self.browse_button = QPushButton(create_icon("folder_search"), "")
        self.browse_button.setToolTip("Browse for folder")
        self.browse_button.setFixedSize(28, 28)  # Icon is 24px, add padding
        self.browse_button.clicked.connect(self._browse_directory)

        self.subfolders_checkbox = QCheckBox("Subfolders")
        self.subfolders_checkbox.setToolTip("Include images from subdirectories")
        self.subfolders_checkbox.stateChanged.connect(self._on_subfolder_changed)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_directory)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.subfolders_checkbox)

    def _build_time_settings_row(self) -> None:
        """Build the time settings row with preset dropdown and custom minute/second spinboxes."""
        settings_layout = QHBoxLayout()
        self.main_layout.addLayout(settings_layout)

        # Time input (left side)
        time_input_layout = QHBoxLayout()
        time_input_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        settings_layout.addLayout(time_input_layout)

        # Clock icon
        time_label = QLabel()
        time_label.setPixmap(create_pixmap("clock", size=20))
        time_label.setToolTip("Session duration")
        time_input_layout.addWidget(time_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Preset dropdown
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Custom", (None, None))
        self.preset_combo.addItem("30 sec", (0, 30))
        self.preset_combo.addItem("1 min", (1, 0))
        self.preset_combo.addItem("2 min", (2, 0))
        self.preset_combo.addItem("5 min", (5, 0))
        self.preset_combo.addItem("10 min", (10, 0))
        self.preset_combo.addItem("15 min", (15, 0))
        self.preset_combo.addItem("20 min", (20, 0))
        self.preset_combo.setCurrentIndex(2)  # Default to 1 min
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        # Apply custom dropdown arrow icon
        arrow_path = os.path.join(tempfile.gettempdir(), "chevron_down.png")
        save_icon("chevron_down", arrow_path, size=16)
        arrow_path_css = arrow_path.replace("\\", "/")
        self.preset_combo.setStyleSheet(f"""
            QComboBox::down-arrow {{
                image: url({arrow_path_css});
                width: 12px;
                height: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
        """)
        time_input_layout.addWidget(self.preset_combo)

        # Custom time spinboxes (disabled by default since preset is not "Custom")
        # Match height to the preset combobox
        spinbox_height = self.preset_combo.sizeHint().height()

        # Also match the folder line edit height
        self.image_directory.setFixedHeight(spinbox_height)

        # Generate spinbox arrow icons
        arrow_up_path = os.path.join(tempfile.gettempdir(), "spinbox_arrow_up.png")
        arrow_down_path = os.path.join(tempfile.gettempdir(), "spinbox_arrow_down.png")
        save_icon("chevron_up", arrow_up_path, color="#cacfd2", size=12)
        save_icon("chevron_down", arrow_down_path, color="#cacfd2", size=12)
        arrow_up_css = arrow_up_path.replace("\\", "/")
        arrow_down_css = arrow_down_path.replace("\\", "/")

        spinbox_style = f"""
            QSpinBox::up-arrow {{ image: url({arrow_up_css}); }}
            QSpinBox::down-arrow {{ image: url({arrow_down_css}); }}
        """

        self.minutes_spinbox = QSpinBox()
        self.minutes_spinbox.setRange(0, 59)
        self.minutes_spinbox.setValue(1)
        self.minutes_spinbox.setSuffix(" min")
        self.minutes_spinbox.setEnabled(False)
        self.minutes_spinbox.setFixedHeight(spinbox_height)
        self.minutes_spinbox.setFixedWidth(85)
        self.minutes_spinbox.setStyleSheet(spinbox_style)
        time_input_layout.addWidget(self.minutes_spinbox)

        self.seconds_spinbox = QSpinBox()
        self.seconds_spinbox.setRange(0, 59)
        self.seconds_spinbox.setValue(0)
        self.seconds_spinbox.setSuffix(" sec")
        self.seconds_spinbox.setEnabled(False)
        self.seconds_spinbox.setFixedHeight(spinbox_height)
        self.seconds_spinbox.setFixedWidth(85)
        self.seconds_spinbox.setStyleSheet(spinbox_style)
        time_input_layout.addWidget(self.seconds_spinbox)

        # Store the base spinbox style with arrows for later use
        self._spinbox_arrow_style = spinbox_style

        # Image counter (center)
        self.image_counter_label = QLabel("")
        self.image_counter_label.setObjectName("imageCounter")
        self.image_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(self.image_counter_label)

        # Countdown display (right side)
        clock_layout = QHBoxLayout()
        clock_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        settings_layout.addLayout(clock_layout)

        self.clock = QLCDNumber()
        self.clock.setDigitCount(5)
        self.clock.display("00:00")
        clock_layout.addWidget(self.clock)

    def _on_preset_changed(self, index: int) -> None:
        """Handle preset dropdown selection."""
        is_custom = (index == 0)  # "Custom" is at index 0

        # Only change enabled state if not running (running state handles its own disabling)
        if not self.is_running:
            self.minutes_spinbox.setEnabled(is_custom)
            self.seconds_spinbox.setEnabled(is_custom)

        # Apply styling based on state
        self._apply_spinbox_styling()

        data = self.preset_combo.currentData()
        if data and data[0] is not None:
            minutes, seconds = data
            self.minutes_spinbox.setValue(minutes)
            self.seconds_spinbox.setValue(seconds)

    def _apply_spinbox_styling(self) -> None:
        """Apply appropriate styling to spinboxes based on enabled state.

        When enabled (Custom preset): dark background (#090909)
        When disabled: uses QSS disabled state (gradient)
        Always includes arrow icons.
        """
        is_custom = (self.preset_combo.currentIndex() == 0)
        is_enabled = is_custom and not self.is_running

        if is_enabled:
            # Enabled: dark background for text area + arrow icons
            spinbox_style = self._spinbox_arrow_style + " QSpinBox { background-color: #090909; }"
            self.minutes_spinbox.setStyleSheet(spinbox_style)
            self.seconds_spinbox.setStyleSheet(spinbox_style)
        else:
            # Disabled: just arrow icons, let QSS handle disabled appearance
            self.minutes_spinbox.setStyleSheet(self._spinbox_arrow_style)
            self.seconds_spinbox.setStyleSheet(self._spinbox_arrow_style)

    def _toggle_flip_h(self) -> None:
        """Toggle horizontal flip."""
        self.is_flipped_h = self.flip_h_button.isChecked()
        self.canvas.set_flip(self.is_flipped_h, self.is_flipped_v)

    def _toggle_flip_v(self) -> None:
        """Toggle vertical flip."""
        self.is_flipped_v = self.flip_v_button.isChecked()
        self.canvas.set_flip(self.is_flipped_h, self.is_flipped_v)

    def _toggle_grayscale(self) -> None:
        """Toggle grayscale mode."""
        self.canvas.set_grayscale(self.grayscale_button.isChecked())

    def _shortcut_flip_h(self) -> None:
        """Keyboard shortcut handler for horizontal flip."""
        self.flip_h_button.setChecked(not self.flip_h_button.isChecked())
        self._toggle_flip_h()

    def _shortcut_flip_v(self) -> None:
        """Keyboard shortcut handler for vertical flip."""
        self.flip_v_button.setChecked(not self.flip_v_button.isChecked())
        self._toggle_flip_v()

    def _shortcut_grayscale(self) -> None:
        """Keyboard shortcut handler for grayscale."""
        self.grayscale_button.setChecked(not self.grayscale_button.isChecked())
        self._toggle_grayscale()

    def _on_subfolder_changed(self) -> None:
        """Handle subfolder checkbox change - reload images."""
        if self.image_directory.text():
            self._load_image_list()

    def _create_h_divider(self) -> QFrame:
        """Create a horizontal divider line."""
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("background-color: rgb(60, 60, 60); border: none; margin: 0;")
        divider.setFixedHeight(2)
        return divider

    def _create_v_divider(self) -> QFrame:
        """Create a vertical divider line."""
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("background-color: rgb(60, 60, 60); border: none; margin: 0;")
        divider.setFixedWidth(2)
        return divider

    def _build_image_canvas(self) -> None:
        """Build the image display area."""
        # Horizontal divider above image
        self.main_layout.addWidget(self._create_h_divider())

        self.start_image = resource_path('start_image.jpg')
        self.canvas = Label(self.start_image)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.canvas.setMinimumSize(100, 50)  # Allow canvas to shrink when window is small
        self.canvas.setStyleSheet("background-color: #050505; margin: 0; border-radius: 0;")

        self.image_layout = QVBoxLayout()
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.image_layout, 1)  # stretch factor of 1
        self.image_layout.addWidget(self.canvas)

    def _build_player_controls(self) -> None:
        """Build the playback control buttons with image manipulation controls."""
        # Horizontal divider above controls
        self.main_layout.addWidget(self._create_h_divider())

        # Row 1: Playback controls (Pause, Prev, Next) + Image controls (Flip H, Flip V, B/W)
        controls_layout = QHBoxLayout()
        self.main_layout.addLayout(controls_layout)

        # Icon button size for all small buttons
        icon_button_size = 28  # Icon is 24px, add a few pixels padding

        pause_icon = create_icon("player_pause")
        prev_icon = create_icon("player_skip_back")
        next_icon = create_icon("player_skip_forward")

        self.pause_button = QPushButton(pause_icon, "")
        self.pause_button.setEnabled(False)
        self.pause_button.setToolTip("Pause/Resume (P)")
        self.pause_button.setFixedHeight(icon_button_size)
        self.pause_button.clicked.connect(self._toggle_pause)
        self._pause_icon = pause_icon
        controls_layout.addWidget(self.pause_button)

        self.prev_button = QPushButton(prev_icon, "")
        self.prev_button.setEnabled(False)
        self.prev_button.setToolTip("Previous image (Left Arrow)")
        self.prev_button.setFixedHeight(icon_button_size)
        self.prev_button.clicked.connect(self._previous)
        controls_layout.addWidget(self.prev_button)

        self.next_button = QPushButton(next_icon, "")
        self.next_button.setEnabled(False)
        self.next_button.setToolTip("Next image (Right Arrow)")
        self.next_button.setFixedHeight(icon_button_size)
        self.next_button.clicked.connect(self._next)
        controls_layout.addWidget(self.next_button)

        # Visual separator between playback and image controls
        controls_layout.addWidget(self._create_v_divider())

        # Image manipulation controls

        self.flip_h_button = QPushButton(create_icon("flip_horizontal"), "")
        self.flip_h_button.setCheckable(True)
        self.flip_h_button.setToolTip("Flip image horizontally (H)")
        self.flip_h_button.setFixedSize(icon_button_size, icon_button_size)
        self.flip_h_button.clicked.connect(self._toggle_flip_h)
        controls_layout.addWidget(self.flip_h_button)

        self.flip_v_button = QPushButton(create_icon("flip_vertical"), "")
        self.flip_v_button.setCheckable(True)
        self.flip_v_button.setToolTip("Flip image vertically (V)")
        self.flip_v_button.setFixedSize(icon_button_size, icon_button_size)
        self.flip_v_button.clicked.connect(self._toggle_flip_v)
        controls_layout.addWidget(self.flip_v_button)

        self.grayscale_button = QPushButton(create_icon("contrast"), "")
        self.grayscale_button.setCheckable(True)
        self.grayscale_button.setToolTip("Convert to grayscale (G)")
        self.grayscale_button.setFixedSize(icon_button_size, icon_button_size)
        self.grayscale_button.clicked.connect(self._toggle_grayscale)
        controls_layout.addWidget(self.grayscale_button)

        # Row 2: Primary Play/Stop button + Reset button
        play_layout = QHBoxLayout()
        self.main_layout.addLayout(play_layout)

        play_button_height = 34  # Taller than the icon buttons

        play_icon = create_icon("player_play_filled", color="#ffffff")
        stop_icon = create_icon("player_stop", color="#ffffff")
        reload_icon = create_icon("refresh")

        self.start_stop_button = QPushButton(play_icon, "Start")
        self.start_stop_button.setToolTip("Start/Stop session (Space)")
        self.start_stop_button.setFixedHeight(play_button_height)
        self.start_stop_button.setStyleSheet("background-color: #4a9f4a; color: #ffffff;")  # Green with white text
        self.start_stop_button.clicked.connect(self._on_start_stop)
        self._play_icon = play_icon
        self._stop_icon = stop_icon
        self._resume_icon = play_icon
        play_layout.addWidget(self.start_stop_button)

        self.restart_button = QPushButton(reload_icon, "")
        self.restart_button.setToolTip("Reset session (R)")
        self.restart_button.setFixedSize(play_button_height, play_button_height)
        self.restart_button.clicked.connect(self._restart)
        play_layout.addWidget(self.restart_button)

    def _browse_directory(self) -> None:
        """Open directory browser and load images."""
        path = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if path:
            self.image_directory.setText(path)
            self._load_image_list()

    def _load_image_list(self) -> None:
        """Load and shuffle the list of images from the selected directory."""
        directory = self.image_directory.text()
        if not directory or not os.path.isdir(directory):
            self.image_list = []
            return

        self.image_list = []
        dir_path = Path(directory)

        # Use recursive glob if subfolders checkbox is checked
        if self.subfolders_checkbox.isChecked():
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    ext = file_path.suffix.lower().lstrip('.')
                    if ext in self.supported_extensions:
                        self.image_list.append(str(file_path))
        else:
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    ext = file_path.suffix.lower().lstrip('.')
                    if ext in self.supported_extensions:
                        self.image_list.append(str(file_path))

        random.shuffle(self.image_list)
        self.image_index = 0

    def _get_next_image(self) -> Optional[str]:
        """Get the next image from the shuffled list.

        Returns None when all images have been shown (no looping).
        """
        if not self.image_list:
            return None

        if self.image_index >= len(self.image_list):
            # All images have been shown - don't loop
            return None

        image_path = self.image_list[self.image_index]
        self.image_index += 1
        return image_path

    def _toggle_controls(self, running: bool) -> None:
        """Enable/disable controls based on running state."""
        self.next_button.setEnabled(running)
        self.prev_button.setEnabled(running and len(self.image_history) > 1)
        self.pause_button.setEnabled(running)
        self.browse_button.setEnabled(not running)
        self.image_directory.setEnabled(not running)
        self.image_label.setEnabled(not running)
        self.preset_combo.setEnabled(not running)
        self.subfolders_checkbox.setEnabled(not running)

        # Spinboxes depend on both running state AND preset selection
        # Only enabled when NOT running AND "Custom" preset is selected
        is_custom = (self.preset_combo.currentIndex() == 0)
        spinbox_enabled = not running and is_custom
        self.minutes_spinbox.setEnabled(spinbox_enabled)
        self.seconds_spinbox.setEnabled(spinbox_enabled)

        # Update spinbox styling to match new state
        self._apply_spinbox_styling()

    def _on_start_stop(self) -> None:
        """Handle start/stop button click."""
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self) -> None:
        """Start the image cycling session."""
        if not self._validate_directory():
            return

        # Load images if not already loaded
        if not self.image_list:
            self._load_image_list()
            if not self.image_list:
                self._show_warning("Warning!", "No supported images found in the selected directory.")
                return

        self.is_running = True
        self.is_paused = False
        self._toggle_controls(running=True)
        self.start_stop_button.setIcon(self._stop_icon)
        self.start_stop_button.setText("Stop")
        self.start_stop_button.setStyleSheet("background-color: #c0392b; color: #ffffff;")  # Red with white text
        self.pause_button.setIcon(self._pause_icon)

        # Calculate total time in seconds
        self.elapse_time_seconds = (self.minutes_spinbox.value() * 60) + self.seconds_spinbox.value()
        if self.elapse_time_seconds == 0:
            self.elapse_time_seconds = 60  # Default to 1 minute if 0

        # Set countdown to full time
        self.remaining_seconds = self.elapse_time_seconds
        self._update_clock_display()
        self._set_clock_color("green")  # Start with green

        # Show first image
        self._cycle_images()

        # Create and start image timer
        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self._cycle_images)
        self.image_timer.start(self.elapse_time_seconds * 1000)

        # Create and start countdown timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_countdown)
        self.clock_timer.start(self.CLOCK_UPDATE_INTERVAL_MS)

    def _stop(self) -> None:
        """Stop the image cycling session."""
        self.is_running = False
        self.is_paused = False
        self._toggle_controls(running=False)
        self.start_stop_button.setIcon(self._play_icon)
        self.start_stop_button.setText("Start")
        self.start_stop_button.setStyleSheet("background-color: #4a9f4a; color: #ffffff;")  # Green with white text
        self.pause_button.setIcon(self._pause_icon)

        if self.image_timer:
            self.image_timer.stop()
        if self.clock_timer:
            self.clock_timer.stop()

        self._reset_countdown()

    def _toggle_pause(self) -> None:
        """Toggle pause state - freezes timer and image."""
        if not self.is_running:
            return

        if self.is_paused:
            # Resume
            self.is_paused = False
            self.pause_button.setIcon(self._pause_icon)
            if self.image_timer:
                self.image_timer.start(self.remaining_seconds * 1000)
            if self.clock_timer:
                self.clock_timer.start(self.CLOCK_UPDATE_INTERVAL_MS)
        else:
            # Pause
            self.is_paused = True
            self.pause_button.setIcon(self._resume_icon)
            if self.image_timer:
                self.image_timer.stop()
            if self.clock_timer:
                self.clock_timer.stop()

    def _restart(self) -> None:
        """Reset the session to initial state."""
        if self.image_timer:
            self.image_timer.stop()
        if self.clock_timer:
            self.clock_timer.stop()

        self.is_running = False
        self.is_paused = False
        self._toggle_controls(running=False)
        self.start_stop_button.setIcon(self._play_icon)
        self.start_stop_button.setText("Start")
        self.start_stop_button.setStyleSheet("background-color: #4a9f4a; color: #ffffff;")  # Green with white text
        self.pause_button.setIcon(self._pause_icon)
        self._reset_countdown()

        # Reset to start image
        self.canvas.set_image(self.start_image)

        # Reset image list and history for fresh shuffle on next start
        self.image_list = []
        self.image_index = 0
        self.image_history = []
        self.history_index = -1
        self._update_image_counter()

        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

    def _update_countdown(self) -> None:
        """Update the countdown timer (counts DOWN)."""
        self.remaining_seconds -= 1
        if self.remaining_seconds < 0:
            self.remaining_seconds = self.elapse_time_seconds
            self._set_clock_color("green")  # Reset to green for new image
        self._update_clock_display()
        self._update_clock_color()

    def _update_clock_color(self) -> None:
        """Update LCD color based on remaining time percentage."""
        if self.elapse_time_seconds == 0:
            return

        percentage = self.remaining_seconds / self.elapse_time_seconds

        if percentage <= 0.10:
            self._set_clock_color("red")
        elif percentage <= 0.50:
            self._set_clock_color("yellow")
        # Green is set at start and when timer resets

    def _set_clock_color(self, color: str) -> None:
        """Set the LCD clock color."""
        colors = {
            "green": "#2ecc71",
            "yellow": "#f1c40f",
            "red": "#e74c3c",
            "default": "rgb(202, 207, 210)"  # Match the default text color from dark.qss
        }
        self.clock.setStyleSheet(f"color: {colors.get(color, colors['default'])};")

    def _update_clock_display(self) -> None:
        """Update the LCD display with remaining time."""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.clock.display(f"{minutes:02d}:{seconds:02d}")

    def _reset_countdown(self) -> None:
        """Reset countdown display to 00:00."""
        self.remaining_seconds = 0
        self.clock.display("00:00")
        self._set_clock_color("default")

    def _validate_directory(self) -> bool:
        """Validate that a directory has been selected."""
        if not self.image_directory.text():
            self._show_warning(
                "Warning!",
                "No Image Directory has been set. "
                "Please press the '...' button at the top and select "
                "a directory that contains images."
            )
            return False
        return True

    def _show_warning(self, title: str, message: str) -> None:
        """Display a warning message box."""
        QMessageBox.warning(self, title, message)

    def _cycle_images(self) -> None:
        """Display the next image in the sequence.

        Automatically stops the session when all images have been shown.
        """
        image_path = self._get_next_image()
        if image_path:
            self.current_image_path = image_path
            self.canvas.set_image(image_path)

            # Add to history
            self.image_history.append(image_path)
            if len(self.image_history) > self.MAX_HISTORY_SIZE:
                self.image_history.pop(0)
            self.history_index = len(self.image_history) - 1

            self._update_image_counter()
            self._update_prev_button()
            self._update_next_button()

            # Reset countdown for new image
            self.remaining_seconds = self.elapse_time_seconds
            self._update_clock_display()
            self._set_clock_color("green")  # Reset to green for new image
        else:
            # No more images - stop the session
            self._stop()

    def _next(self) -> None:
        """Skip to the next image."""
        # If we're in history, go forward; otherwise get new image
        if self.history_index < len(self.image_history) - 1:
            self.history_index += 1
            image_path = self.image_history[self.history_index]
            self.current_image_path = image_path
            self.canvas.set_image(image_path)
            self._update_image_counter()
            self._update_prev_button()
            self._update_next_button()
            self.remaining_seconds = self.elapse_time_seconds
            self._update_clock_display()
            self._set_clock_color("green")  # Reset to green

            # Restart the image timer
            if self.image_timer:
                self.image_timer.stop()
                self.image_timer.start(self.elapse_time_seconds * 1000)
        elif self.image_index < len(self.image_list):
            # More images available - cycle to next
            self._cycle_images()

            # Restart the image timer
            if self.image_timer:
                self.image_timer.stop()
                self.image_timer.start(self.elapse_time_seconds * 1000)
        # else: on last image, do nothing (wait for timer to finish)

        self.next_button.setFocus()

    def _previous(self) -> None:
        """Go back to the previous image in history."""
        if self.history_index > 0:
            self.history_index -= 1
            image_path = self.image_history[self.history_index]
            self.current_image_path = image_path
            self.canvas.set_image(image_path)
            self._update_image_counter()
            self._update_prev_button()
            self._update_next_button()

            # Reset countdown for this image
            self.remaining_seconds = self.elapse_time_seconds
            self._update_clock_display()
            self._set_clock_color("green")  # Reset to green

            # Restart the image timer
            if self.image_timer:
                self.image_timer.stop()
                self.image_timer.start(self.elapse_time_seconds * 1000)

        self.prev_button.setFocus()

    def _update_prev_button(self) -> None:
        """Enable/disable previous button based on history."""
        self.prev_button.setEnabled(self.is_running and self.history_index > 0)

    def _update_next_button(self) -> None:
        """Enable/disable next button based on remaining images."""
        # Can go next if: in history and not at end, OR more images available
        can_go_next = (
            self.history_index < len(self.image_history) - 1 or
            self.image_index < len(self.image_list)
        )
        self.next_button.setEnabled(self.is_running and can_go_next)

    def _update_image_counter(self) -> None:
        """Update the image counter display."""
        if self.image_list:
            current = self.history_index + 1 if self.history_index >= 0 else 0
            total = len(self.image_list)
            self.image_counter_label.setText(f"{current} / {total}")
        else:
            self.image_counter_label.setText("")

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Space - Start/Stop
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._on_start_stop)

        # P - Pause/Resume
        QShortcut(QKeySequence(Qt.Key.Key_P), self, self._toggle_pause)

        # Right Arrow - Next
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self._next)

        # Left Arrow - Previous
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self._previous)

        # R - Reset
        QShortcut(QKeySequence(Qt.Key.Key_R), self, self._restart)

        # H - Flip Horizontal
        QShortcut(QKeySequence(Qt.Key.Key_H), self, self._shortcut_flip_h)

        # V - Flip Vertical
        QShortcut(QKeySequence(Qt.Key.Key_V), self, self._shortcut_flip_v)

        # G - Grayscale
        QShortcut(QKeySequence(Qt.Key.Key_G), self, self._shortcut_grayscale)

        # F11 - Fullscreen toggle
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, self._toggle_fullscreen)

        # Escape - Exit fullscreen
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._exit_fullscreen)

    def _toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _exit_fullscreen(self) -> None:
        """Exit fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()

    def _load_settings(self) -> None:
        """Load saved settings."""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

        # Restore window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore subfolder setting (before loading directory)
        subfolders = settings.value("subfolders", False, type=bool)
        self.subfolders_checkbox.setChecked(subfolders)

        # Restore last directory
        last_dir = settings.value("last_directory", "")
        if last_dir and os.path.isdir(last_dir):
            self.image_directory.setText(last_dir)
            self._load_image_list()

        # Restore preset selection and time settings
        preset_index = settings.value("preset_index", 2, type=int)  # Default to "1 min"
        self.preset_combo.setCurrentIndex(preset_index)

        minutes = settings.value("minutes", 1, type=int)
        seconds = settings.value("seconds", 0, type=int)
        self.minutes_spinbox.setValue(minutes)
        self.seconds_spinbox.setValue(seconds)

        # Apply initial spinbox styling based on loaded preset
        self._apply_spinbox_styling()

    def _save_settings(self) -> None:
        """Save current settings."""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

        # Save window geometry
        settings.setValue("geometry", self.saveGeometry())

        # Save last directory
        settings.setValue("last_directory", self.image_directory.text())

        # Save subfolder setting
        settings.setValue("subfolders", self.subfolders_checkbox.isChecked())

        # Save preset selection and time settings
        settings.setValue("preset_index", self.preset_combo.currentIndex())
        settings.setValue("minutes", self.minutes_spinbox.value())
        settings.setValue("seconds", self.seconds_spinbox.value())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Clear focus from input widgets when clicking on empty areas."""
        focused_widget = QApplication.focusWidget()
        if focused_widget:
            focused_widget.clearFocus()
        super().mousePressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Clean up timers and save settings on close."""
        self._save_settings()

        if self.image_timer:
            self.image_timer.stop()
        if self.clock_timer:
            self.clock_timer.stop()
        super().closeEvent(event)


class Label(QLabel):
    """Custom QLabel with aspect-ratio preserving image scaling, caching, flip, and grayscale."""

    def __init__(self, img_path: str) -> None:
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self._source_pixmap: QPixmap = QPixmap(img_path)
        self._processed_pixmap: Optional[QPixmap] = None
        self._scaled_pixmap: Optional[QPixmap] = None
        self._last_size: Optional[QSize] = None
        self._flip_h: bool = False
        self._flip_v: bool = False
        self._grayscale: bool = False

    def set_image(self, img_path: str) -> None:
        """Set a new image (reuses widget instead of recreating)."""
        self._source_pixmap = QPixmap(img_path)
        self._invalidate_cache()
        self.update()

    def set_flip(self, horizontal: bool, vertical: bool) -> None:
        """Set flip state."""
        if self._flip_h != horizontal or self._flip_v != vertical:
            self._flip_h = horizontal
            self._flip_v = vertical
            self._invalidate_cache()
            self.update()

    def set_grayscale(self, enabled: bool) -> None:
        """Set grayscale mode."""
        if self._grayscale != enabled:
            self._grayscale = enabled
            self._invalidate_cache()
            self.update()

    def _invalidate_cache(self) -> None:
        """Invalidate all cached pixmaps."""
        self._processed_pixmap = None
        self._scaled_pixmap = None

    def _get_processed_pixmap(self) -> QPixmap:
        """Get the processed pixmap (with flip/grayscale applied)."""
        if self._processed_pixmap is None:
            pixmap = self._source_pixmap

            # Apply grayscale
            if self._grayscale:
                image = pixmap.toImage()
                gray_image = image.convertToFormat(image.Format.Format_Grayscale8)
                pixmap = QPixmap.fromImage(gray_image)

            # Apply flip transformations
            if self._flip_h or self._flip_v:
                transform = QTransform()
                if self._flip_h:
                    transform.scale(-1, 1)
                if self._flip_v:
                    transform.scale(1, -1)
                pixmap = pixmap.transformed(transform)

            self._processed_pixmap = pixmap

        return self._processed_pixmap

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Invalidate scaled pixmap on resize."""
        self._scaled_pixmap = None
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Clear focus from input widgets when clicking on the canvas."""
        focused_widget = QApplication.focusWidget()
        if focused_widget:
            focused_widget.clearFocus()
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the image centered and scaled to fit."""
        size = self.size()
        processed = self._get_processed_pixmap()

        # Only rescale if size changed (caching optimization)
        if self._scaled_pixmap is None or self._last_size != size:
            self._scaled_pixmap = processed.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._last_size = size

        painter = QPainter(self)
        x = (size.width() - self._scaled_pixmap.width()) // 2
        y = (size.height() - self._scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, self._scaled_pixmap)


def main() -> None:
    app = QApplication(sys.argv)
    tool = FigureDrawingTool()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
