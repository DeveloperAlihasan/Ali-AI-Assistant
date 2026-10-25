import os
import re
import time
import difflib
import subprocess
import webbrowser
import urllib.request
import urllib.parse
import ctypes
import pyautogui
import pyperclip

BN_TO_EN_MAP = {
    "স্কুল": "school", "এসএমএস": "sms", "ডট": ".", "এইচটিএমএল": "html",
    "সিএসএস": "css", "জাভাস্ক্রিপ্ট": "js", "পাইথন": "py", "ইনডেক্স": "index",
    "মেইন": "main", "অ্যাপ": "app", "প্রজেক্ট": "project", "ফোল্ডার": "",
    "ফাইল": "", "ওপেন": "", "খোলো": "", "করো": "", "চালু": "",
    "অ্যান্টিগ্রাভিটি": "", "ইন্টিগ্রাভিটি": "", "অ্যান্টিগ্রাভিটিতে": "", "ইন্টিগ্রাভিটিতে": "",
    "ভিএস": "", "কোডে": "", "কোড": "", "আলী": "", "সম্পা": "", "শম্পা": ""
}

def normalize_target_name(raw_query: str) -> str:
    q = raw_query.lower()
    for bn, en in BN_TO_EN_MAP.items():
        q = q.replace(bn, f" {en} ")
    q = re.sub(r"\s+\.\s+", ".", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q

def get_search_roots():
    user_home = os.path.expanduser("~")
    roots = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "OneDrive", "Desktop"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Downloads"),
        user_home,
        "D:\\",
        "E:\\",
        "C:\\Projects",
    ]
    return [r for r in roots if os.path.exists(r)]

def find_file_or_folder(raw_spoken_text: str, want_folder: bool = False) -> str:
    target = normalize_target_name(raw_spoken_text)
    if not target:
        return ""

    target_clean = re.sub(r"[^a-z0-9.]", "", target)
    best_match = ""
    best_score = 0.0

    for root in get_search_roots():
        root_depth = root.rstrip("\\/").count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            cur_depth = dirpath.count(os.sep) - root_depth
            if cur_depth > 3:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", ".venv", "venv", "__pycache__", "build", "dist", "AppData")]

            candidates = dirnames if want_folder else (filenames + dirnames)
            for item in candidates:
                item_lower = item.lower()
                item_clean = re.sub(r"[^a-z0-9.]", "", item_lower)
                full_path = os.path.join(dirpath, item)

                if target == item_lower or target_clean == item_clean:
                    return full_path

                if target_clean and target_clean in item_clean:
                    score = 0.92
                else:
                    score = difflib.SequenceMatcher(None, target_clean, item_clean).ratio()

                if score > best_score and score >= 0.60:
                    best_score = score
                    best_match = full_path

    return best_match

def open_in_antigravity_or_vscode(target_path: str) -> bool:
    local_app = os.environ.get("LOCALAPPDATA", "")
    possible_bins = [
        os.path.join(local_app, "Programs", "Antigravity", "Antigravity.exe"),
        os.path.join(local_app, "Programs", "cursor", "Cursor.exe"),
        os.path.join(local_app, "Programs", "Microsoft VS Code", "Code.exe"),
    ]
    for exe in possible_bins:
        if os.path.exists(exe):
            subprocess.Popen([exe, target_path])
            return True

    for cli in ["antigravity", "cursor", "code"]:
        try:
            res = subprocess.run(f'{cli} "{target_path}"', shell=True)
            if res.returncode == 0:
                return True
        except Exception:
            continue

    try:
        os.startfile(target_path)
        return True
    except Exception:
        return False

def open_specific_target(spoken_command: str) -> str:
    cmd_lower = spoken_command.lower()
    want_ide = any(w in cmd_lower for w in ["অ্যান্টিগ্রাভিটি", "ইন্টিগ্রাভিটি", "antigravity", "ভিএস কোড", "vscode", "প্রজেক্ট"])
    want_folder = any(w in cmd_lower for w in ["ফোল্ডার", "প্রজেক্ট", "folder", "project"]) or want_ide

    matched_path = find_file_or_folder(spoken_command, want_folder=want_folder)
    if not matched_path and want_folder:
        matched_path = find_file_or_folder(spoken_command, want_folder=False)

    if not matched_path:
        return "বস, ওই নামের ফাইল বা ফোল্ডারটি খুঁজে পাওয়া যায়নি।"

    base_name = os.path.basename(matched_path)
    if want_ide or os.path.isdir(matched_path):
        open_in_antigravity_or_vscode(matched_path)
        return f"জী বস, {base_name} প্রজেক্টটি অ্যান্টিগ্রাভিটিতে ওপেন করে দিয়েছি।"
    else:
        os.startfile(matched_path)
        return f"জী বস, {base_name} ফাইলটি ওপেন করা হয়েছে।"

def auto_play_youtube(query: str):
    if not query:
        webbrowser.open("https://www.youtube.com")
        return
    try:
        encoded = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
            if video_ids:
                webbrowser.open(f"https://www.youtube.com/watch?v={video_ids[0]}")
                return
    except Exception:
        pass
    webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")

def send_whatsapp_to_contact(contact_name: str, message: str):
    webbrowser.open("https://web.whatsapp.com")
    time.sleep(6)
    pyautogui.hotkey('ctrl', 'alt', '/')
    time.sleep(0.8)
    pyperclip.copy(contact_name)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.5)
    pyautogui.press('enter')
    time.sleep(1.0)
    pyperclip.copy(message)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.4)
    pyautogui.press('enter')

def trigger_whatsapp_call():
    webbrowser.open("https://web.whatsapp.com")
    time.sleep(4)
    pyautogui.hotkey('ctrl', 'shift', 'c')

def human_type(text: str):
    time.sleep(0.5)
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')

def lock_pc():
    ctypes.windll.user32.LockWorkStation()

def shutdown_pc():
    os.system("shutdown /s /f /t 5")
