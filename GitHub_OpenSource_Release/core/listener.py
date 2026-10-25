import os
import time
import ctypes
import speech_recognition as sr
from config import APP_DATA_DIR

LISTENING_ENABLED = True

def set_listening_enabled(state: bool):
    global LISTENING_ENABLED
    LISTENING_ENABLED = bool(state)

def is_listening_enabled() -> bool:
    return LISTENING_ENABLED

def record_wav_winmm(duration: float = 3.2) -> str:
    if not LISTENING_ENABLED:
        time.sleep(0.4)
        return ""

    wav_path = os.path.join(APP_DATA_DIR, "temp_live.wav")
    if os.path.exists(wav_path):
        try: os.remove(wav_path)
        except Exception: pass

    winmm = ctypes.windll.winmm
    winmm.mciSendStringW("close rec_live", None, 0, None)
    winmm.mciSendStringW("open new type waveaudio alias rec_live", None, 0, None)
    winmm.mciSendStringW("record rec_live", None, 0, None)
    time.sleep(duration)
    winmm.mciSendStringW("stop rec_live", None, 0, None)
    winmm.mciSendStringW(f'save rec_live "{wav_path}"', None, 0, None)
    winmm.mciSendStringW("close rec_live", None, 0, None)
    return wav_path

def listen_once(duration: float = 3.2) -> str:
    if not LISTENING_ENABLED:
        time.sleep(0.4)
        return ""

    wav_path = record_wav_winmm(duration=duration)
    if not wav_path or not os.path.exists(wav_path) or os.path.getsize(wav_path) < 500:
        return ""

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language="bn-BD")
        return text.strip()
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print(f"[STT Warning]: {e}")
        return ""
