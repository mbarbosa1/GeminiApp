import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Load model path
model_path = "pose_landmarker_lite.task"  # Must be in same folder as this script

# Set up landmarker options
BaseOptions = mp.tasks.BaseOptions
VisionRunningMode = mp.tasks.vision.RunningMode
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO
)

# Define pose connections for drawing
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),  # Face
    (0, 4), (4, 5), (5, 6), (6, 8),  # Face
    (9, 10),  # Mouth
    (11, 12),  # Shoulders
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),  # Left arm
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),  # Right arm
    (11, 23), (12, 24),  # Torso
    (23, 24),  # Hips
    (23, 25), (25, 27), (27, 29), (27, 31),  # Left leg
    (24, 26), (26, 28), (28, 30), (28, 32),  # Right leg
]

# Open webcam
cap = cv2.VideoCapture(0)

def draw_pose_landmarks(image, landmarks):
    """Draw pose landmarks and connections manually"""
    h, w = image.shape[:2]
    
    # Draw connections
    for connection in POSE_CONNECTIONS:
        start_idx, end_idx = connection
        if start_idx < len(landmarks) and end_idx < len(landmarks):
            start_point = (int(landmarks[start_idx].x * w), int(landmarks[start_idx].y * h))
            end_point = (int(landmarks[end_idx].x * w), int(landmarks[end_idx].y * h))
            cv2.line(image, start_point, end_point, (0, 255, 0), 2)
    
    # Draw landmarks
    for landmark in landmarks:
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        cv2.circle(image, (x, y), 4, (0, 0, 255), -1)

# Initialize landmarker
with PoseLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Convert to RGB and wrap in MediaPipe Image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Use video timestamp for tracking
        timestamp = int(cap.get(cv2.CAP_PROP_POS_MSEC))
        result = landmarker.detect_for_video(mp_image, timestamp)

        # Draw landmarks
        annotated_frame = frame.copy()
        if result.pose_landmarks:
            for landmarks in result.pose_landmarks:
                draw_pose_landmarks(annotated_frame, landmarks)

        # Show the result
        cv2.imshow("Pose Detection", annotated_frame)

        # Exit on ESC
        if cv2.waitKey(1) & 0xFF == 27:
            break

# Cleanup
cap.release()
cv2.destroyAllWindows()