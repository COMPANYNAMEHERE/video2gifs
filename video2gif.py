import sys
import os
import random
from PyQt5 import QtCore, QtGui, QtWidgets
from moviepy.editor import VideoFileClip, concatenate_videoclips
import threading

class VideoToGifConverter(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to GIF Converter")
        self.setGeometry(150, 150, 1000, 800)
        self.video_path = ""
        self.gifs = []
        self.selected_gif = None
        self.settings = QtCore.QSettings('config.ini', QtCore.QSettings.IniFormat)
        self.output_path = self.settings.value('output_path', os.path.join(os.getcwd(), 'output'))
        self.num_chunks = int(self.settings.value('num_chunks', 3))
        self.gif_duration = float(self.settings.value('gif_duration', 2))
        self.frame_rate = int(self.settings.value('frame_rate', 10))
        self.resolution = self.settings.value('resolution', '480p')
        self.initUI()

    def initUI(self):
        # Main widget
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setAlignment(QtCore.Qt.AlignTop)

        # Title
        title = QtWidgets.QLabel("Video to GIF Converter")
        title.setFont(QtGui.QFont("Arial", 24, QtGui.QFont.Bold))
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        # Video selection
        video_layout = QtWidgets.QHBoxLayout()
        self.load_button = QtWidgets.QPushButton("Load Video")
        self.load_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon))
        self.load_button.clicked.connect(self.load_video)
        self.video_label = QtWidgets.QLabel("No video loaded.")
        self.video_label.setWordWrap(True)
        video_layout.addWidget(self.load_button)
        video_layout.addWidget(self.video_label)
        main_layout.addLayout(video_layout)

        # Create GIFs button
        self.create_button = QtWidgets.QPushButton("Create GIFs")
        self.create_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowForward))
        self.create_button.clicked.connect(self.create_gifs)
        self.create_button.setFixedHeight(40)
        main_layout.addWidget(self.create_button)

        # GIF previews
        self.gif_group = QtWidgets.QGroupBox("GIF Previews")
        gif_layout = QtWidgets.QHBoxLayout()
        self.gif_labels = []
        self.radio_buttons = []
        for i in range(3):
            vbox = QtWidgets.QVBoxLayout()
            label = QtWidgets.QLabel(f"GIF {i+1}")
            label.setFixedSize(300, 300)
            label.setStyleSheet("border: 2px solid #ccc; border-radius: 10px;")
            label.setAlignment(QtCore.Qt.AlignCenter)
            self.gif_labels.append(label)

            radio = QtWidgets.QRadioButton("Select")
            self.radio_buttons.append(radio)

            vbox.addWidget(label)
            vbox.addWidget(radio, alignment=QtCore.Qt.AlignCenter)
            gif_layout.addLayout(vbox)
        self.gif_group.setLayout(gif_layout)
        main_layout.addWidget(self.gif_group)

        # Save button
        self.save_button = QtWidgets.QPushButton("Save Selected GIF")
        self.save_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton))
        self.save_button.clicked.connect(self.save_gif)
        self.save_button.setFixedHeight(40)
        main_layout.addWidget(self.save_button)

        # Settings button
        self.settings_button = QtWidgets.QPushButton("Settings")
        self.settings_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setFixedHeight(30)
        main_layout.addWidget(self.settings_button)

        # Status bar
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Ensure output directory exists
        os.makedirs(self.output_path, exist_ok=True)

    def load_video(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv)", options=options)
        if file_name:
            self.video_path = file_name
            self.video_label.setText(os.path.basename(self.video_path))
            self.status.showMessage("Video loaded successfully.", 5000)

    def create_gifs(self):
        if not self.video_path:
            QtWidgets.QMessageBox.warning(self, "No Video", "Please load a video first.")
            return
        self.create_button.setEnabled(False)
        self.status.showMessage("Generating GIFs...", 0)
        threading.Thread(target=self.generate_gifs).start()

    def generate_gifs(self):
        try:
            clip = VideoFileClip(self.video_path)
            duration = clip.duration
            if duration < self.gif_duration * self.num_chunks:
                self.status.showMessage("Video is too short for the specified GIF duration and number of chunks.", 5000)
                clip.close()
                self.create_button.setEnabled(True)
                return

            max_start = duration - self.gif_duration * self.num_chunks
            selected_starts = sorted(random.sample([random.uniform(0, max_start) for _ in range(self.num_chunks * 3)], 3 * self.num_chunks))

            self.gifs = []
            for i in range(3):
                clips = []
                for j in range(self.num_chunks):
                    start_time = selected_starts[i * self.num_chunks + j]
                    subclip = clip.subclip(start_time, start_time + self.gif_duration)
                    clips.append(subclip)
                final_clip = concatenate_videoclips(clips)
                gif_filename = f"thumbnail_{int(selected_starts[i * self.num_chunks])}_{i}.gif"
                gif_path = os.path.join(self.output_path, gif_filename)
                final_clip.write_gif(gif_path, fps=self.frame_rate, program='ffmpeg')
                self.gifs.append(gif_path)
                self.update_gif_preview(i, gif_path)
                final_clip.close()
            clip.close()
            self.status.showMessage("GIFs generated successfully.", 5000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            self.status.showMessage("Failed to generate GIFs.", 5000)
        finally:
            self.create_button.setEnabled(True)

    def update_gif_preview(self, index, gif_path):
        if index >= len(self.gif_labels):
            return
        movie = QtGui.QMovie(gif_path)
        self.gif_labels[index].setMovie(movie)
        movie.start()
        self.radio_buttons[index].setChecked(False)

    def save_gif(self):
        selected_index = None
        for i, radio in enumerate(self.radio_buttons):
            if radio.isChecked():
                selected_index = i
                break
        if selected_index is None:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a GIF to save.")
            return
        gif_path = self.gifs[selected_index]
        optimized_gif_name = self.generate_web_compatible_name(gif_path)
        save_path = os.path.join(self.output_path, optimized_gif_name)
        try:
            os.rename(gif_path, save_path)
            QtWidgets.QMessageBox.information(self, "GIF Saved", f"GIF saved to {save_path}.")
            self.status.showMessage(f"GIF saved as {optimized_gif_name}.", 5000)
            self.gif_labels[selected_index].clear()
            self.gifs[selected_index] = None
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save GIF: {str(e)}")
            self.status.showMessage("Failed to save GIF.", 5000)

    def generate_web_compatible_name(self, gif_path):
        base_name = os.path.basename(gif_path)
        name, _ = os.path.splitext(base_name)
        web_name = f"{name}.gif".lower().replace(' ', '_')
        return web_name

    def open_settings(self):
        dialog = SettingsDialog(
            output_path=self.output_path,
            num_chunks=self.num_chunks,
            gif_duration=self.gif_duration,
            frame_rate=self.frame_rate,
            resolution=self.resolution,
            parent=self)
        if dialog.exec_():
            self.output_path = dialog.output_path
            self.num_chunks = dialog.num_chunks
            self.gif_duration = dialog.gif_duration
            self.frame_rate = dialog.frame_rate
            self.resolution = dialog.resolution
            self.settings.setValue('output_path', self.output_path)
            self.settings.setValue('num_chunks', self.num_chunks)
            self.settings.setValue('gif_duration', self.gif_duration)
            self.settings.setValue('frame_rate', self.frame_rate)
            self.settings.setValue('resolution', self.resolution)
            os.makedirs(self.output_path, exist_ok=True)
            self.status.showMessage("Settings updated.", 5000)

    def closeEvent(self, event):
        # Clean up temporary GIFs if any
        for gif in self.gifs:
            if gif and os.path.exists(gif):
                try:
                    os.remove(gif)
                except:
                    pass
        event.accept()

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, output_path, num_chunks, gif_duration, frame_rate, resolution, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.output_path = output_path
        self.num_chunks = num_chunks
        self.gif_duration = gif_duration
        self.frame_rate = frame_rate
        self.resolution = resolution
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QFormLayout()

        # Output Path
        self.output_path_edit = QtWidgets.QLineEdit(self.output_path)
        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.clicked.connect(self.browse_output_path)
        output_layout = QtWidgets.QHBoxLayout()
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(browse_button)
        layout.addRow("Output Path:", output_layout)

        # Number of Video Chunks
        self.num_chunks_spin = QtWidgets.QSpinBox()
        self.num_chunks_spin.setMinimum(1)
        self.num_chunks_spin.setMaximum(10)
        self.num_chunks_spin.setValue(self.num_chunks)
        layout.addRow("Number of Video Chunks per GIF:", self.num_chunks_spin)

        # GIF Duration
        self.gif_duration_spin = QtWidgets.QDoubleSpinBox()
        self.gif_duration_spin.setMinimum(1.0)
        self.gif_duration_spin.setMaximum(10.0)
        self.gif_duration_spin.setSingleStep(0.5)
        self.gif_duration_spin.setValue(self.gif_duration)
        layout.addRow("GIF Duration (seconds per chunk):", self.gif_duration_spin)

        # Frame Rate
        self.frame_rate_spin = QtWidgets.QSpinBox()
        self.frame_rate_spin.setMinimum(5)
        self.frame_rate_spin.setMaximum(30)
        self.frame_rate_spin.setValue(self.frame_rate)
        layout.addRow("Frame Rate (FPS):", self.frame_rate_spin)

        # Resolution
        self.resolution_combo = QtWidgets.QComboBox()
        self.resolution_combo.addItems(["240p", "360p", "480p", "720p", "1080p"])
        index = self.resolution_combo.findText(self.resolution, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.resolution_combo.setCurrentIndex(index)
        layout.addRow("Resolution:", self.resolution_combo)

        # Buttons
        buttons = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.save_settings)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)

        self.setLayout(layout)

    def browse_output_path(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_path)
        if directory:
            self.output_path_edit.setText(directory)

    def save_settings(self):
        self.output_path = self.output_path_edit.text()
        self.num_chunks = self.num_chunks_spin.value()
        self.gif_duration = self.gif_duration_spin.value()
        self.frame_rate = self.frame_rate_spin.value()
        self.resolution = self.resolution_combo.currentText()
        os.makedirs(self.output_path, exist_ok=True)
        self.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = VideoToGifConverter()
    window.show()
    sys.exit(app.exec_())
