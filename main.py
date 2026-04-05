import cv2 #type: ignore
import mediapipe as mp #type: ignore
import time
import numpy as np #type: ignore

# ------------------ SETUP ------------------

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    cap = cv2.VideoCapture(1)

# Eye landmarks
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

NOSE_TIP = 1

# ------------------ FUNCTIONS ------------------

def calculate_ear(eye_points, landmarks, w, h):
    coords = []

    for point in eye_points:
        x = int(landmarks[point].x * w)
        y = int(landmarks[point].y * h)
        coords.append((x, y))

    coords = np.array(coords)

    A = np.linalg.norm(coords[1] - coords[5])
    B = np.linalg.norm(coords[2] - coords[4])
    C = np.linalg.norm(coords[0] - coords[3])

    ear = (A + B) / (2.0 * C)
    return ear

# ------------------ VARIABLES ------------------

prev_time = 0
blink_counter = 0
stress_level = "LOW"

# ------------------ MAIN LOOP ------------------

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    attention = "HIGH"
    confidence_score = 100

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:

            mp_drawing.draw_landmarks(
                frame,
                face_landmarks,
                mp_face_mesh.FACEMESH_CONTOURS
            )

            landmarks = face_landmarks.landmark

            # ----------- EAR (Blink Detection) -----------
            left_ear = calculate_ear(LEFT_EYE, landmarks, w, h)
            right_ear = calculate_ear(RIGHT_EYE, landmarks, w, h)
            ear = (left_ear + right_ear) / 2.0

            EAR_THRESHOLD = 0.25

            if ear < EAR_THRESHOLD:
                blink_counter += 1
                cv2.putText(frame, "Blink", (30, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # ----------- ATTENTION DETECTION -----------
            nose = landmarks[NOSE_TIP]
            nose_x = int(nose.x * w)
            nose_y = int(nose.y * h)

            center_x = w // 2
            center_y = h // 2

            if abs(nose_x - center_x) > 100 or nose_y > center_y + 50:
                attention = "LOW"

            # ----------- STRESS DETECTION -----------
            if blink_counter > 15:
                stress_level = "HIGH"
            else:
                stress_level = "LOW"

            # ----------- CONFIDENCE SCORE -----------
            confidence_score = 100

            if attention == "LOW":
                confidence_score -= 30

            if stress_level == "HIGH":
                confidence_score -= 20

            confidence_score = max(confidence_score, 0)

            # ----------- DISPLAY TEXT -----------

            cv2.putText(frame, f"EAR: {ear:.2f}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            cv2.putText(frame, f"Attention: {attention}", (30, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 0) if attention == "HIGH" else (0, 0, 255), 2)

            cv2.putText(frame, f"Stress: {stress_level}", (30, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 0) if stress_level == "LOW" else (0, 0, 255), 2)

            cv2.putText(frame, f"Confidence: {confidence_score}%", (30, 170),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2)

    # ----------- FPS -----------

    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) != 0 else 0
    prev_time = curr_time

    cv2.putText(frame, f"FPS: {int(fps)}", (30, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # ----------- SHOW -----------

    cv2.imshow("AI Behavior Analyzer", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()