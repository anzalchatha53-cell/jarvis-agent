import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock
import threading
import os
import time
import json
import re
import requests
import subprocess
import urllib.parse
import datetime
import base64
import shutil

kivy.require('2.1.0')

# ==============================================================================
# JARVIS ENTERPRISE SUPREME AGENT CORE v50.0 (ADVANCED AUTONOMOUS ENGINE)
# ==============================================================================

AI_SCREENSHOT_DIR = "/sdcard/jarvis_enterprise_vision"

# Global Dynamic API Pool (Supports user addition via '+' API Manager popup)
API_POOL = [
    {
        "provider": "OpenRouter Qwen Vision",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
        "key": "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"
    },
    {
        "provider": "Groq Cloud LLM",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "openai/gpt-oss-120b",
        "key": "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"
    }
]

ACTIVE_API_INDEX = 0
SYSTEM_LOGS = []

AI_SYSTEM_PROMPT = (
    "You are Jarvis Enterprise, an ultra-advanced Autonomous Android Operating Agent with full root/Shizuku privileges. "
    "MANDATORY OPERATIONAL PROTOCOLS: "
    "1. Always respond in **Roman Urdu using English alphabets only** (e.g., 'Ji Boss, main screen scan kar raha hoon'). "
    "2. Analyze screen frames meticulously, deduce coordinates or package names, and emit strict JSON tool execution arrays. "
    "3. Format for tool invocation: `[{\"tool\": \"tool_name\", \"args\": {...}}]` "
    "4. Format when objective is completely fulfilled: `{\"status\": \"completed\", \"message\": \"Task mukamal ho gaya Boss!\"}` "
    "5. Supported Native Capabilities: tap_screen, swipe_screen, open_app, open_playstore_app, open_youtube_search, control_torch, wait_seconds, go_home, go_back, shell_exec."
)

CHAT_HISTORY = [{"role": "system", "content": AI_SYSTEM_PROMPT}]


# ==============================================================================
# LOW-LEVEL BRIDGE & ROOT/SHIZUKU EXECUTION LAYER
# ==============================================================================

def execute_shell_command(cmd):
    rish_path = "rish"
    full_cmd = f"RISH_APPLICATION_ID=com.termux {rish_path} -c '{cmd}'"
    try:
        res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=20)
        return res.stdout.strip() or res.stderr.strip(), res.returncode
    except Exception as ex:
        # Fallback to standard termux execution if shizuku is busy
        try:
            res_alt = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return res_alt.stdout.strip() or res_alt.stderr.strip(), res_alt.returncode
        except Exception as e:
            return str(e), -1


def ensure_vision_directory():
    if not os.path.exists(AI_SCREENSHOT_DIR):
        execute_shell_command(f"mkdir -p {AI_SCREENSHOT_DIR}")
        try:
            os.makedirs(AI_SCREENSHOT_DIR, exist_ok=True)
        except Exception:
            pass


def capture_screen_b64():
    try:
        ensure_vision_directory()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(AI_SCREENSHOT_DIR, f"shot_{ts}.png")
        
        execute_shell_command(f"screencap -p {path}")
        if not os.path.exists(path):
            fallback = "/sdcard/jarvis_temp_shot.png"
            execute_shell_command(f"screencap -p {fallback}")
            if os.path.exists(fallback):
                shutil.copy(fallback, path)

        if os.path.exists(path):
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            return encoded
    except Exception as err:
        print(f"Vision Capture Exception: {err}")
    return None


# ==============================================================================
# EXECUTABLE TOOLS REGISTRY
# ==============================================================================

def tap_screen(x, y, desc=""):
    execute_shell_command(f"input tap {int(x)} {int(y)}")
    return f"Tapped at coordinates ({x}, {y}) -> {desc}"

def swipe_screen(x1, y1, x2, y2, duration=300):
    execute_shell_command(f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration)}")
    return "Screen swipe executed successfully."

def open_app(app_name):
    query = str(app_name).lower().strip()
    registry_map = {
        "youtube": "com.google.android.youtube",
        "whatsapp": "com.whatsapp",
        "instagram": "com.instagram.android",
        "play store": "com.android.vending",
        "settings": "com.android.settings",
        "chrome": "com.android.chrome",
        "telegram": "org.telegram.messenger"
    }
    pkg = registry_map.get(query)
    if pkg:
        execute_shell_command(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
        return f"Launched app package: {pkg}"
    execute_shell_command(f"am start -n {query}/.MainActivity || am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER")
    return f"Attempted starting application: {app_name}"

def open_playstore_app(package_name):
    execute_shell_command(f"am start -a android.intent.action.VIEW -d 'market://details?id={package_name}'")
    return f"Opened Google PlayStore for package: {package_name}"

def open_youtube_search(query):
    encoded = urllib.parse.quote(str(query))
    execute_shell_command(f"am start -a android.intent.action.VIEW -d 'https://www.youtube.com/results?search_query={encoded}'")
    return f"Executed YouTube search query: {query}"

def control_torch(action="on"):
    act = str(action).lower().strip()
    if act in ["on", "true", "1"]:
        execute_shell_command("svc power torch on || cmd camera flashlight torch 1")
    else:
        execute_shell_command("svc power torch off || cmd camera flashlight torch 0")
    return f"Flashlight state updated to: {action}"

def wait_seconds(sec=3):
    time.sleep(float(sec))
    return f"Paused execution for {sec} seconds."

def go_home():
    execute_shell_command("input keyevent KEYCODE_HOME")
    return "Navigated to home screen."

def go_back():
    execute_shell_command("input keyevent KEYCODE_BACK")
    return "Performed system back action."

def shell_exec(command_str):
    out, code = execute_shell_command(command_str)
    return f"Shell Output (Code {code}): {out[:300]}"

TOOLS_REGISTRY = {
    "tap_screen": tap_screen,
    "swipe_screen": swipe_screen,
    "open_app": open_app,
    "open_playstore_app": open_playstore_app,
    "open_youtube_search": open_youtube_search,
    "control_torch": control_torch,
    "wait_seconds": wait_seconds,
    "go_home": go_home,
    "go_back": go_back,
    "shell_exec": shell_exec
}


# ==============================================================================
# MULTI-API FAILSAFE BRAIN ENGINE WITH AUTOMATIC ROTATION
# ==============================================================================

def query_ai_core(goal, b64_img):
    global ACTIVE_API_INDEX, CHAT_HISTORY
    
    packet = [
        {"type": "text", "text": f"Target Objective: {goal}\nReview screenshot frame and return next JSON actions or status completion."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
    ]
    CHAT_HISTORY.append({"role": "user", "content": packet})

    retries = len(API_POOL)
    for _ in range(retries):
        api = API_POOL[ACTIVE_API_INDEX]
        headers = {
            "Authorization": f"Bearer {api['key']}",
            "Content-Type": "application/json"
        }
        body = {
            "model": api["model"],
            "messages": CHAT_HISTORY,
            "temperature": 0.1
        }
        try:
            res = requests.post(api["url"], headers=headers, json=body, timeout=35)
            if res.status_code == 200:
                data = res.json()
                if 'choices' in data and len(data['choices']) > 0:
                    text_content = data['choices'][0]['message'].get('content')
                    if text_content:
                        CHAT_HISTORY.append({"role": "assistant", "content": text_content})
                        return text_content
            elif res.status_code in [429, 401, 503, 500]:
                # Automatically rotate to next API key/provider to prevent rate limit blocks!
                ACTIVE_API_INDEX = (ACTIVE_API_INDEX + 1) % len(API_POOL)
        except Exception:
            ACTIVE_API_INDEX = (ACTIVE_API_INDEX + 1) % len(API_POOL)

    return '{"status": "error", "message": "Saari APIs rate limit ya network error par hain. Nayi API add karein!"}'


# ==============================================================================
# FUTURISTIC MATERIAL UI & DYNAMIC API MANAGER (+) POPUP
# ==============================================================================

class AddApiPopup(Popup):
    def __init__(self, submit_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Add Custom API Key & Model"
        self.size_hint = (0.85, 0.65)
        
        layout = BoxLayout(orientation='vertical', padding=15, spacing=12)
        
        self.prov_input = TextInput(hint_text="Provider Name (e.g. OpenRouter / Groq / DeepSeek)", multiline=False)
        self.url_input = TextInput(hint_text="API Endpoint URL", multiline=False)
        self.model_input = TextInput(hint_text="Model ID String", multiline=False)
        self.key_input = TextInput(hint_text="Secret API Key (sk-... / gsk_...)", multiline=False)
        
        save_btn = Button(text="Save & Register API", size_hint=(1, 0.2), background_color=(0.1, 0.7, 0.4, 1))
        save_btn.bind(on_press=lambda x: submit_callback(
            self.prov_input.text, self.url_input.text, self.model_input.text, self.key_input.text, self
        ))
        
        layout.add_widget(self.prov_input)
        layout.add_widget(self.url_input)
        layout.add_widget(self.model_input)
        layout.add_widget(self.key_input)
        layout.add_widget(save_btn)
        
        self.content = layout


class JarvisEnterpriseApp(App):
    def build(self):
        self.title = "Jarvis Enterprise Supreme Agent"
        
        root = FloatLayout()
        
        # Main Futuristic Dashboard Container
        main_layout = BoxLayout(orientation='vertical', padding=12, spacing=10)
        
        # Top Header Bar with Title and '+' API Button
        header_box = BoxLayout(size_hint=(1, 0.08), spacing=10)
        title_lbl = Label(text="[b]JARVIS ENTERPRISE AGENT[/b]", markup=True, font_size=18, color=(0, 1, 0.9, 1))
        
        plus_btn = Button(text="+ API", size_hint=(0.25, 1), background_color=(0.85, 0.2, 0.2, 1))
        plus_btn.bind(on_press=self.open_api_manager)
        
        header_box.add_widget(title_lbl)
        header_box.add_widget(plus_btn)
        main_layout.add_widget(header_box)
        
        # Real-time System Console Output Terminal
        self.console = TextInput(
            text="[System]: Jarvis Enterprise v50.0 Online. Shizuku & Vision Bridges Active.\n[Info]: Aap '+' button daba kar nayi API keys add kar sakte hain taaki limit ka masla na ho.\n",
            readonly=True,
            background_color=(0.03, 0.04, 0.06, 1),
            foreground_color=(0.1, 0.9, 0.5, 1),
            font_size=13
        )
        main_layout.add_widget(self.console)
        
        # Command Input Field
        self.user_input = TextInput(
            text="",
            hint_text="Yahan command dein (jaise: YouTube par lofi songs chalao)",
            size_hint=(1, 0.1),
            multiline=False,
            background_color=(0.1, 0.12, 0.15, 1),
            foreground_color=(1, 1, 1, 1)
        )
        self.user_input.bind(on_text_validate=self.dispatch_command)
        main_layout.add_widget(self.user_input)
        
        # Autonomous Execution Button
        exec_btn = Button(
            text="START AUTONOMOUS TASK",
            size_hint=(1, 0.11),
            background_color=(0, 0.5, 0.9, 1)
        )
        exec_btn.bind(on_press=self.dispatch_command)
        main_layout.add_widget(exec_btn)
        
        root.add_widget(main_layout)
        return root

    def open_api_manager(self, instance):
        popup = AddApiPopup(self.register_new_api)
        popup.open()

    def register_new_api(self, prov, url, model, key, popup_ref):
        if prov and url and model and key:
            API_POOL.append({
                "provider": prov.strip(),
                "url": url.strip(),
                "model": model.strip(),
                "key": key.strip()
            })
            self.console.text += f"\n[Success]: Nayi API '{prov}' pool mein register ho gayi hai! Total APIs: {len(API_POOL)}"
            popup_ref.dismiss()
        else:
            self.console.text += f"\n[Error]: Saari fields bharna lazmi hain!"

    def dispatch_command(self, instance):
        cmd = self.user_input.text.strip()
        if cmd:
            self.console.text += f"\n[Boss Cmd] >>> {cmd}"
            self.user_input.text = ""
            threading.Thread(target=self.run_autonomous_loop, args=(cmd,)).start()

    def run_autonomous_loop(self, goal):
        self.console.text += f"\n[Agent Brain]: Autonomous loop shuru ho chuka hai..."
        max_steps = 15
        
        for step in range(1, max_steps + 1):
            b64_frame = capture_screen_b64()
            if not b64_frame:
                self.console.text += f"\n[Error]: Screen capture nahi ho saki!"
                break
                
            response_json_str = query_ai_core(goal, b64_frame)
            
            try:
                cleaned = re.sub(r'```(?:json)?', '', response_json_str).replace('```', '').strip()
                extracted = re.search(r'(\[.*?\]|\{.*?\})', cleaned, re.DOTALL)
                
                if extracted:
                    parsed = json.loads(extracted.group(1))
                    if isinstance(parsed, dict) and parsed.get("status") == "completed":
                        message = parsed.get("message", "Task successfully mukamal ho gaya!")
                        self.console.text += f"\n[Jarvis AI]: {message}"
                        break
                    
                    actions = parsed if isinstance(parsed, list) else [parsed]
                    for action in actions:
                        tool_name = action.get("tool")
                        args = action.get("args", {})
                        if tool_name in TOOLS_REGISTRY:
                            self.console.text += f"\n[Executing Tool]: {tool_name} (Args: {args})"
                            result_msg = TOOLS_REGISTRY[tool_name](**args)
                            self.console.text += f"\n[Result]: {result_msg}"
                            time.sleep(2.0)
            except Exception as loop_err:
                self.console.text += f"\n[Engine Exception]: {str(loop_err)}"
                break
            time.sleep(1.0)

if __name__ == '__main__':
    JarvisEnterpriseApp().run()
          
