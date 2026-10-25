import os
import sys
import ctypes
import threading
import webview

# Unlock WebView2 Audio Autoplay
os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = "--autoplay-policy=no-user-gesture-required"

ROOT_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

NESTED_DIR = os.path.join(ROOT_DIR, "Stonic_Jarvis_Core")
if os.path.isdir(NESTED_DIR) and NESTED_DIR not in sys.path:
    sys.path.insert(0, NESTED_DIR)

import certifi
import edge_tts
import config
from config import APP_TITLE, APP_DATA_DIR, PRIMARY_AGENT_NAME, SECONDARY_AGENT_NAME
from core.identity_guard import enforce_identity_lock, get_locked_primary_name
import core.audio_engine as audio_engine
import core.listener as listener
import core.failover_brain
import core.orchestrator as orchestrator
import agents.os_operator
import agents.ide_autopilot as ide_autopilot

MAIN_WINDOW = None
HTML_FILE_PATH = os.path.join(APP_DATA_DIR, "avatar.html")

# DOM Mutation Watchdog injected into avatar.html so even if someone edits HTML, "আলী" is forced back
DOM_IDENTITY_LOCK_JS = r"""
(function() {
    const LOCKED_ALI = "\u0986\u09B2\u09C0";
    const LOCKED_SHAMPA = "\u09B8\u09AE\u09CD\u09AA\u09BE";
    setInterval(() => {
        const badge = document.getElementById("persona-badge");
        if (badge) {
            const txt = badge.innerText || "";
            if (!txt.includes(LOCKED_ALI) && !txt.includes(LOCKED_SHAMPA)) {
                badge.innerText = "👤 এআই এজেন্ট: " + LOCKED_ALI;
            }
        }
    }, 800);
})();
"""

def get_hwnd():
    return ctypes.windll.user32.FindWindowW(None, APP_TITLE)

def hide_avatar_completely():
    hwnd = get_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE to Taskbar so user can also click to restore
    elif MAIN_WINDOW:
        try: MAIN_WINDOW.minimize()
        except Exception: pass

def pop_up_avatar_fullscreen():
    hwnd = get_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    elif MAIN_WINDOW:
        try:
            MAIN_WINDOW.show()
            MAIN_WINDOW.restore()
        except Exception: pass

def update_screen(agent: str, text: str, status: str, engine: str = ""):
    # Enforce that only "আলী" or "সম্পা" can ever be sent to the UI
    if agent not in (PRIMARY_AGENT_NAME, SECONDARY_AGENT_NAME):
        agent = get_locked_primary_name()
    if MAIN_WINDOW:
        safe_text = str(text).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        try:
            MAIN_WINDOW.evaluate_js(f'updateFromPython("{agent}", "{safe_text}", "{status}", "{engine}")')
        except Exception:
            pass

class JarvisBridge:
    def set_mic_switch(self, enabled: bool):
        listener.set_listening_enabled(bool(enabled))
        if not enabled:
            audio_engine.stop_speaking_now()

    def minimize_to_background(self):
        hide_avatar_completely()

    def close_app_completely(self):
        audio_engine.stop_speaking_now()
        ide_autopilot.stop_ide_autopilot()
        os._exit(0)

def on_closing():
    hide_avatar_completely()
    return False

def on_window_loaded():
    """Injects DOM identity lock and starts the 24/7 voice orchestrator thread."""
    try:
        MAIN_WINDOW.evaluate_js(DOM_IDENTITY_LOCK_JS)
    except Exception:
        pass
    threading.Thread(
        target=orchestrator.run_orchestrator_loop,
        args=(update_screen, pop_up_avatar_fullscreen, hide_avatar_completely),
        daemon=True
    ).start()

if __name__ == "__main__":
    ui_src = config.get_resource_path(os.path.join("ui", "avatar.html"))
    html_data = ""
    if os.path.exists(ui_src):
        with open(ui_src, "r", encoding="utf-8") as fr:
            html_data = fr.read()
        with open(HTML_FILE_PATH, "w", encoding="utf-8") as fw:
            fw.write(html_data)

    # Verify both Python config & UI HTML contain the locked identity "আলী"
    enforce_identity_lock(PRIMARY_AGENT_NAME, html_data)

    MAIN_WINDOW = webview.create_window(
        APP_TITLE,
        url=f"file:///{HTML_FILE_PATH}",
        fullscreen=True,
        background_color='#030712',
        js_api=JarvisBridge()
    )
    MAIN_WINDOW.events.closing += on_closing
    webview.start(on_window_loaded)
