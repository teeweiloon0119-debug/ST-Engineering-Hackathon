import ctypes
import math
import random
import time
from typing import List, Optional, Union

# Own user32 instance: argtypes set by other modules in the same process
# (e.g. financial_report.py) must not change how these calls behave.
user32 = ctypes.WinDLL("user32")

# [INTEGRATION] No debug log file on disk any more. Messages go to print(),
# which the orchestrator silences unless DEBUG is switched on.
def log_debug(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] [WebTasks] {msg}")

# ---------------------------------------------------------------------------
# WIN32 STRUCTURES & CONSTANTS
# ---------------------------------------------------------------------------
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_ESCAPE = 0x1B
VK_LWIN = 0x5B
VK_R = 0x52
VK_L = 0x4C
VK_T = 0x54

SW_MAXIMIZE = 3
WM_CLOSE = 0x0010

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

ADJACENT_KEYS = {
    'a': 's', 'b': 'v', 'c': 'x', 'd': 's', 'e': 'w', 'f': 'd',
    'g': 'f', 'h': 'g', 'i': 'u', 'j': 'h', 'k': 'j', 'l': 'k',
    'm': 'n', 'n': 'b', 'o': 'i', 'p': 'o', 'q': 'w', 'r': 'e',
    's': 'a', 't': 'r', 'u': 'y', 'v': 'c', 'w': 'q', 'x': 'z',
    'y': 't', 'z': 'x'
}

# ---------------------------------------------------------------------------
# DOMAIN POOLS & SITE CLASSIFICATIONS
# ---------------------------------------------------------------------------
HARDWARE_SITES = [
    "https://www.apple.com",
    "https://www.amazon.com",
    "https://www.dell.com",
    "https://www.samsung.com",
    "https://www.asus.com",
    "https://www.cnet.com"
]

MARKET_SITES = [
    "https://www.coinmarketcap.com",
    "https://coingecko.com",
    "https://www.coinbase.com",
    "https://apnews.com",
    "https://www.binance.com"
]

# Domains that have long-form text where humans scroll deeper
LONG_CONTENT_DOMAINS = [
    "apnews.com",
    "cnet.com",
    "arstechnica.com"
]

# ---------------------------------------------------------------------------
# SAFETY & ENTROPY TIMING ROUTINES (Workshop 2: Cv > 0.4)
# ---------------------------------------------------------------------------
def release_all_modifiers():
    for vk in [VK_MENU, VK_CONTROL, VK_SHIFT, VK_LWIN]:
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def check_emergency_stop():
    if (user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) and (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000):
        release_all_modifiers()
        log_debug("Emergency stop triggered: Shift + ESC.")
        raise SystemExit("Emergency abort: Shift + ESC pressed.")

def human_delay(min_s: float = 0.8, max_s: float = 2.2, reading_prob: float = 0.15):
    """
    Log-normal timing generator with simulated cognitive hesitations.
    Guarantees non-uniform intervals to pass Process Monitor timeline checks.
    """
    check_emergency_stop()
    if random.random() < reading_prob:
        duration = random.uniform(2.5, 4.5)
    else:
        # Log-normal distribution mapped into [min_s, max_s]
        raw = random.lognormvariate(0.0, 0.35)
        duration = min_s + (raw / 2.0) * (max_s - min_s)
        duration = max(min_s, min(duration, max_s))
    
    t0 = time.time()
    while time.time() - t0 < duration:
        check_emergency_stop()
        time.sleep(0.04)

def micro_delay():
    check_emergency_stop()
    time.sleep(random.uniform(0.08, 0.20))

def get_mouse_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

# ---------------------------------------------------------------------------
# KINEMATIC MOUSE SIMULATION (Jolt, Bézier Path, Speed Profile)
# ---------------------------------------------------------------------------
def human_hand_touch_jolt():
    """Simulates physical hand displacement when touching the mouse."""
    cx, cy = get_mouse_pos()
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)
    for _ in range(random.randint(4, 6)):
        check_emergency_stop()
        jx = max(5, min(screen_w - 5, cx + random.randint(-22, 22)))
        jy = max(5, min(screen_h - 5, cy + random.randint(-22, 22)))
        user32.SetCursorPos(jx, jy)
        time.sleep(random.uniform(0.014, 0.024))
    time.sleep(random.uniform(0.05, 0.10))

def human_mouse_move(target_x: int, target_y: int, trigger_jolt: bool = True):
    """
    Cubic Bézier trajectory with dynamic acceleration.
    Yields 15-24ms per step to keep VM CPU usage < 5% in Proxmox.
    """
    if trigger_jolt:
        human_hand_touch_jolt()

    start_x, start_y = get_mouse_pos()
    dist = math.hypot(target_x - start_x, target_y - start_y)
    steps = max(16, min(32, int(dist / 28)))

    dx = target_x - start_x
    dy = target_y - start_y
    perp_x, perp_y = -dy, dx
    norm = math.hypot(perp_x, perp_y) or 1.0
    perp_x /= norm
    perp_y /= norm

    arc_scale = min(120.0, max(20.0, dist * random.uniform(0.12, 0.28)))
    side = random.choice([-1.0, 1.0])

    cp1_x = start_x + dx * 0.28 + perp_x * arc_scale * side + random.randint(-10, 10)
    cp1_y = start_y + dy * 0.28 + perp_y * arc_scale * side + random.randint(-10, 10)
    cp2_x = start_x + dx * 0.72 + perp_x * (arc_scale * 0.6) * side + random.randint(-10, 10)
    cp2_y = start_y + dy * 0.72 + perp_y * (arc_scale * 0.6) * side + random.randint(-10, 10)

    for i in range(1, steps + 1):
        check_emergency_stop()
        raw_t = i / float(steps)
        # Smoothstep S-curve for realistic acceleration
        t = raw_t * raw_t * (3.0 - 2.0 * raw_t)
        u = 1.0 - t

        bx = (u**3) * start_x + 3 * (u**2) * t * cp1_x + 3 * u * (t**2) * cp2_x + (t**3) * target_x
        by = (u**3) * start_y + 3 * (u**2) * t * cp1_y + 3 * u * (t**2) * cp2_y + (t**3) * target_y
        user32.SetCursorPos(int(bx), int(by))

        # Yield scheduler to keep CPU < 100%
        if 0.20 < raw_t < 0.75:
            time.sleep(random.uniform(0.012, 0.018))
        else:
            time.sleep(random.uniform(0.018, 0.026))

    # Pre-destination hovering
    for _ in range(random.randint(2, 4)):
        check_emergency_stop()
        user32.SetCursorPos(target_x + random.randint(-6, 6), target_y + random.randint(-5, 5))
        time.sleep(random.uniform(0.04, 0.07))

    user32.SetCursorPos(target_x, target_y)
    time.sleep(random.uniform(0.04, 0.08))

def human_hover(target_x: int, target_y: int, hover_s: float = 0.8, trigger_jolt: bool = True):
    human_mouse_move(target_x, target_y, trigger_jolt=trigger_jolt)
    t0 = time.time()
    while time.time() - t0 < hover_s:
        check_emergency_stop()
        user32.SetCursorPos(target_x + random.randint(-2, 2), target_y + random.randint(-2, 2))
        time.sleep(random.uniform(0.14, 0.24))

def human_click(target_x: int, target_y: int, trigger_jolt: bool = True):
    human_mouse_move(target_x, target_y, trigger_jolt=trigger_jolt)
    time.sleep(random.uniform(0.07, 0.14))
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(random.uniform(0.06, 0.12))
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    micro_delay()

def human_scroll(ticks: int = -3):
    direction = 1 if ticks > 0 else -1
    for _ in range(abs(ticks)):
        check_emergency_stop()
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, direction * 120, 0)
        time.sleep(random.uniform(0.08, 0.16))

# ---------------------------------------------------------------------------
# KEYBOARD SIMULATION WITH TYPING RHYTHM
# ---------------------------------------------------------------------------
def press_key(vk_code: int):
    check_emergency_stop()
    user32.keybd_event(vk_code, 0, 0, 0)
    micro_delay()
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

def send_char(char: str):
    vk = user32.VkKeyScanW(ord(char))
    vk_code = vk & 0xFF
    shift_state = (vk >> 8) & 0xFF
    if shift_state & 1:
        user32.keybd_event(VK_SHIFT, 0, 0, 0)
        time.sleep(0.02)
    user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(random.uniform(0.02, 0.04))
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
    if shift_state & 1:
        time.sleep(0.02)
        user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)

def type_text_human(text: str, typo_rate: float = 0.04):
    for char in text:
        check_emergency_stop()
        low = char.lower()
        if low in ADJACENT_KEYS and random.random() < typo_rate:
            wrong = ADJACENT_KEYS[low].upper() if char.isupper() else ADJACENT_KEYS[low]
            send_char(wrong)
            time.sleep(random.uniform(0.16, 0.30))
            press_key(VK_BACK)
            time.sleep(random.uniform(0.10, 0.18))
        send_char(char)
        # Fast keystrokes with natural chunking pauses at word boundaries
        time.sleep(random.uniform(0.06, 0.16))
        if char in ['.', '/']:
            time.sleep(random.uniform(0.14, 0.24))

# ---------------------------------------------------------------------------
# WINDOW MANAGEMENT & SSL DETECTION
# ---------------------------------------------------------------------------
def get_chrome_hwnd():
    return user32.FindWindowW("Chrome_WidgetWin_1", None)

def get_window_title(hwnd) -> str:
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value

def is_ssl_error_page(hwnd, url: str) -> bool:
    title = get_window_title(hwnd)
    log_debug(f"Title for {url}: '{title}'")
    t_low = title.lower()
    for kw in ["privacy error", "security error", "isn't private", "not private", "untrusted", "certificate"]:
        if kw in t_low:
            return True
    hostname = url.replace("https://", "").replace("http://", "").split("/")[0].lower()
    if t_low.startswith(hostname) or t_low.startswith("https://"):
        return True
    return False

def bypass_ssl_4_tabs():
    log_debug("SSL interstitial detected. Running 4-Tab bypass...")
    human_delay(1.0, 1.8, reading_prob=0.0)
    for _ in range(4):
        press_key(VK_TAB)
        time.sleep(random.uniform(0.18, 0.32))
    human_delay(0.4, 0.8, reading_prob=0.0)
    press_key(VK_RETURN)

    human_delay(0.8, 1.4, reading_prob=0.0)
    human_scroll(ticks=-2)
    human_delay(0.5, 1.0, reading_prob=0.0)
    press_key(VK_TAB)
    human_delay(0.3, 0.7, reading_prob=0.0)
    press_key(VK_RETURN)

def close_chrome_with_mouse():
    """
    Accurately closes Chrome using the mouse without coordinate clamping bugs.
    Targets top-right [X] directly, verifies closure, and falls back to WM_CLOSE.
    """
    hwnd = get_chrome_hwnd()
    if not hwnd or not user32.IsWindowVisible(hwnd):
        return

    user32.SetForegroundWindow(hwnd)
    user32.ShowWindowAsync(hwnd, SW_MAXIMIZE)
    time.sleep(0.3)

    screen_w = user32.GetSystemMetrics(0)
    # The [X] close button on a maximized window is anchored at top-right
    close_x = screen_w - 15
    close_y = 12

    log_debug(f"Closing Chrome with mouse click at ({close_x}, {close_y})")
    human_click(close_x, close_y, trigger_jolt=True)
    human_delay(0.6, 0.8, reading_prob=0.0)

    # Deterministic fallback: ensure window is closed
    if user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
        log_debug("Fallback: Dispatching WM_CLOSE to terminate Chrome.")
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        time.sleep(0.5)

# ---------------------------------------------------------------------------
# CORE GENERALIZED BROWSING SESSION
# ---------------------------------------------------------------------------
def execute_web_session(
    target_urls: List[str],
    session_name: str,
    close_when_done: bool = True
):
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)

    try:
        log_debug(f"Starting {session_name} session with URLs: {target_urls}")
        human_delay(0.8, 1.4, reading_prob=0.0)

        # Check if Chrome is already running
        hwnd = get_chrome_hwnd()
        chrome_already_open = bool(hwnd and user32.IsWindowVisible(hwnd))

        if not chrome_already_open:
            # Launch Chrome via Run dialog (ParentImage = explorer.exe in Sysmon)
            release_all_modifiers()
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            micro_delay()
            user32.keybd_event(VK_R, 0, 0, 0)
            micro_delay()
            user32.keybd_event(VK_R, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

            human_delay(0.8, 1.3, reading_prob=0.0)
            type_text_human("chrome", typo_rate=0.0)
            human_delay(0.3, 0.6, reading_prob=0.0)
            press_key(VK_RETURN)
            human_delay(2.8, 3.8, reading_prob=0.0)

            hwnd = get_chrome_hwnd()
            if hwnd:
                user32.ShowWindowAsync(hwnd, SW_MAXIMIZE)
            human_delay(0.5, 0.8, reading_prob=0.0)
        else:
            user32.SetForegroundWindow(hwnd)
            user32.ShowWindowAsync(hwnd, SW_MAXIMIZE)
            human_delay(0.4, 0.7, reading_prob=0.0)

        for idx, url in enumerate(target_urls):
            log_debug(f"Navigating to {url}")

            # 25% chance to open a brand new tab (Ctrl+T) if Chrome is already open
            opened_new_tab = False
            if (chrome_already_open or idx > 0) and (random.random() < 0.25):
                log_debug("Opening URL in a new tab (Ctrl + T)")
                user32.keybd_event(VK_CONTROL, 0, 0, 0)
                micro_delay()
                user32.keybd_event(VK_T, 0, 0, 0)
                micro_delay()
                user32.keybd_event(VK_T, 0, KEYEVENTF_KEYUP, 0)
                user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
                opened_new_tab = True
                human_delay(0.4, 0.7, reading_prob=0.0)
            else:
                # Click address bar with mouse (with jolt & curve)
                addr_x = int(screen_w * random.uniform(0.30, 0.44))
                addr_y = 54
                human_click(addr_x, addr_y, trigger_jolt=True)

                # Ensure address bar focus is established
                user32.keybd_event(VK_CONTROL, 0, 0, 0)
                micro_delay()
                user32.keybd_event(VK_L, 0, 0, 0)
                micro_delay()
                user32.keybd_event(VK_L, 0, KEYEVENTF_KEYUP, 0)
                user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
                human_delay(0.3, 0.6, reading_prob=0.0)

            # Type URL and press Enter
            type_text_human(url, typo_rate=0.04)
            human_delay(0.3, 0.6, reading_prob=0.0)
            press_key(VK_RETURN)

            # Tight 1.0s to 2.0s initial load pause
            human_delay(1.0, 2.0, reading_prob=0.0)

            # Dynamic check: Did this site hit the SSL warning?
            hwnd = get_chrome_hwnd()
            if is_ssl_error_page(hwnd, url):
                # [INTEGRATION] Re-check after a short pause: while a real page is
                # still loading, Chrome shows the URL as the title, which looks
                # like an SSL page. Only bypass if it still looks like one.
                human_delay(1.2, 2.0, reading_prob=0.0)
                hwnd = get_chrome_hwnd()
                if is_ssl_error_page(hwnd, url):
                    bypass_ssl_4_tabs()
                    human_delay(1.5, 2.5, reading_prob=0.0)
                else:
                    log_debug(f"SSL false alarm (page was still loading) for {url}.")
            else:
                log_debug(f"Direct connection confirmed for {url}.")

            # IMMEDIATE INITIAL SCROLL: Scroll down 2-3 notches before reading
            human_scroll(ticks=-random.randint(2, 3))
            human_delay(0.8, 1.5, reading_prob=0.20)

            # Determine scroll depth: long sites (like apnews.com) get 6-10 scrolls
            is_long_site = any(domain in url.lower() for domain in LONG_CONTENT_DOMAINS)
            scroll_cycles = random.randint(6, 10) if is_long_site else random.randint(2, 4)
            log_debug(f"Exploring {url} (Long site: {is_long_site}, Cycles: {scroll_cycles})")

            # Main content exploration (hovering and reading scrolls)
            for _ in range(scroll_cycles):
                rx = int(screen_w * random.uniform(0.35, 0.65))
                ry = int(screen_h * random.uniform(0.36, 0.62))
                human_hover(rx, ry, hover_s=random.uniform(0.3, 0.6), trigger_jolt=False)
                human_scroll(ticks=-random.randint(2, 4))
                human_delay(1.5, 3.2, reading_prob=0.30)

            # Scroll back up slightly to mimic re-reading
            human_scroll(ticks=random.randint(2, 3))
            human_delay(1.0, 1.8, reading_prob=0.20)

        if close_when_done:
            close_chrome_with_mouse()
            human_delay(0.8, 1.3, reading_prob=0.0)

    finally:
        release_all_modifiers()

# ---------------------------------------------------------------------------
# PUBLIC CALLABLE FUNCTIONS (For Orchestrator Integration)
# ---------------------------------------------------------------------------
def browse_hardware_procurement(
    urls: Optional[Union[str, List[str]]] = None,
    count: int = 1,
    close_when_done: bool = True
):
    """Workflow 1: Browses hardware pricing across Apple, Amazon, Dell, Samsung, etc."""
    if isinstance(urls, str):
        target_list = [urls]
    elif isinstance(urls, list):
        target_list = urls
    else:
        k = min(len(HARDWARE_SITES), max(1, count))
        target_list = random.sample(HARDWARE_SITES, k=k)

    execute_web_session(target_list, "Hardware Procurement", close_when_done=close_when_done)

def browse_market_intelligence(
    urls: Optional[Union[str, List[str]]] = None,
    count: int = 1,
    close_when_done: bool = True
):
    """Workflow 2: Browses market intelligence across AP News, CoinMarketCap, Coinbase, etc."""
    if isinstance(urls, str):
        target_list = [urls]
    elif isinstance(urls, list):
        target_list = urls
    else:
        k = min(len(MARKET_SITES), max(1, count))
        target_list = random.sample(MARKET_SITES, k=k)

    execute_web_session(target_list, "Market Intelligence", close_when_done=close_when_done)

if __name__ == "__main__":
    #print("[TEST] Running Workflow 2: Market tracking (Chrome stays open for notes)...")
    #browse_market_intelligence(urls="https://www.coinmarketcap.com", close_when_done=False)
    #print("[TEST] Browser is still open. Verify that focus can be handed to OpenOffice.")
    pass  # [INTEGRATION] an if-block of only comments is a SyntaxError on import

