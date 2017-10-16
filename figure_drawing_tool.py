#!/usr/bin/python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------#
#-------------------------------------------------------------------- HEADER --#

"""
:author:
    acarlisle

:description:
    Figure Drawing Tool, used for cycling through images for either gesture
    or long timed drawings

:to use:
    python figure_drawing_tool.py
"""

#------------------------------------------------------------------------------#
#------------------------------------------------------------------- IMPORTS --#

# built-in
import os, sys, timeit
from random import shuffle

# third-party
from PySide import QtGui, QtCore

#------------------------------------------------------------------------------#
#--------------------------------------------------------------------- UTILS --#

def convert_path(path):
    """Converts to Windows readable path"""
    separator = os.sep
    if separator != "/":
        path = path.replace(os.sep, "/")
    return path

def build_path(folder, name):
    return convert_path(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                     folder, name))

def update_line_edit(line_edit_widget):
    """Finds path and populates QLineEdit"""
    path = QtGui.QFileDialog.getExistingDirectory()
    if path:
        return line_edit_widget.setText(path)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

#------------------------------------------------------------------------------#
#------------------------------------------------------------------- CLASSES --#


class FigureDrawingTool(QtGui.QWidget):
    def __init__(self):
        super(FigureDrawingTool, self).__init__()

        # globals
        self._build_canvas()
        self.elapse_time = None
        self.supported_formats = tuple(QtGui.QImageReader.supportedImageFormats())

    def _build_canvas(self):

        # set styling
        style_sheet_file = QtCore.QFile(resource_path('dark.qss'))
        style_sheet_file.open(QtCore.QFile.ReadOnly)
        self.setStyleSheet(str(style_sheet_file.readAll()))

        # define window
        self.setWindowTitle("Figure Drawing Tool")
        self.setObjectName("FigureDrawingTool")
        self.resize(420, 700)
        self.setMinimumSize(400, 300)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        # main layout
        self.main_layout = QtGui.QVBoxLayout(self)

        # root directory
        image_directory_layout = QtGui.QHBoxLayout()
        self.main_layout.addLayout(image_directory_layout)

        self.image_label = QtGui.QLabel("Image Directory: ")
        self.image_label.setStyleSheet("font-size: 12px;")
        self.image_directory = QtGui.QLineEdit()
        self.browse_button = QtGui.QPushButton("...")
        self.browse_button.setObjectName('roundedButton')
        image_directory_layout.addWidget(self.image_label)
        image_directory_layout.addWidget(self.image_directory)
        image_directory_layout.addWidget(self.browse_button)

        # settings layout
        settings_layout = QtGui.QHBoxLayout()
        self.main_layout.addLayout(settings_layout)

        # set time layout
        set_time_layout = QtGui.QHBoxLayout()
        set_time_layout.setAlignment(QtCore.Qt.AlignLeft)
        settings_layout.addLayout(set_time_layout)

        self.set_time = QtGui.QDoubleSpinBox()
        self.set_time.setPrefix("TIME: ")
        self.set_time.setStyleSheet("border: none; font-size: 16px;")
        self.set_time.setValue(1)

        set_time_layout.addWidget(self.set_time)

        # timer
        clock_layout = QtGui.QHBoxLayout()
        clock_layout.setAlignment(QtCore.Qt.AlignRight)
        settings_layout.addLayout(clock_layout)

        self.clock = QtGui.QLCDNumber()
        self.clock.setNumDigits(8)
        self.time = QtCore.QTime(0, 0)
        self.clock.display(self.time.toString('mm:ss'))

        clock_layout.addWidget(self.clock)

        # spacer
        vertical_spacer = QtGui.QSpacerItem(20, 291, QtGui.QSizePolicy.Minimum,
                                            QtGui.QSizePolicy.Expanding)
        self.main_layout.addItem(vertical_spacer)

        # header
        self.start_image = resource_path('start_image.jpg')
        self.canvas = Label(self.start_image)

        self.pixmap = QtGui.QPixmap(self.start_image)
        self.canvas.setPixmap(self.pixmap)

        self.image_layout = QtGui.QVBoxLayout()
        self.image_layout.setAlignment(QtCore.Qt.AlignVCenter)
        self.main_layout.addLayout(self.image_layout)
        self.image_layout.addWidget(self.canvas)

        # spacer
        vertical_spacer = QtGui.QSpacerItem(20, 291, QtGui.QSizePolicy.Minimum,
                                            QtGui.QSizePolicy.Expanding)
        self.main_layout.addItem(vertical_spacer)

        # player controls
        player_controls_layout = QtGui.QHBoxLayout()
        self.main_layout.addLayout(player_controls_layout)

        self.start_stop_button = QtGui.QPushButton("Start")
        self.next_button = QtGui.QPushButton(">")
        self.next_button.setEnabled(False)
        self.next_button.setMaximumWidth(60)
        self.restart_button = QtGui.QPushButton("<<")
        self.restart_button.setMaximumWidth(70)

        player_controls_layout.addWidget(self.start_stop_button)
        player_controls_layout.addWidget(self.next_button)
        player_controls_layout.addWidget(self.restart_button)

        self.start_stop_button.clicked.connect(self._start)
        self.restart_button.clicked.connect(self._restart)
        self.next_button.clicked.connect(self._next)
        self.browse_button.clicked.connect(lambda: update_line_edit(self.image_directory))

        self.show()

    def toggle(self):
        self._toggle([self.next_button, self.restart_button,
                      self.browse_button, self.image_directory,
                      self.image_label, self.set_time])

    def _toggle(self, widgets):
        for widget in widgets:
            if widget.isEnabled():
                widget.setEnabled(False)
            elif not widget.isEnabled():
                widget.setEnabled(True)

    def warning_notice(self, title, message):
        message_box = QtGui.QMessageBox.warning(self, title, message)
        return message_box

    def _next(self):
        self._stop()
        self._start()
        self.next_button.setFocus()

    def _start(self):
        # toggle, start, stop
        if not self._error_check():
            message = "No Image Directory has been set. "
            message += "Please press the '...' button at the top and search for"
            message += " a directory that contains images."
            return self.warning_notice("Warning!", message)
        if self.start_stop_button.text() == "Stop":
            return self._stop()
        self.toggle()
        self.start_stop_button.setText("Stop")

        # set first image
        self._cycle_images()

        # calculate elapse time
        minutes = str(self.set_time.value()).split(".")[0]
        seconds = str(self.set_time.value()).split(".")[1]
        if len(seconds) == 1:
            seconds = seconds + str(0)
        self.elapse_time = ((int(minutes) * 60) + int(seconds)) * 1000

        # create image timer
        self.image_timer = QtCore.QTimer()

        # connect image timer
        self.image_timer.timeout.connect(self._cycle_images)
        self.image_timer.start(self.elapse_time)

        # create clock timer
        self.clock_timer = QtCore.QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

    def _update_clock(self):
        self.time = self.time.addSecs(1)
        self.clock.display(self.time.toString('mm:ss'))

    def _show_time(self):
        time = QtCore.QTime.currentTime()
        text = time.toString('hh:mm')
        if (time.second() % 2) == 0:
            text = text[:2] + ' ' + text[3:]

    def _stop(self):
        self.toggle()
        self.start_stop_button.setText("Start")
        self._reset_clock()

        self.image_timer.stop()
        self.clock_timer.stop()

    def _restart(self):
        if not self._error_check():
            return
        self._start()
        self._stop()
        self._reset_clock()
        self._reset_time()
        self.image_timer.stop()
        self.clock_timer.stop()
        self._add_image_to_canvas(self.start_image)
        self.resize(420, 700)

    def _reset_clock(self):
        self.time = QtCore.QTime(0, 0)
        self.clock.display(self.time.toString('mm:ss'))

    def _reset_time(self):
        self.set_time.setValue(1)

    def _error_check(self):
        if not self.image_directory.text():
            return
        return True

    def _cycle_images(self):
        image_dir = convert_path(self.image_directory.text())
        images = os.listdir(image_dir)
        shuffle(images)

        # stop if the time have elapsed
        for path in images:
            full_path = "{0}/{1}".format(image_dir, path)
            if not full_path.endswith(self.supported_formats):
                continue
            self._add_image_to_canvas(full_path)
            break
            
        self._reset_clock()

    def _add_image_to_canvas(self, full_path):
        for i in reversed(range(self.image_layout.count())):
            self.image_layout.itemAt(i).widget().deleteLater()
        canvas = Label(full_path)
        self.image_layout.addWidget(canvas)
        pixmap = QtGui.QPixmap(full_path)
        size = pixmap.size()
        canvas.setPixmap(pixmap)

        
class Label(QtGui.QLabel):
    def __init__(self, img):
        super(Label, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.pixmap = QtGui.QPixmap(img)

    def paintEvent(self, event):
        size = self.size()
        painter = QtGui.QPainter(self)
        point = QtCore.QPoint(0,0)
        scaled = self.pixmap.scaled(size, QtCore.Qt.KeepAspectRatio,
                                    transformMode=QtCore.Qt.SmoothTransformation)

        # start painting the label from left upper corner
        point.setX((size.width() - scaled.width())/2)
        point.setY((size.height() - scaled.height())/2)
        painter.drawPixmap(point, scaled)

def main():
    app = QtGui.QApplication(sys.argv)
    tool = FigureDrawingTool()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
