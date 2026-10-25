import os
import sys
from dotenv import load_dotenv
from core.identity_guard import get_locked_primary_name, get_locked_secondary_name, enforce_identity_lock

load_dotenv()
os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = "--autoplay-policy=no-user-gesture-required"

def get_resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# 🔒 LOCKED IDENTITY ("আলী" cannot be changed)
PRIMARY_AGENT_NAME = enforce_identity_lock(get_locked_primary_name())
SECONDARY_AGENT_NAME = get_locked_secondary_name()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

GROQ_MODELS = ["qwen/qwen3.8-27b", "llama-3.1-8b-instant"]
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-3.8-flash"

VOICE_ALI = "bn-BD-PradeepNeural"
VOICE_SHAMPA = "bn-BD-NabanitaNeural"

APP_TITLE = "STONIC_AI_HUMANOID_CORE"
APP_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "StonicJarvis")
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Jarvis_Outputs")
RELEASE_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Stonic_Jarvis_Release")

os.makedirs(APP_DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RELEASE_DIR, exist_ok=True)
