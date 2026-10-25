import os
import time
import ctypes
import asyncio
import threading
import subprocess
import edge_tts
from config import APP_DATA_DIR, VOICE_ALI

IS_SPEAKING = False
STOP_REQUESTED = False
_AUDIO_LOCK = threading.Lock()

def stop_speaking_now():
    """Immediately stop any ongoing speech playback."""
    global STOP_REQUESTED, IS_SPEAKING
    STOP_REQUESTED = True
    IS_SPEAKING = False

async def _synthesize_edge_tts(text: str, voice: str, out_file: str):
    communicate = edge_tts.Communicate(text, voice, rate="+12%")
    await communicate.save(out_file)

def _play_with_powershell_wmp(mp3_path: str):
    """Guaranteed Windows Media Player OCX fallback if MCI fails on an audio driver."""
    global STOP_REQUESTED
    safe_path = mp3_path.replace("'", "''")
    ps_script = (
        f"$p = New-Object -ComObject WMPlayer.OCX; "
        f"$p.settings.volume = 100; "
        f"$p.URL = '{safe_path}'; "
        f"$p.controls.play(); "
        f"Start-Sleep -Milliseconds 400; "
        f"while ($p.playState -eq 3 -or $p.playState -eq 6) {{ Start-Sleep -Milliseconds 100 }}; "
        f"$p.close()"
    )
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    while proc.poll() is None:
        if STOP_REQUESTED:
            proc.terminate()
            break
        time.sleep(0.06)

def _tts_and_play_worker(text: str, voice: str, on_start=None, on_finish=None):
    global IS_SPEAKING, STOP_REQUESTED

    with _AUDIO_LOCK:
        STOP_REQUESTED = False
        IS_SPEAKING = True
        alias = f"jv_tts_{int(time.time() * 1000) % 100000}"
        mp3_path = os.path.join(APP_DATA_DIR, f"{alias}.mp3")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_synthesize_edge_tts(text, voice, mp3_path))
            loop.close()

            if STOP_REQUESTED or not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 100:
                IS_SPEAKING = False
                return

            if on_start:
                try: on_start()
                except Exception: pass

            winmm = ctypes.windll.winmm
            winmm.mciSendStringW(f'close {alias}', None, 0, None)
            err = winmm.mciSendStringW(f'open "{mp3_path}" type mpegvideo alias {alias}', None, 0, None)

            if err == 0:
                winmm.mciSendStringW(f'play {alias}', None, 0, None)
                time.sleep(0.35)

                len_buf = ctypes.create_unicode_buffer(64)
                winmm.mciSendStringW(f'status {alias} length', len_buf, 64, None)
                total_len = int(len_buf.value) if len_buf.value.isdigit() else 0

                pos_buf = ctypes.create_unicode_buffer(64)
                mode_buf = ctypes.create_unicode_buffer(64)
                start_t = time.time()
                max_wait = (total_len / 1000.0) + 1.5 if total_len > 0 else 20.0

                while (time.time() - start_t) < max_wait:
                    if STOP_REQUESTED:
                        winmm.mciSendStringW(f'stop {alias}', None, 0, None)
                        break
                    winmm.mciSendStringW(f'status {alias} position', pos_buf, 64, None)
                    cur_pos = int(pos_buf.value) if pos_buf.value.isdigit() else 0
                    if total_len > 0 and cur_pos >= total_len:
                        break
                    winmm.mciSendStringW(f'status {alias} mode', mode_buf, 64, None)
                    if mode_buf.value.lower() == 'stopped' and (time.time() - start_t) > 0.6:
                        break
                    time.sleep(0.05)

                winmm.mciSendStringW(f'close {alias}', None, 0, None)
            else:
                _play_with_powershell_wmp(mp3_path)

        except Exception as e:
            print(f"[Audio Error]: {e}")
        finally:
            IS_SPEAKING = False
            STOP_REQUESTED = False
            if on_finish:
                try: on_finish()
                except Exception: pass
            if os.path.exists(mp3_path):
                try: os.remove(mp3_path)
                except Exception: pass

def speak_agent_async(text: str, voice: str = VOICE_ALI, on_start=None, on_finish=None):
    if not text or not text.strip():
        return
    stop_speaking_now()
    threading.Thread(
        target=_tts_and_play_worker,
        args=(text.strip(), voice, on_start, on_finish),
        daemon=True
    ).start()
