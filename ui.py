from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import cv2
import sys
import os

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the project root to sys.path
sys.path.insert(0, PROJECT_ROOT)

# Now import the module
from src.person_tracking import PersonTracking


# Base directory setup for file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "..", "assets", "background.jpg")

button_style = """
    QPushButton {
        font-size: 18px;
        padding: 12px;
        border-radius: 8px;
        background-color: #2E86C1;
        color: white;
        font-weight: bold;
        transition: 0.3s;
    }
    QPushButton:hover {
        background-color: #1F618D;
        transform: scale(1.05);
    }
"""

dropdown_style = """
    QComboBox {
        background: white;
        border: 2px solid #2E86C1;
        padding: 8px;
        font-size: 16px;
        color: black;
        border-radius: 8px;
    }
"""

class ResultsViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tracking Results")
        self.setGeometry(300, 150, 900, 600)
        self.setStyleSheet("background-color: #2C3E50; color: white;")

        layout = QVBoxLayout()
        heading_label = QLabel("📂 Saved Tracking Results")
        heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading_label.setStyleSheet("font-size: 28px; font-weight: bold; padding-bottom: 20px;")
        layout.addWidget(heading_label)

        self.open_video_button = QPushButton("🎞 Open Saved Video")
        self.open_video_button.setStyleSheet(button_style)
        self.open_video_button.clicked.connect(self.open_saved_video)

        self.open_images_button = QPushButton("📸 View Saved Images")
        self.open_images_button.setStyleSheet(button_style)
        self.open_images_button.clicked.connect(self.open_saved_images)

        layout.addWidget(self.open_video_button)
        layout.addWidget(self.open_images_button)
        self.setLayout(layout)

    def open_saved_video(self):
        video_path = os.path.join(BASE_DIR, "..", "tracking_results", "tracked_output.mp4")
        if os.path.exists(video_path):
            os.startfile(video_path)
        else:
            QMessageBox.warning(self, "Error", "No saved tracking video found!")

    def open_saved_images(self):
        folder_path = os.path.abspath(os.path.join(BASE_DIR, "..", "tracking_results"))
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            QMessageBox.warning(self, "Error", "No saved tracking images found!")


class CameraThread(QThread):
    def __init__(self, person_tracker):
        super().__init__()
        self.person_tracker = person_tracker
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(0)

        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            QMessageBox.critical(None, "Error", "Failed to open camera!")
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            if self.person_tracker:
                frame = self.person_tracker.track_person(frame)

            cv2.imshow("Live Camera Tracking", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Person Tracking - Home")
        self.setGeometry(300, 150, 900, 600)

        if os.path.exists(BACKGROUND_IMAGE_PATH):
            self.setStyleSheet(f"background-image: url({BACKGROUND_IMAGE_PATH}); background-size: cover;")
        else:
            self.setStyleSheet("background-color: #2C3E50;")

        layout = QVBoxLayout()

        heading_label = QLabel("Advanced Person Tracking")
        heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading_label.setStyleSheet("font-size: 42px; font-weight: bold; color: white; padding-bottom: 30px;")
        layout.addWidget(heading_label)

        button_layout = QHBoxLayout()
        self.live_camera_button = QPushButton("🎥 Track in Live Camera")
        self.live_camera_button.setStyleSheet(button_style)
        self.live_camera_button.clicked.connect(self.open_live_tracking)

        self.recorded_video_button = QPushButton("📹 Track in Recorded Video")
        self.recorded_video_button.setStyleSheet(button_style)
        self.recorded_video_button.clicked.connect(self.open_video_tracking)

        self.view_results_button = QPushButton("📂 View Tracking Results")
        self.view_results_button.setStyleSheet(button_style)
        self.view_results_button.clicked.connect(self.open_results_viewer)

        button_layout.addWidget(self.live_camera_button)
        button_layout.addWidget(self.recorded_video_button)
        layout.addLayout(button_layout)
        layout.addWidget(self.view_results_button)

        self.setLayout(layout)

    def open_live_tracking(self):
        self.live_tracking_page = LiveTrackingPage()
        self.live_tracking_page.show()

    def open_video_tracking(self):
        self.video_tracking_page = VideoTrackingPage()
        self.video_tracking_page.show()

    def open_results_viewer(self):
        self.results_page = ResultsViewer()
        self.results_page.show()


class LiveTrackingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Track in Live Camera")
        self.setGeometry(300, 150, 900, 600)
        self.setStyleSheet("background-color: #34495E;")

        layout = QVBoxLayout()

        heading_label = QLabel("Track in Live Camera")
        heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(heading_label)

        self.person_tracker = PersonTracking()  # ✅ Always initialized

        self.track_button = QPushButton("🚀 Start Tracking")
        self.track_button.setStyleSheet(button_style)
        self.track_button.clicked.connect(self.start_live_tracking)

        layout.addWidget(self.track_button)
        self.setLayout(layout)

    def start_live_tracking(self):
        if hasattr(self, "camera_thread") and self.camera_thread.isRunning():
            QMessageBox.warning(self, "Warning", "Live tracking is already running!")
            return

        self.camera_thread = CameraThread(person_tracker=self.person_tracker)
        self.camera_thread.start()


class VideoTrackingPage(LiveTrackingPage):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Track in Recorded Video")
        self.track_button.clicked.disconnect()
        self.track_button.clicked.connect(self.start_video_tracking)

    def start_video_tracking(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Videos (*.mp4 *.avi)")
        if file_path:
            self.person_tracker.track_in_video(file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    home_page = HomePage()
    home_page.show()
    sys.exit(app.exec())
