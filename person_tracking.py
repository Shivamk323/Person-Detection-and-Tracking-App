import winsound
import threading
import face_recognition
from ultralytics import YOLO
import cv2
import numpy as np
import os
import time
from deep_sort_realtime.deepsort_tracker import DeepSort


class PersonTracking:
    def __init__(self, reference_image_paths=None):
        # Load YOLO model with GPU (if available)
        self.model = YOLO("yolov8n.pt")  
        self.model.to("cuda:0" if cv2.cuda.getCudaEnabledDeviceCount() > 0 else "cpu")  

        print("✅ YOLOv8 model loaded successfully!")

        self.tracker = DeepSort(max_age=30, n_init=3, max_iou_distance=0.3)

        self.known_face_encodings = []
        self.known_face_names = []
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_update = time.time()
        self.fps = 0

        self.last_beep_time = 0
        self.beep_interval = 1.0

        self.output_folder = "tracking_results"
        os.makedirs(self.output_folder, exist_ok=True)

        # Variables for smoothing bounding box
        self.prev_bbox = None  # Store previous bounding box coordinates
        self.smoothing_factor = 0.6  # Adjusted for better stability

        # ✅ Allow multiple reference images for better identification
        if reference_image_paths:
            for image_path in reference_image_paths:
                try:
                    print(f"🔍 Loading reference image: {image_path}")

                    if not os.path.exists(image_path):
                        print(f"❌ Error: Image file not found! ({image_path})")
                        continue

                    image = face_recognition.load_image_file(image_path)
                    encoding = face_recognition.face_encodings(image)

                    if encoding:
                        self.known_face_encodings.append(encoding[0])
                        self.known_face_names.append(f"Target Person {len(self.known_face_encodings)}")
                        print(f"✅ Face encoding successfully stored from: {image_path}")
                    else:
                        print(f"❌ No face detected in image: {image_path}. Try a clearer image.")
                except Exception as e:
                    print(f"❌ Error processing image {image_path}: {e}")

    def play_beep(self):
        """Plays beep sound asynchronously."""
        threading.Thread(target=lambda: winsound.Beep(1000, 500), daemon=True).start()

    def track_in_video(self, video_path):

        cv2.destroyAllWindows()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Error: Could not open video file {video_path}")
            return
        else:
            print(f"✅ Video file loaded: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        output_path = os.path.join(self.output_folder, "tracked_output.mp4")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("⚠️ End of video or frame not available. Exiting loop.")
                break  # Avoid blank frame errors

            frame = self.track_person(frame)
            out.write(frame)

            # ✅ Fix Screen Blipping Issue (Only update display every 5 frames)
            if frame_count % 5 == 0:  
                cv2.imshow("Recorded Video Tracking", frame)

            frame_count += 1

            # ✅ Ensure correct frame size before displaying
            if frame.shape[0] != height or frame.shape[1] != width:
                frame = cv2.resize(frame, (width, height))

            # ✅ Reduce CPU Usage by Adding a Small Delay (Prevents Blipping)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                print("❌ User pressed 'q'. Exiting tracking...")
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()
        print(f"✅ Tracking results saved in: {self.output_folder}")

    def track_person(self, frame):
        try:
            self.frame_count += 1
            height, width, _ = frame.shape


            # ✅ Skip frame processing to reduce CPU/GPU load
            if self.frame_count % 5 == 0:
                return frame  # Skip every other frame for performance boost

            # ✅ Run YOLO detection with optimized confidence
            results = self.model(frame, verbose=False, conf=0.5)
            detections = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    if class_id == 0:  # Detect only 'person'
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        detections.append(([x1, y1, x2, y2], box.conf[0].item(), "person"))

            tracked_objects = self.tracker.update_tracks(detections, frame=frame) if detections else []
            person_detected = False

            for track in tracked_objects:
                if not track.is_confirmed():
                    continue

                person_detected = True
                track_id = track.track_id
                x1, y1, x2, y2 = map(int, track.to_ltrb())

                # ✅ Ensure Bounding Box Stays Inside Frame
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(width - 1, x2), min(height - 1, y2)

                # ✅ Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # ✅ Play Beep Sound in a Separate Process
            if person_detected and (time.time() - self.last_beep_time >= self.beep_interval):
                print("🔊 Beep sound triggered!")  # Debugging
                self.play_beep()
                self.last_beep_time = time.time()

            # ✅ Refresh Screen Every 5 Frames to Reduce Blinking
            if self.frame_count % 5 == 0:
                cv2.imshow("Tracking", frame)
            return frame

        except Exception as e:
            print(f"❌ Error in track_person: {e}")
            return frame

