import cv2
import time
import os
import threading
import subprocess
import numpy as np
import mediapipe as mp
from collections import deque
from PIL import Image, ImageDraw, ImageFont

import pyttsx3
import pygame

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


class SpeechThread:
    """Thread terpisah untuk TTS agar tidak mengeblok kamera."""
    def __init__(self):
        self.is_speaking = False
        self.lock = threading.Lock()

    def speak(self, text):
        with self.lock:
            if not self.is_speaking:
                self.is_speaking = True
                thread = threading.Thread(target=self._speak, args=(text,))
                thread.daemon = True
                thread.start()

    def _speak(self, text):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 170)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
        finally:
            with self.lock:
                self.is_speaking = False


class LocalVideoPlayer:
    """Mengekstrak audio dari video dan memutarnya dengan Pygame."""
    def __init__(self, video_path):
        self.video_path = video_path
        self.is_playing = False
        self.cap = None
        self.audio_path = None
        self._prepare_audio()

    def _prepare_audio(self):
        if not os.path.exists(self.video_path):
            return

        cache_path = os.path.splitext(self.video_path)[0] + "_audio.wav"

        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            self.audio_path = cache_path
            return
        elif os.path.exists(cache_path):
            os.remove(cache_path)

        try:
            cmd = ['ffmpeg', '-y', '-i', self.video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', cache_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                self.audio_path = cache_path
                return
        except Exception:
            pass

        if MOVIEPY_AVAILABLE:
            try:
                clip = VideoFileClip(self.video_path)
                if clip.audio is not None:
                    clip.audio.write_audiofile(cache_path, codec='pcm_s16le', fps=44100, logger=None)
                    clip.close()
                    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                        self.audio_path = cache_path
            except Exception:
                pass

    def start(self):
        if self.is_playing:
            return False
        if not os.path.exists(self.video_path):
            return False

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.cap = None
            return False

        self.is_playing = True

        if self.audio_path and os.path.exists(self.audio_path):
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                pygame.mixer.music.load(self.audio_path)
                pygame.mixer.music.play()
            except Exception:
                pass

        return True

    def get_frame(self, target_w, target_h):
        if not self.is_playing or self.cap is None:
            return None
        ret, frame = self.cap.read()
        if not ret:
            self.stop()
            return None
        frame = cv2.resize(frame, (target_w, target_h))
        return frame

    def stop(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.is_playing = False


# Inisialisasi Audio Engine
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
except Exception:
    pass

speech = SpeechThread()
video_player = LocalVideoPlayer(os.path.join("recordings", "IMG.MP4"))

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def fingers_up(hand_landmarks, image_width, image_height):
    lm = hand_landmarks.landmark

    def px(i):
        return (lm[i].x * image_width, lm[i].y * image_height)

    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    wrist = px(0)
    middle_mcp = px(9)
    scale = max(dist(wrist, middle_mcp), 1.0)

    result = [False] * 5

    finger_joints = {
        1: (8, 6, 5),    # index
        2: (12, 10, 9),  # middle
        3: (16, 14, 13), # ring
        4: (20, 18, 17), # pinky
    }

    for idx, (tip_i, pip_i, mcp_i) in finger_joints.items():
        tip, pip, mcp = px(tip_i), px(pip_i), px(mcp_i)
        d_tip = dist(tip, wrist)
        d_pip = dist(pip, wrist)
        d_mcp = dist(mcp, wrist)
        result[idx] = d_tip > d_pip and d_tip > d_mcp + (scale * 0.05)

    tip = px(4)
    mcp = px(2)
    pinky_mcp = px(17)
    d_tip_pm = dist(tip, pinky_mcp)
    d_mcp_pm = dist(mcp, pinky_mcp)
    result[0] = d_tip_pm > d_mcp_pm + (scale * 0.05)

    return result


def count_fingers(fingers):
    return sum(fingers)


GESTURES = {
    1: ("Sistem Information", "Sistem Information"),
    2: ("From the", "from the"),
    3: ("Aliya", "Aliya"),
    4: ("My name is", "my name is"),
    5: ("Hello", "hello"),
}


def detect_gesture(finger_count):
    return GESTURES.get(finger_count, ("", None))


class GestureStabilizer:
    def __init__(self, buffer_size=4, min_agree=3):
        self.buffer = deque(maxlen=buffer_size)
        self.min_agree = min_agree

    def add(self, finger_count):
        self.buffer.append(finger_count)

    def get_stable_count(self):
        if len(self.buffer) < self.buffer.maxlen:
            return None

        counts = {}
        for c in self.buffer:
            counts[c] = counts.get(c, 0) + 1
        value, freq = max(counts.items(), key=lambda item: item[1])

        if freq >= self.min_agree:
            return value
        return None


# FUNGSI RENDER TEKS
def draw_custom_text(img, text, position=None, font_size=45, color=(219, 114, 163), align_center_bottom=False):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    if align_center_bottom:
        img_w, img_h = img_pil.size
        x = (img_w - text_w) // 2
        y = img_h - text_h - 60
    else:
        x, y = position if position else (30, 40)

    for offset_x, offset_y in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        draw.text((x + offset_x, y + offset_y), text, font=font, fill=(0, 0, 0))

    draw.text((x, y), text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def apply_visual_effect(roi, effect_index):
    if effect_index == 0:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        processed = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        label = "Effect: thermal"
    elif effect_index == 1:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        processed = np.zeros_like(roi)
        processed[edges > 0] = [255, 0, 255]
        label = "Effect: neon"
    elif effect_index == 2:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        processed = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        label = "Effect: edges"
    elif effect_index == 3:
        processed = cv2.bitwise_not(roi)
        label = "Effect: invert"
    elif effect_index == 4:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + 60) % 180
        processed = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        label = "Effect: cyberpunk"
    else:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        label = "Effect: mono"

    return processed, label


def apply_dynamic_effect_box(frame, box_coords, effect_index):
    x1, y1, x2, y2 = box_coords
    h, w = frame.shape[:2]

    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    box_w, box_h = x2 - x1, y2 - y1

    if box_w > 80 and box_h > 80:
        roi = frame[y1:y2, x1:x2]
        processed_roi, label_text = apply_visual_effect(roi, effect_index)
        frame[y1:y2, x1:x2] = processed_roi

        cv2.rectangle(frame, (x1, y1), (x2, y2), (219, 114, 163), 2)
        frame = draw_custom_text(frame, label_text, position=(x1, y1 - 35), font_size=20, color=(219, 114, 163))
        return frame, True, (x1, y1, x2, y2)

    return frame, False, (0, 0, 0, 0)


def main():
    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("Kamera tidak bisa dibuka.")
        return

    cv2.namedWindow("Gesture Recognition", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Gesture Recognition", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    stabilizer = GestureStabilizer(buffer_size=4)
    last_spoken_gesture = -1
    last_said = 0
    cooldown = 1.2
    play_cooldown = 3.0
    last_played_end = 0

    # VARIABEL SCAN & ANIMASI
    scan_active = False
    scan_start_time = 0
    scan_duration = 3.0  # Durasi animasi scan dalam detik

    last_effect_change = 0
    current_effect_idx = 0
    total_effects = 6

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        model_complexity=0,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    ) as hands:

        print("Kamera siap!")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            try:
                win_rect = cv2.getWindowImageRect("Gesture Recognition")
                win_w, win_h = win_rect[2], win_rect[3]
            except Exception:
                win_w, win_h = 1280, 720

            if win_w <= 0 or win_h <= 0:
                win_w, win_h = 1280, 720

            frame = cv2.flip(frame, 1)

            if video_player.is_playing:
                vid_frame = video_player.get_frame(win_w, win_h)
                if vid_frame is not None:
                    cv2.imshow("Gesture Recognition", vid_frame)
                else:
                    last_played_end = time.time()
                    stabilizer.buffer.clear()
                    last_spoken_gesture = -1

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            frame = cv2.resize(frame, (win_w, win_h))
            h, w = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True

            gesture_text = ""
            frame_detected = False
            active_box = (0, 0, 0, 0)

            now = time.time()
            if now - last_effect_change >= 0.3:
                current_effect_idx = (current_effect_idx + 1) % total_effects
                last_effect_change = now

            # DETEKSI 2 TANGAN (DYNAMIC BOX)
            if results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2:
                hand1 = results.multi_hand_landmarks[0]
                hand2 = results.multi_hand_landmarks[1]

                pts = [
                    (int(hand1.landmark[8].x * w), int(hand1.landmark[8].y * h)),
                    (int(hand1.landmark[4].x * w), int(hand1.landmark[4].y * h)),
                    (int(hand2.landmark[8].x * w), int(hand2.landmark[8].y * h)),
                    (int(hand2.landmark[4].x * w), int(hand2.landmark[4].y * h))
                ]

                x_coords = [p[0] for p in pts]
                y_coords = [p[1] for p in pts]

                x1, x2 = min(x_coords), max(x_coords)
                y1, y2 = min(y_coords), max(y_coords)

                frame, frame_detected, active_box = apply_dynamic_effect_box(frame, (x1, y1, x2, y2), current_effect_idx)

            # SIKLUS SCANNING & TRIGGER VIDEO
            if frame_detected and (now - last_played_end > play_cooldown):
                if not scan_active:
                    scan_active = True
                    scan_start_time = now

                elapsed = now - scan_start_time
                bx1, by1, bx2, by2 = active_box
                box_h = by2 - by1

                if elapsed < scan_duration:
                    # ANIMASI GARIS SCANNING (Hijau)
                    progress = (elapsed / scan_duration)
                    scan_y = int(by1 + progress * box_h)
                    cv2.line(frame, (bx1, scan_y), (bx2, scan_y), (0, 255, 0), 4)

                    # Teks indikator SCANNING...
                    frame = draw_custom_text(frame, "SCANNING...", position=(bx1 + 10, by2 - 40), font_size=24, color=(0, 255, 0))
                else:
                    # SCAN SELESAI -> TAMPILKAN SUCCESS DAN MAIN/PLAY VIDEO
                    frame = draw_custom_text(frame, "SUCCESS", position=(bx1 + int((bx2 - bx1) * 0.2), by1 + int(box_h * 0.35)), font_size=55, color=(0, 255, 0))
                    scan_active = False
                    video_player.start()
            else:
                scan_active = False

            # DETEKSI 1 TANGAN (GESTURE REGULAR)
            if not scan_active and results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 1:
                hand_lms = results.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(
                    frame, hand_lms, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(186, 82, 43), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(219, 114, 163), thickness=2)
                )

                fingers = fingers_up(hand_lms, w, h)
                finger_count = count_fingers(fingers)

                stabilizer.add(finger_count)
                stable_count = stabilizer.get_stable_count()

                if stable_count is not None:
                    display_text, speech_text = detect_gesture(stable_count)

                    if (speech_text and
                            stable_count != last_spoken_gesture and
                            (now - last_said > cooldown) and
                            not speech.is_speaking):
                        
                        speech.speak(speech_text)
                        last_said = now
                        last_spoken_gesture = stable_count
                        gesture_text = display_text

                    elif stable_count == last_spoken_gesture:
                        gesture_text = display_text
            else:
                stabilizer.buffer.clear()
                if now - last_said > 2.0:
                    last_spoken_gesture = -1

            if gesture_text and not scan_active:
                frame = draw_custom_text(frame, gesture_text, font_size=52, color=(219, 114, 163), align_center_bottom=True)

            cv2.imshow("Gesture Recognition", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()