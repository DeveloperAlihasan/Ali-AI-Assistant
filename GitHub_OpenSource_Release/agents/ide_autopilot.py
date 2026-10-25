import os
import time
import threading
import subprocess
import pyautogui

AUTOPILOT_ACTIVE = False
POST_COMPLETION_ACTION = "STANDBY"

def click_antigravity_buttons_once() -> bool:
    ps_uia_script = r"""
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $cond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Window
    )
    $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)
    $clicked = $false
    foreach ($win in $windows) {
        $title = $win.Current.Name
        if ($title -match "Antigravity|Visual Studio Code|Cursor") {
            $btnCond = New-Object System.Windows.Automation.PropertyCondition(
                [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                [System.Windows.Automation.ControlType]::Button
            )
            $buttons = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCond)
            foreach ($btn in $buttons) {
                $bname = $btn.Current.Name
                if ($bname -match "^(Accept|Accept All|Submit|Allow|Run|Run Command|Approve|Continue|Keep|Yes)$|Accept|Submit|Allow|Run command") {
                    try {
                        $invoke = $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
                        $invoke.Invoke()
                        $clicked = $true
                    } catch {
                        $rect = $btn.Current.BoundingRectangle
                        if ($rect.Width -gt 0 -and $rect.Height -gt 0) {
                            Write-Output "COORD:$([int]($rect.Left + $rect.Width/2)),$([int]($rect.Top + $rect.Height/2))"
                            $clicked = $true
                        }
                    }
                }
            }
        }
    }
    if ($clicked) { Write-Output "SUCCESS" }
    """
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_uia_script],
            capture_output=True, text=True, timeout=4
        )
        out = res.stdout or ""
        for line in out.splitlines():
            if line.startswith("COORD:"):
                coords = line.replace("COORD:", "").split(",")
                x, y = int(coords[0]), int(coords[1])
                pyautogui.click(x, y)
                return True
        if "SUCCESS" in out:
            return True
    except Exception:
        pass

    pyautogui.hotkey('alt', 'enter')
    time.sleep(0.15)
    pyautogui.hotkey('ctrl', 'enter')
    time.sleep(0.15)
    pyautogui.press('enter')
    return True

def _autopilot_loop(watch_dir: str, on_complete_callback=None):
    global AUTOPILOT_ACTIVE, POST_COMPLETION_ACTION
    last_change_time = time.time()
    last_seen_mtime = 0.0

    while AUTOPILOT_ACTIVE:
        click_antigravity_buttons_once()

        latest_mtime = 0.0
        if watch_dir and os.path.exists(watch_dir):
            for dp, dn, fn in os.walk(watch_dir):
                dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__", "build", "dist")]
                for f in fn:
                    try:
                        mt = os.path.getmtime(os.path.join(dp, f))
                        if mt > latest_mtime:
                            latest_mtime = mt
                    except Exception:
                        pass

        if latest_mtime > last_seen_mtime:
            last_seen_mtime = latest_mtime
            last_change_time = time.time()

        if (time.time() - last_change_time) > 180:
            AUTOPILOT_ACTIVE = False
            if on_complete_callback:
                on_complete_callback(POST_COMPLETION_ACTION)
            break

        time.sleep(4.0)

def start_ide_autopilot(post_action: str = "STANDBY", watch_dir: str = "", on_complete_callback=None):
    global AUTOPILOT_ACTIVE, POST_COMPLETION_ACTION
    POST_COMPLETION_ACTION = post_action
    if not AUTOPILOT_ACTIVE:
        AUTOPILOT_ACTIVE = True
        threading.Thread(
            target=_autopilot_loop,
            args=(watch_dir or os.path.expanduser("~\\Desktop"), on_complete_callback),
            daemon=True
        ).start()

def stop_ide_autopilot():
    global AUTOPILOT_ACTIVE
    AUTOPILOT_ACTIVE = False
