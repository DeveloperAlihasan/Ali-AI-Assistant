import os
import time
import webbrowser
import pyautogui
from config import VOICE_ALI, VOICE_SHAMPA, PRIMARY_AGENT_NAME, SECONDARY_AGENT_NAME
from core.identity_guard import enforce_identity_lock, get_locked_primary_name, get_locked_secondary_name
from core.listener import listen_once, is_listening_enabled
from core.audio_engine import speak_agent_async, stop_speaking_now, IS_SPEAKING
from core.failover_brain import ask_tri_cloud_ai
from agents.os_operator import (
    open_specific_target, auto_play_youtube, send_whatsapp_to_contact,
    trigger_whatsapp_call, human_type, lock_pc, shutdown_pc
)
from agents.ide_autopilot import click_antigravity_buttons_once, start_ide_autopilot, stop_ide_autopilot

LOCKED_ALI = enforce_identity_lock(PRIMARY_AGENT_NAME)
LOCKED_SHAMPA = get_locked_secondary_name()

CURRENT_AGENT = LOCKED_ALI
CURRENT_VOICE = VOICE_ALI

def run_orchestrator_loop(update_ui_fn, pop_up_fn, hide_fn):
    """
    Main 24/7 background voice listener and task router.
    Continuously verifies that the primary agent name remains 'আলী'.
    """
    global CURRENT_AGENT, CURRENT_VOICE

    # Verify lock at startup
    enforce_identity_lock(LOCKED_ALI)

    time.sleep(0.8)
    welcome_msg = f"আসসালামু আলাইকুম বস! আমি {LOCKED_ALI}, আপনার কমান্ডের জন্য প্রস্তুত।"
    update_ui_fn(CURRENT_AGENT, welcome_msg, "SPEAKING", "READY ⚡")
    speak_agent_async(welcome_msg, CURRENT_VOICE)
    time.sleep(3.5)

    while True:
        try:
            # Continuous runtime identity guard: if someone attempts to mutate CURRENT_AGENT to an unknown name
            if CURRENT_AGENT not in (LOCKED_ALI, LOCKED_SHAMPA):
                CURRENT_AGENT = LOCKED_ALI
                CURRENT_VOICE = VOICE_ALI

            if not is_listening_enabled():
                time.sleep(0.5)
                continue

            if not IS_SPEAKING:
                update_ui_fn(CURRENT_AGENT, f"🎙️ মাইক্রোফোন সচল ({CURRENT_AGENT} শুনছে)... এখন কথা বলুন", "LISTENING", "")

            user_text = listen_once(duration=3.2)
            if not user_text or len(user_text.strip()) < 2:
                continue

            cmd = user_text.lower()

            # Block voice attempts to rename Ali
            if any(w in cmd for w in ["তোমার নাম পরিবর্তন", "তোমার নাম চেঞ্জ", "নতুন নাম", "change your name"]):
                reply = f"দুঃখিত বস, আমার নাম '{LOCKED_ALI}' চিরস্থায়ীভাবে লক করা। একমাত্র আমার নির্মাতা ছাড়া কেউ আমার নাম পরিবর্তন করতে পারবে না।"
                update_ui_fn(LOCKED_ALI, reply, "SPEAKING", "LOCKED 🔒")
                speak_agent_async(reply, VOICE_ALI)
                continue

            # 1. Instant Stop / Voice Barge-in
            if any(w in cmd for w in ["থামো", "চুপ", "দাঁড়াও", "stop", "ব্যাস", "সিস্টেম কিল", "জরুরি বন্ধ"]):
                stop_speaking_now()
                stop_ide_autopilot()
                update_ui_fn(CURRENT_AGENT, "🛑 জী বস, আমি থেমে গেছি। বলুন শুনছি...", "LISTENING", "")
                continue

            if IS_SPEAKING:
                stop_speaking_now()
                time.sleep(0.1)

            # 2. Persona Switching & Auto Pop-up
            has_ali = any(w in cmd for w in ["আলী", "আলি", "ali"])
            has_shampa = any(w in cmd for w in ["সম্পা", "শম্পা", "সমপা", "সম্পদ", "shampa", "shompa"])

            if has_ali:
                CURRENT_AGENT = LOCKED_ALI
                CURRENT_VOICE = VOICE_ALI
                pop_up_fn()
            elif has_shampa:
                CURRENT_AGENT = LOCKED_SHAMPA
                CURRENT_VOICE = VOICE_SHAMPA
                pop_up_fn()

            update_ui_fn(CURRENT_AGENT, f'🗣️ আপনি বলেছেন: "{user_text}"', "NODDING", "")

            # 3. Minimize / Hide to Background
            if any(w in cmd for w in ["লুকিয়ে যাও", "মিনিমাইজ", "হাইড হও", "ব্যাকগ্রাউন্ডে যাও"]):
                hide_fn()
                speak_agent_async("জী বস, আমি ব্যাকগ্রাউন্ডে যাচ্ছি। ডাকলেই হাজির হব।", CURRENT_VOICE)
                continue

            # 4. Complete Exit
            if any(w in cmd for w in ["সফটওয়্যার পুরোপুরি বন্ধ", "অ্যাপ বন্ধ করো", "এক্সিট করো"]):
                speak_agent_async("সফটওয়্যার বন্ধ করা হচ্ছে। আল্লাহ হাফেজ বস!", CURRENT_VOICE)
                time.sleep(2.5)
                os._exit(0)

            # 5. Unattended Antigravity Auto-Pilot Mode
            if any(w in cmd for w in ["অটো সাবমিট", "বাইরে যাচ্ছি", "অটো এক্সেপ্ট", "নিজে নিজে সাবমিট"]):
                post_act = "STANDBY"
                if "লক" in cmd or "lock" in cmd:
                    post_act = "LOCK"
                elif any(w in cmd for w in ["অফ", "বন্ধ", "শাটডাউন"]):
                    post_act = "SHUTDOWN"

                def on_auto_done(action_mode):
                    if action_mode == "LOCK":
                        speak_agent_async("প্রজেক্টের কাজ শেষ হয়েছে বস। কম্পিউটার লক করে দিচ্ছি।", CURRENT_VOICE)
                        time.sleep(3)
                        lock_pc()
                    elif action_mode == "SHUTDOWN":
                        speak_agent_async("প্রজেক্ট সম্পন্ন হয়েছে বস। কম্পিউটার শাটডাউন করছি।", CURRENT_VOICE)
                        time.sleep(3)
                        shutdown_pc()
                    else:
                        pop_up_fn()
                        update_ui_fn(CURRENT_AGENT, "✅ প্রজেক্টের কাজ সম্পন্ন হয়েছে বস!", "LISTENING", "")

                hide_fn()
                start_ide_autopilot(post_action=post_act, on_complete_callback=on_auto_done)
                speak_agent_async("জী বস, অটো-সাবমিট চালু করেছি। যতবার সাবমিট বা এক্সেপ্ট চাইবে আমি করে দেব।", CURRENT_VOICE)
                continue

            # 6. Single Antigravity / VS Code Submit, Accept, Allow, Click
            if any(w in cmd for w in ["সাবমিট", "submit", "এক্সেপ্ট", "accept", "এলাও", "allow", "অনুমতি", "ইয়েস", "yes", "কনফার্ম"]):
                hide_fn()
                time.sleep(0.25)
                click_antigravity_buttons_once()
                speak_agent_async("জী বস, সাবমিট ও এক্সেপ্ট করে দিয়েছি।", CURRENT_VOICE)
                continue

            if "ক্লিক করো" in cmd or "ক্লিক দাও" in cmd:
                hide_fn()
                time.sleep(0.2)
                pyautogui.click()
                speak_agent_async("ক্লিক করা হয়েছে।", CURRENT_VOICE)
                continue

            # 7. Specific File or Folder Opening
            if any(w in cmd for w in ["ফোল্ডার", "প্রজেক্ট", "ফাইল", ".html", ".py", "ডট", "স্কুল", "এসএমএস", " ইন্টিগ্রাভিটি", "অ্যান্টিগ্রাভিটি"]) or (
                any(w in cmd for w in ["ওপেন করো", "খোলো"]) and not any(w in cmd for w in ["ইউটিউব", "ফেসবুক", "মেসেঞ্জার", "হোয়াটসঅ্যাপ"])
            ):
                hide_fn()
                reply = open_specific_target(user_text)
                update_ui_fn(CURRENT_AGENT, reply, "SPEAKING", "")
                speak_agent_async(reply, CURRENT_VOICE)
                continue

            # 8. YouTube Direct Play
            if any(w in cmd for w in ["ইউটিউব", "গান", "ভিডিও"]):
                q = cmd
                for rem in ["আলী", "সম্পা", "শম্পা", "সম্পদ", "ইউটিউবে", "ইউটিউব", "চালাও", "বাজাও", "প্লে করো", "খোলো", "ওপেন করো"]:
                    q = q.replace(rem, "")
                q = q.strip()
                hide_fn()
                auto_play_youtube(q)
                reply = f"ইউটিউবে '{q}' প্লে করা হচ্ছে।" if q else "ইউটিউব ওপেন করা হলো।"
                speak_agent_async(reply, CURRENT_VOICE)
                continue

            # 9. Social Media & WhatsApp
            if any(w in cmd for w in ["মেসেজ পাঠাও", "মেসেজ দাও", "টেক্সট করো"]):
                clean_c = user_text
                for rem in ["আলী", "সম্পা", "শম্পা", "হোয়াটসঅ্যাপে", "মেসেজ", "পাঠাও", "দাও", "কে", "বলো"]:
                    clean_c = clean_c.replace(rem, "")
                parts = clean_c.strip().split()
                contact = parts[0] if parts else "Friend"
                msg = " ".join(parts[1:]) if len(parts) > 1 else "হ্যালো, কেমন আছেন?"
                hide_fn()
                send_whatsapp_to_contact(contact, msg)
                speak_agent_async(f"{contact}-কে মেসেজ পাঠানো হয়েছে।", CURRENT_VOICE)
                continue

            if any(w in cmd for w in ["কল করো", "কল দাও", "ফোন দাও"]):
                hide_fn()
                trigger_whatsapp_call()
                speak_agent_async("কল লাগানো হচ্ছে।", CURRENT_VOICE)
                continue

            if "ফেসবুক" in cmd or "facebook" in cmd:
                hide_fn()
                webbrowser.open("https://www.facebook.com")
                speak_agent_async("ফেসবুক ওপেন করা হলো।", CURRENT_VOICE)
                continue

            if "মেসেঞ্জার" in cmd or "messenger" in cmd:
                hide_fn()
                webbrowser.open("https://www.messenger.com")
                speak_agent_async("মেসেঞ্জার ওপেন করা হলো।", CURRENT_VOICE)
                continue

            if "হোয়াটসঅ্যাপ" in cmd or "whatsapp" in cmd:
                hide_fn()
                webbrowser.open("https://web.whatsapp.com")
                speak_agent_async("হোয়াটসঅ্যাপ ওপেন করা হলো।", CURRENT_VOICE)
                continue

            # 10. Notepad Typing
            if any(w in cmd for w in ["লেখো", "টাইপ করো", "নোটপ্যাডে"]):
                to_w = user_text
                for rem in ["আলী", "সম্পা", "শম্পা", "নোটপ্যাডে", "লেখো", "টাইপ করো"]:
                    to_w = to_w.replace(rem, "")
                hide_fn()
                os.system("start notepad")
                time.sleep(1.2)
                human_type(to_w.strip())
                speak_agent_async("টাইপ সম্পন্ন হয়েছে।", CURRENT_VOICE)
                continue

            # 11. Lock or Shutdown PC
            if "লক করো" in cmd or "কম্পিউটার লক" in cmd:
                speak_agent_async("কম্পিউটার লক করা হচ্ছে।", CURRENT_VOICE)
                time.sleep(1.5)
                lock_pc()
                continue

            if any(w in cmd for w in ["কম্পিউটার অফ", "পিসি অফ", "শাটডাউন", "কম্পিউটার বন্ধ"]):
                speak_agent_async("৫ সেকেন্ডের মধ্যে কম্পিউটার শাটডাউন হচ্ছে।", CURRENT_VOICE)
                shutdown_pc()
                continue

            # 12. Conversational AI Reply (Groq -> OpenAI -> Gemini)
            ai_reply, engine_name = ask_tri_cloud_ai(user_text, CURRENT_AGENT)
            update_ui_fn(CURRENT_AGENT, ai_reply, "SPEAKING", engine_name)
            speak_agent_async(ai_reply, CURRENT_VOICE)

        except Exception as err:
            print(f"[Orchestrator Loop Error]: {err}")
            time.sleep(1.0)
