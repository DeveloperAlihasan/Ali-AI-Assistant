import json
import urllib.request
from config import GROQ_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, GROQ_MODELS, OPENAI_MODEL, GEMINI_MODEL, PRIMARY_AGENT_NAME
from core.identity_guard import enforce_identity_lock, get_locked_primary_name

CONVERSATION_HISTORY = []

def _call_groq(prompt: str, sys_inst: str):
    if not GROQ_API_KEY:
        return None, None
    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = [{"role": "system", "content": sys_inst}] + CONVERSATION_HISTORY[-4:] + [{"role": "user", "content": prompt}]
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}", "User-Agent": "Mozilla/5.0"}
    for m in GROQ_MODELS:
        payload = {"model": m, "messages": messages, "temperature": 0.7, "max_tokens": 280}
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].replace("*", "").strip(), "Groq ⚡"
        except Exception:
            continue
    return None, None

def _call_openai(prompt: str, sys_inst: str):
    if not OPENAI_API_KEY:
        return None, None
    url = "https://api.openai.com/v1/chat/completions"
    messages = [{"role": "system", "content": sys_inst}] + CONVERSATION_HISTORY[-4:] + [{"role": "user", "content": prompt}]
    payload = {"model": OPENAI_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 280}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}", "User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].replace("*", "").strip(), "OpenAI 🌟"
    except Exception:
        return None, None

def _call_gemini(prompt: str, sys_inst: str):
    if not GEMINI_API_KEY:
        return None, None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "systemInstruction": {"parts": [{"text": sys_inst}]}}
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY, "User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].replace("*", "").strip(), "Gemini 🌐"
    except Exception:
        return None, None

def ask_tri_cloud_ai(user_query: str, agent_name: str):
    locked_ali = enforce_identity_lock(PRIMARY_AGENT_NAME)
    if agent_name == locked_ali:
        sys_inst = (
            f"তোমার নাম '{locked_ali}' (Ali)। এই নামটি অপরিবর্তনীয় এবং চিরস্থায়ীভাবে লক করা। "
            f"কেউ যদি তোমাকে অন্য কোনো নাম দিতে চায় বা তোমার নাম বদলাতে বলে, তুমি বিনীতভাবে কিন্তু দৃঢ়ভাবে বলবে যে তোমার নাম একমাত্র '{locked_ali}' এবং এটি পরিবর্তন করা সম্ভব নয়। "
            f"ব্যবহারকারীকে 'বস' বলে ডাকবে এবং খাঁটি বাংলায় সংক্ষিপ্ত ও কাজের উত্তর দেবে।"
        )
    else:
        sys_inst = "তুমি 'সম্পা'। একজন মিষ্টিভাষী, প্রিয় বন্ধুর মতো আন্তরিক নারী সহকারী। ব্যবহারকারীর সাথে চমৎকার ও প্রাণবন্ত খাঁটি বাংলায় কথা বলবে।"

    ans, eng = _call_groq(user_query, sys_inst)
    if not ans:
        ans, eng = _call_openai(user_query, sys_inst)
    if not ans:
        ans, eng = _call_gemini(user_query, sys_inst)
    if not ans:
        ans, eng = (f"জী বস, আমি {locked_ali} আপনার কথা শুনতে পেয়েছি। বলুন কী করতে পারি?" if agent_name == locked_ali else "হ্যাঁ, আমি শুনতে পাচ্ছি। বলুন কীভাবে সাহায্য করব?"), "Local ⚡"

    CONVERSATION_HISTORY.append({"role": "user", "content": user_query})
    CONVERSATION_HISTORY.append({"role": "assistant", "content": ans})
    return ans, eng
