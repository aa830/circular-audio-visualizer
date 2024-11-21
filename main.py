import sys
import numpy as np
import sounddevice as sd
import soundfile as sf
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QPushButton
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush
from PyQt5.QtCore import QPointF
import math

# Custom widget representing the circle


class CircleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.volume = 0
        self.volume_history = []
        self.volume_history_size = 50

        # Define relative minimal and maximal sizes for your circle
        self.min_size = 400  # 0.2 * SCREEN_WIDTH
        self.max_size = 1344  # 0.7 * SCREEN_WIDTH

        # Initialize size_value with a default value
        self.size_value = self.min_size

        # Create a timer for updating the UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_circle)
        self.timer.start(16)  # Approx 60 FPS

        # Create a timer for rotation (angle update)
        self.rotation_timer = QTimer(self)
        self.rotation_timer.timeout.connect(self.rotate_button)
        self.rotation_timer.start(16)

        self.angle = 0  # Angle for rotation animation

        # Set up the file loading button
        self.file_button = QPushButton("Load Audio File", self)
        self.file_button.clicked.connect(self.load_audio_file)
        self.file_button.resize(200, 50)
        self.file_button.move(20, 20)

        self.audio_data = None
        self.audio_stream = None

    def paintEvent(self, event):
        """Override paint event to draw the rotating circle with segments."""
        if not hasattr(self, 'size_value'):
            self.size_value = self.min_size  # Initialize it with a default if not yet set

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Set the color of the circles and segments
        painter.setPen(QColor(0, 170, 255))  # Blue color from the example
        painter.setBrush(QBrush(QColor(0, 170, 255)))  # Filled segments

        # Define circle size
        circle_size = self.size_value
        radius = circle_size // 2

        # Draw the main circle centered
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)

        # Draw concentric circles
        for i in range(3):  # Example of three concentric circles
            offset = i * 10  # Adjust the gap between circles
            painter.drawEllipse(QPointF(0, 0), radius +
                                offset, radius + offset)

        # Draw segmented inner circle
        num_segments = 20  # Number of segments
        segment_width = 10  # Width of each segment
        segment_radius = radius - 20  # Adjust radius for segments

        for i in range(num_segments):
            angle = (360 / num_segments) * i
            painter.save()  # Save the painter state

            # Rotate to the angle of the segment
            painter.rotate(angle)
            # Draw a rectangle segment
            painter.drawRect(-segment_width // 2, -
                             segment_radius, segment_width, 30)

            painter.restore()  # Restore the painter state to the original

        # Draw outer circle
        outer_radius = radius + 30
        painter.drawEllipse(QPointF(0, 0), outer_radius, outer_radius)

    def update_circle(self):
        """Update the size of the circle based on volume level."""
        try:
            self.size_value = int(np.mean(self.volume_history))
        except:
            self.size_value = self.min_size

        # Ensure the size remains within the defined limits
        if self.size_value <= self.min_size:
            self.size_value = self.min_size
        elif self.size_value >= self.max_size:
            self.size_value = self.max_size

        # Trigger a redraw of the widget
        self.update()

    def update_volume(self, indata, frames, time, status):
        """Update the volume level based on incoming audio data."""
        volume_norm = np.linalg.norm(indata) * 100
        self.volume = volume_norm
        self.volume_history.append(volume_norm)

        # Keep the volume history within the defined size limit
        if len(self.volume_history) > self.volume_history_size:
            self.volume_history.pop(0)

    def start_listening(self):
        """Start listening to the audio stream and update the volume."""
        self.stream = sd.InputStream(callback=self.update_volume)
        self.stream.start()

    def play_audio_file(self):
        """Play the loaded audio file and update the volume in real time."""
        if self.audio_data is not None:
            self.audio_stream = sd.OutputStream(callback=self.audio_callback)
            self.audio_stream.start()

    def audio_callback(self, outdata, frames, time, status):
        """Callback to play audio and update volume visualization."""
        if len(self.audio_data) >= frames:
            data = self.audio_data[:frames]
            self.audio_data = self.audio_data[frames:]
        else:
            data = self.audio_data
            self.audio_data = np.array([])  # Clear data when done

        outdata[:] = data.reshape(-1, 2)  # Assuming stereo audio
        self.update_volume(data, frames, time, status)

    def load_audio_file(self):
        """Open a dialog to load an audio file and play it."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Open Audio File", "", "Audio Files (*.wav *.flac *.mp3)")

        if file_path:
            try:
                # Load the audio file
                self.audio_data, self.sample_rate = sf.read(
                    file_path, dtype='float32')
                # Use only the first 2 channels (stereo)
                self.audio_data = self.audio_data[:, :2]
                self.play_audio_file()
            except Exception as e:
                print(f"Error loading file: {e}")

    def rotate_button(self):
        """Rotate the circle by incrementing the angle."""
        self.angle += 2
        if self.angle >= 360:
            self.angle = 0
        self.update()

# Custom PyQt Application class


class MyPyQtApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.main_widget = CircleWidget()
        self.main_widget.setGeometry(0, 0, 1920, 1080)  # Fullscreen
        self.main_widget.showFullScreen()  # Set to fullscreen


if __name__ == '__main__':
    app = MyPyQtApp(sys.argv)
    sys.exit(app.exec_())
