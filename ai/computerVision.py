import cv2
import numpy as np
import mediapipe as mp
import math

# MediaPipe setup
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def calculate_angle(a, b, c):
    """Calculate angle between three points"""
    a = np.array(a)  # First point
    b = np.array(b)  # Middle point
    c = np.array(c)  # End point
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360-angle
        
    return angle

def analyze_pushup(landmarks):
    """Simple pushup analysis"""
    try:
        # Get coordinates
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                   landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        
        # Calculate arm angle
        angle = calculate_angle(shoulder, elbow, wrist)
        
        # Simple form check
        feedback = []
        score = 100
        
        if angle > 160:  # Arms too straight
            feedback.append("Bend your arms more")
            score -= 30
        elif angle < 70:  # Too low
            feedback.append("Don't go too low")
            score -= 20
        else:
            feedback.append("Good arm position!")
            
        return {
            'score': max(0, score),
            'feedback': feedback,
            'angle': round(angle, 1)
        }
    except:
        return {'score': 0, 'feedback': ['Cannot detect pose'], 'angle': 0}

def analyze_squat(landmarks):
    """Simple squat analysis"""
    try:
        # Get coordinates
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
               landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
        
        # Calculate knee angle
        angle = calculate_angle(hip, knee, ankle)
        
        # Simple form check
        feedback = []
        score = 100
        
        if angle > 160:  # Not squatting enough
            feedback.append("Squat deeper")
            score -= 40
        elif angle < 90:  # Too deep
            feedback.append("Don't go too deep")
            score -= 10
        else:
            feedback.append("Good squat depth!")
            
        return {
            'score': max(0, score),
            'feedback': feedback,
            'angle': round(angle, 1)
        }
    except:
        return {'score': 0, 'feedback': ['Cannot detect pose'], 'angle': 0}

def main():
    # Start camera
    cap = cv2.VideoCapture(1)
    
    # Exercise mode (press 'p' for pushup, 's' for squat)
    exercise_mode = 'pushup'
    
    print("AI Fitness Form Checker")
    print("Press 'p' for pushup mode, 's' for squat mode, 'q' to quit")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convert to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process pose
        results = pose.process(rgb)
        
        # Draw pose on frame
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # Analyze form
            if exercise_mode == 'pushup':
                analysis = analyze_pushup(results.pose_landmarks.landmark)
            else:
                analysis = analyze_squat(results.pose_landmarks.landmark)
            
            # Display feedback
            score = analysis['score']
            feedback = analysis['feedback']
            angle = analysis['angle']
            
            # Color based on score
            if score >= 80:
                color = (0, 255, 0)  # Green
            elif score >= 60:
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 0, 255)  # Red
            
            # Show info on screen
            cv2.putText(frame, f"Exercise: {exercise_mode.upper()}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Score: {score}/100", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, f"Angle: {angle}Â°", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show feedback
            for i, fb in enumerate(feedback):
                cv2.putText(frame, fb, (10, 120 + i*30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        else:
            cv2.putText(frame, "No pose detected", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Show frame
        cv2.imshow('AI Fitness Form Checker', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            exercise_mode = 'pushup'
            print("Switched to pushup mode")
        elif key == ord('s'):
            exercise_mode = 'squat'
            print("Switched to squat mode")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
