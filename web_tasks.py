import ctypes
import math
import random
import re
import time
from typing import List, Optional, Union

import pyautogui

import human_io  # shared log-normal typing + Fitts's-law mouse paths
import ui_find    # locate real Chrome controls (UI Automation)

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
    Wide log-normal timing with simulated cognitive hesitations.
    min_s is a hard floor (callers rely on it as a minimum wait for a window or
    page); the upside spreads well past max_s's old cut-off instead of piling up
    against it, and a 'reading' pause is itself log-normal (2.5 s up to ~9 s).
    """
    check_emergency_stop()
    if random.random() < reading_prob:
        duration = min(9.0, 2.5 + random.lognormvariate(math.log(1.4), 0.6))
    else:
        span = max(max_s - min_s, 0.5 * min_s)
        duration = min_s + span * random.lognormvariate(math.log(0.5), 0.85)
        duration = min(duration, min_s + span * 3.0)

    t0 = time.time()
    while time.time() - t0 < duration:
        check_emergency_stop()
        time.sleep(0.04)

def micro_delay():
    check_emergency_stop()
    time.sleep(max(0.06, min(0.45, random.lognormvariate(math.log(0.12), 0.5))))

def get_mouse_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

# ---------------------------------------------------------------------------
# KINEMATIC MOUSE SIMULATION (Jolt, Bézier Path, Speed Profile)
# ---------------------------------------------------------------------------
def human_mouse_move(target_x: int, target_y: int, trigger_jolt: bool = True):
    """
    Delegates to human_io.human_move: Bezier path, minimum-jerk speed profile
    over a Fitts's-law duration (~100 cursor updates/s while moving, so the
    path is continuous rather than a handful of big hops), overshoot + correction.
    """
    human_io.human_move(target_x, target_y, jitter=trigger_jolt)

def human_hover(target_x: int, target_y: int, hover_s: float = 0.8, trigger_jolt: bool = True):
    human_mouse_move(target_x, target_y, trigger_jolt=trigger_jolt)
    t0 = time.time()
    while time.time() - t0 < hover_s:
        check_emergency_stop()
        # Hand resting on the mouse: tiny drifts at irregular intervals.
        user32.SetCursorPos(target_x + random.randint(-2, 2), target_y + random.randint(-2, 2))
        time.sleep(max(0.08, min(0.6, random.lognormvariate(math.log(0.17), 0.5))))

def human_click(target_x: int, target_y: int, trigger_jolt: bool = True):
    human_io.human_click(target_x, target_y, jitter=trigger_jolt)

def human_scroll(ticks: int = -3):
    direction = 1 if ticks > 0 else -1
    for _ in range(abs(ticks)):
        check_emergency_stop()
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, direction * 120, 0)
        gap = max(0.04, min(0.6, random.lognormvariate(math.log(0.11), 0.5)))
        if random.random() < 0.06:
            gap += random.uniform(0.3, 0.9)   # eyes catch something mid-scroll
        time.sleep(gap)

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
    """Same typing model as the Writer/Calc modules (human_io.human_type):
    log-normal per-key delays, a speed that drifts word to word, slower for
    symbols/long tokens (URLs), occasional neighbouring-key typo + Backspace."""
    human_io.human_type(text, typo_rate=typo_rate)

# ---------------------------------------------------------------------------
# WINDOW MANAGEMENT & SSL DETECTION
# ---------------------------------------------------------------------------
_WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)


def get_chrome_hwnd():
    """The visible Chrome BROWSER window. Chrome also owns hidden windows of
    the same class (menus, tooltips, helpers); FindWindowW can return one of
    those, and UI Automation then sees no page at all. Prefer the browser
    window in front, else any visible one titled '... - Google Chrome'."""
    found = []

    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(ctypes.c_void_p(hwnd), cls, 64)
            if cls.value == "Chrome_WidgetWin_1" and get_window_title(hwnd).endswith("Google Chrome"):
                found.append(hwnd)
        return True

    user32.EnumWindows(_WNDENUMPROC(cb), 0)
    front = user32.GetForegroundWindow()
    for hwnd in found:
        if hwnd == front:
            return hwnd
    if found:
        return found[0]
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

def focus_address_bar(use_mouse: bool = True):
    """Put the cursor in Chrome's address bar with its text selected. Mouse:
    click the REAL address bar, found by a bounded UI Automation lookup that
    does not walk the web page itself (with accessibility on, a page can hold
    thousands of controls). Falls back to Ctrl+L."""
    clicked = False
    if use_mouse and ui_find.available():
        bar = ui_find.find_office(get_chrome_hwnd(), names=["Address and search bar"],
                                  control_types=["EditControl"], skip_into=("DocumentControl",),
                                  timeout=2.0, label="Chrome address bar")
        clicked = bar is not None and ui_find.click_rect(ui_find.rect_of(bar))
    if not clicked:
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        micro_delay()
        user32.keybd_event(VK_L, 0, 0, 0)
        micro_delay()
        user32.keybd_event(VK_L, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    # Select any existing text so the new URL replaces it.
    human_delay(0.2, 0.5, reading_prob=0.0)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    micro_delay()
    send_char("a")
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    human_delay(0.3, 0.6, reading_prob=0.0)


def wait_for_site(url: str, timeout: float = 8.0) -> bool:
    """True once Chrome's title names the site ('amazon' for www.amazon.com,
    'apnews' for apnews.com; spaces ignored, so 'AP News' counts)."""
    host = url.split("//")[-1].split("/")[0].lower()
    parts = [p for p in host.split(".") if p != "www"]
    word = parts[-2] if len(parts) >= 2 else parts[0]
    end = time.time() + timeout
    while time.time() < end:
        if word in get_window_title(get_chrome_hwnd()).lower().replace(" ", ""):
            return True
        time.sleep(0.4)
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
    Closes Chrome by clicking its REAL title-bar Close button with the mouse
    (UI Automation, class 'WindowsCaptionButton' so it is never the tab's close
    button), verifies closure, and falls back to WM_CLOSE. Name kept: the
    orchestrator calls it.
    """
    hwnd = get_chrome_hwnd()
    if not hwnd or not user32.IsWindowVisible(hwnd):
        return

    ui_find.ensure_foreground(hwnd)
    user32.ShowWindowAsync(hwnd, SW_MAXIMIZE)
    time.sleep(0.3)

    clicked = False
    if ui_find.available():
        log_debug("Closing Chrome: clicking the caption Close button")
        button = ui_find.find_office(hwnd, names=["Close"], control_types=["ButtonControl"],
                                     class_name="WindowsCaptionButton", skip_into=("DocumentControl",),
                                     timeout=2.0, label="Chrome caption Close")
        clicked = button is not None and ui_find.click_rect(ui_find.rect_of(button))
    if not clicked:
        log_debug("Fallback: WM_CLOSE to Chrome")
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    human_delay(0.6, 0.8, reading_prob=0.0)

    # Deterministic fallback: ensure window is closed
    if user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
        log_debug("Fallback: Dispatching WM_CLOSE to terminate Chrome.")
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        time.sleep(0.5)

# ---------------------------------------------------------------------------
# LAUNCHING CHROME (always through the shell: ParentImage = explorer.exe)
# ---------------------------------------------------------------------------
CHROME_ICON_NAME = "Chrome"          # desktop shortcut, usually "Google Chrome"
VK_D = 0x44


def _wait_for_chrome(timeout: float) -> int:
    end = time.time() + timeout
    while time.time() < end:
        hwnd = get_chrome_hwnd()
        if hwnd and user32.IsWindowVisible(hwnd):
            return hwnd
        time.sleep(0.5)
    return 0


def _show_desktop() -> None:
    """Win+D, but only if a window covers the desktop (pressing it while the
    desktop is already showing would bring all the windows back)."""
    cls = ctypes.create_unicode_buffer(64)
    user32.GetClassNameW(ctypes.c_void_p(user32.GetForegroundWindow()), cls, 64)
    if cls.value in ("Progman", "WorkerW"):
        return
    user32.keybd_event(VK_LWIN, 0, 0, 0)
    micro_delay()
    user32.keybd_event(VK_D, 0, 0, 0)
    micro_delay()
    user32.keybd_event(VK_D, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
    human_delay(1.0, 1.8, reading_prob=0.0)


def launch_chrome() -> int:
    """Open Chrome like a person: double-click its icon on the desktop; if
    there is none, search for it in the Start menu and press Enter. The shell
    (explorer.exe) starts it either way. Returns Chrome's window or 0."""
    release_all_modifiers()
    if ui_find.available():
        _show_desktop()
        if ui_find.click_desktop_icon(CHROME_ICON_NAME, double=True):
            log_debug("Opening Chrome from its desktop icon")
            hwnd = _wait_for_chrome(15.0)
            if hwnd:
                return hwnd
        log_debug("No Chrome icon on the desktop - using the Start menu search")
    pyautogui.press("win")
    human_delay(0.8, 1.4, reading_prob=0.0)
    type_text_human("Google Chrome", typo_rate=0.0)
    human_delay(0.8, 1.4, reading_prob=0.0)
    press_key(VK_RETURN)
    return _wait_for_chrome(15.0)


# ---------------------------------------------------------------------------
# CORE GENERALIZED BROWSING SESSION
# ---------------------------------------------------------------------------
def execute_web_session(
    target_urls: List[str],
    session_name: str,
    close_when_done: bool = True,
    click_into_data: bool = False
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
            hwnd = launch_chrome()
            if hwnd:
                user32.ShowWindowAsync(hwnd, SW_MAXIMIZE)
            human_delay(0.5, 0.8, reading_prob=0.0)
        else:
            ui_find.ensure_foreground(hwnd)
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
                human_delay(0.3, 0.8, reading_prob=0.0)
                focus_address_bar()

            # Type URL and press Enter
            type_text_human(url, typo_rate=0.04)
            human_delay(0.3, 0.6, reading_prob=0.0)
            press_key(VK_RETURN)

            # Tight 1.0s to 2.0s initial load pause
            human_delay(1.0, 2.0, reading_prob=0.0)

            # Did Chrome really go there? If the typing landed in the old page
            # instead of the address bar, go to the address bar with Ctrl+L
            # and type the URL again (once).
            if not wait_for_site(url):
                log_debug(f"Still not on {url} (title '{get_window_title(get_chrome_hwnd())}') - retrying via Ctrl+L")
                ui_find.ensure_foreground(get_chrome_hwnd())
                focus_address_bar(use_mouse=False)
                type_text_human(url, typo_rate=0.0)
                human_delay(0.3, 0.6, reading_prob=0.0)
                press_key(VK_RETURN)
                human_delay(1.0, 2.0, reading_prob=0.0)
                wait_for_site(url)

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

            # Main content exploration: read what is on screen with the pointer
            # following the words/numbers, then scroll on. If the page exposes
            # no readable text, hover somewhere in the content instead.
            for _ in range(scroll_cycles):
                if random.random() < 0.65 and read_with_mouse():
                    human_delay(0.5, 1.4, reading_prob=0.15)
                else:
                    rx = int(screen_w * random.uniform(0.35, 0.65))
                    ry = int(screen_h * random.uniform(0.36, 0.62))
                    human_hover(rx, ry, hover_s=random.uniform(0.3, 0.6), trigger_jolt=False)
                    human_delay(1.5, 3.2, reading_prob=0.30)
                human_scroll(ticks=-random.randint(2, 4))

            # Scroll back up slightly to mimic re-reading
            human_scroll(ticks=random.randint(2, 3))
            human_delay(1.0, 1.8, reading_prob=0.20)

            # Click into the site's data (a product / link), then come back.
            # Any error page or robot check is simply read and left.
            if click_into_data:
                try:
                    click_into_page_data()
                except pyautogui.FailSafeException:
                    raise
                except Exception as error:
                    log_debug(f"Page click skipped: {error!r}")

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

    # Apple / Amazon: also click into a product or link on the page.
    execute_web_session(target_list, "Hardware Procurement", close_when_done=close_when_done,
                        click_into_data=True)

# ---------------------------------------------------------------------------
# CLICKING INTO LIVE WEB DATA (UI Automation) — judges' "click into data"
# ---------------------------------------------------------------------------
VK_LEFT = 0x25


def click_coin_row(coin_name: str = "Bitcoin") -> bool:
    """On the CoinGecko table, click the coin's row (a DataItemControl such as
    'BTC Bitcoin BTC'), opening its page like a person would. Returns True/False."""
    if not ui_find.available():
        return False
    hwnd = get_chrome_hwnd()
    row = ui_find.find(hwnd, name=coin_name, control_type="DataItemControl", contains=True)
    if row is None:
        # Some layouts expose the coin as a hyperlink instead of a table row.
        row = ui_find.find(hwnd, name=coin_name, control_type="HyperlinkControl", contains=True)
    return ui_find.click(row)


def page_document():
    """The web page itself (Chrome's DocumentControl), or None.

    Chrome builds a page's accessibility tree only once an assistive tool
    asks for it the classic way (see enable_web_accessibility); until then
    the page is ONE empty pane. Ask, then wait (up to ~6 s) for real content.
    Chrome wraps the page in an unnamed DocumentControl; the real page inside
    it carries the page title, so the named one is returned when present."""
    if not ui_find.available():
        return None
    doc = None
    end = time.time() + 6.0
    while True:
        hwnd = get_chrome_hwnd()
        # A covered or minimised Chrome stops exposing its page.
        if hwnd and user32.GetForegroundWindow() != hwnd:
            ui_find.ensure_foreground(hwnd)
        asked = enable_web_accessibility(hwnd)
        docs = page_documents(hwnd)
        full = [d for d in docs if _has_web_content(d)]
        if full:
            # Chrome's own (UIA) page carries the page title; the unnamed one
            # is the empty legacy window stand-in.
            return _best_document(max(full, key=lambda d: (bool(ui_find.text_of(d)), _area(d))))
        doc = docs[0] if docs else None
        if time.time() >= end:
            log_debug(f"Web page has no accessible content (asked {asked} page window(s), "
                      f"doc={ui_find.rect_of(doc) if doc is not None else None})")
            return doc
        time.sleep(0.5)


def page_documents(chrome_hwnd, max_nodes: int = 2500):
    """Every visible DocumentControl in the Chrome window (breadth-first, not
    looking inside documents). Chrome can show the same page twice: an
    unnamed empty stand-in for its legacy page window, and its real page."""
    root = ui_find._window_control(chrome_hwnd) if chrome_hwnd else None
    found, queue, seen = [], [root] if root is not None else [], 0
    while queue and seen < max_nodes:
        ctl = queue.pop(0)
        try:
            child = ctl.GetFirstChildControl()
            while child is not None and seen < max_nodes:
                seen += 1
                if child.ControlTypeName == "DocumentControl":
                    if _area(child) > 0 and not getattr(child, "IsOffscreen", False):
                        found.append(child)
                else:
                    queue.append(child)
                child = child.GetNextSiblingControl()
        except Exception:
            continue
    print(f"[uia] web page: {len(found)} document(s) "
          + ", ".join(f"{ui_find.text_of(d)[:40]!r}" for d in found) + f" after {seen} controls")
    return found


def _area(control) -> int:
    r = ui_find.rect_of(control)
    return (r[2] - r[0]) * (r[3] - r[1]) if r else 0


def _best_document(doc, max_depth: int = 4):
    """The page document under Chrome's wrapper: among visible DocumentControls
    a few levels down, the named one first, then the largest."""
    best, best_key = doc, (bool(ui_find.text_of(doc)), _area(doc))
    stack = [(doc, 0)]
    while stack:
        ctl, depth = stack.pop()
        if depth >= max_depth:
            continue
        try:
            child, n = ctl.GetFirstChildControl(), 0
            while child is not None and n < 60:
                if child.ControlTypeName == "DocumentControl" and not child.IsOffscreen:
                    key = (bool(ui_find.text_of(child)), _area(child))
                    if key[1] > 0 and key > best_key:
                        best, best_key = child, key
                stack.append((child, depth + 1))
                child, n = child.GetNextSiblingControl(), n + 1
        except Exception:
            continue
    return best


def _has_web_content(doc) -> bool:
    """False while the page is just Chrome's empty render pane (accessibility
    off); True once it holds real controls (text, links, groups...)."""
    try:
        child = doc.GetFirstChildControl()
        while child is not None:
            if child.ControlTypeName != "PaneControl" or child.GetFirstChildControl() is not None:
                return True
            child = child.GetNextSiblingControl()
    except Exception:
        pass                    # an unreadable tree is not content yet
    return False


_ENUMCHILDPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
_OBJID_CLIENT = -4
_WM_GETOBJECT = 0x003D


def page_windows(chrome_hwnd):
    """Chrome's page (renderer) windows, Chrome_RenderWidgetHostHWND."""
    targets = []
    if not chrome_hwnd:
        return targets

    def cb(hwnd, _):
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(ctypes.c_void_p(hwnd), cls, 64)
        if cls.value == "Chrome_RenderWidgetHostHWND":
            targets.append(hwnd)
        return True

    user32.EnumChildWindows(ctypes.c_void_p(chrome_hwnd), _ENUMCHILDPROC(cb), 0)
    return targets


def knock(hwnd) -> None:
    """The plain screen-reader knock: WM_GETOBJECT for the client object."""
    send = user32.SendMessageTimeoutW
    send.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t,
                     ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_size_t)]
    result = ctypes.c_size_t()
    send(ctypes.c_void_p(hwnd), _WM_GETOBJECT, 0, _OBJID_CLIENT, 0x0002, 1000,  # SMTO_ABORTIFHUNG
         ctypes.byref(result))


def _iaccessible_type():
    try:
        from comtypes.gen.Accessibility import IAccessible
    except ImportError:
        import comtypes.client
        IAccessible = comtypes.client.GetModule("oleacc.dll").IAccessible
    return IAccessible


def _msaa_root(hwnd):
    """The page window's IAccessible (comtypes pointer), or None."""
    IAccessible = _iaccessible_type()
    acc = ctypes.POINTER(IAccessible)()
    hr = ctypes.windll.oleacc.AccessibleObjectFromWindow(
        ctypes.c_void_p(hwnd), ctypes.c_long(_OBJID_CLIENT), ctypes.byref(IAccessible._iid_),
        ctypes.byref(acc))
    return acc if hr == 0 and acc else None


def msaa_read(hwnd) -> str:
    """Use the page through MSAA like a screen reader: read the root's name,
    role and children. Newer Chrome builds the page tree only once an
    assistive tool actually USES it, not when it merely asks for it."""
    acc = _msaa_root(hwnd)
    if acc is None:
        return "no MSAA object"
    IAccessible = _iaccessible_type()
    count = acc.accChildCount
    names = [acc.accName(0), acc.accRole(0)]
    for i in range(1, min(count, 5) + 1):
        try:
            child = acc.accChild(i).QueryInterface(IAccessible)
            names.append(child.accName(0))
        except Exception:
            try:
                names.append(acc.accName(i))
            except Exception:
                pass
    return f"{count} children, {names!r}"[:160]


def enable_web_accessibility(chrome_hwnd) -> int:
    """Make Chrome build web pages' accessibility trees, the way a screen
    reader does, on each page window (Chrome_RenderWidgetHostHWND): knock
    (WM_GETOBJECT), then take its MSAA object and read from it. No command
    line flag is involved. Returns how many page windows were asked."""
    targets = page_windows(chrome_hwnd)
    if not targets:
        log_debug(f"No Chrome page window under {chrome_hwnd!r}")
        return 0                # the top-level window does not switch anything on
    for hwnd in targets:
        knock(hwnd)
        try:
            msaa_read(hwnd)
        except Exception as error:
            log_debug(f"MSAA read failed: {error!r}")
    return len(targets)


def visible_links(min_len: int = 3, control_types=("HyperlinkControl",), retries: int = 3):
    """Links that are on screen in the page, in reading order. A link counts
    once its centre is in view. Chrome may still be building the tree of a
    heavy page (Apple, Amazon), so an empty answer is retried a few times."""
    for attempt in range(retries):
        try:
            doc = page_document()
            if doc is not None:
                links = ui_find.visible_controls(
                    doc, list(control_types), center_only=True, limit=80, max_nodes=4000, timeout=6.0,
                    accept=lambda c, r: len(ui_find.text_of(c).strip()) >= min_len and r[2] - r[0] >= 20)
                if links:
                    return links
        except pyautogui.FailSafeException:
            raise
        except Exception as error:          # COM errors while the page rebuilds
            log_debug(f"Link search error: {error!r}")
        if attempt < retries - 1:
            time.sleep(0.5)
    return []


# What the research notes are about: markets, crypto, economy, energy.
# Whole words only: 'prices' alone (ticket resale prices...) is not finance.
_FINANCE = re.compile(
    r"\b(stocks?|stock market|markets?|wall street|dow|nasdaq|s&p|shares|investors?|investing|"
    r"investments?|traders?|bitcoin|crypto\w*|ethereum|blockchain|econom\w*|inflation|"
    r"interest rates?|federal reserve|the fed|fed (chair|rate|officials?)|central banks?|banks?|"
    r"banking|dollar|currenc\w+|tariffs?|trade (war|deal|deficit|talks)|earnings|profits?|"
    r"revenue|financ\w*|bonds?|treasur\w+|oil|opec|gasoline|recession|unemployment|jobless|"
    r"jobs report|gdp|debt|budget|mortgages?|housing market|layoffs|ipo|retail sales|"
    r"(stock|oil|gas|home|food|energy|consumer) prices)\b",
    re.I)


def _finance_on_screen() -> bool:
    """Is a finance / market headline or paragraph showing in the page?"""
    view = _page_view()
    for c in visible_links(min_len=25, retries=1):
        if _FINANCE.search(ui_find.text_of(c)) and _shown_part(ui_find.rect_of(c), view):
            return True
    for c, r in text_blocks(min_width=250, min_height=30, max_height=320):
        if _FINANCE.search(ui_find.text_of(c)) and _shown_part(r, view):
            return True
    return False


def scroll_to_finance(max_scrolls: int = 8) -> bool:
    """Scroll down the page, looking a moment at each screen, until a finance
    or market story is showing. Returns True if one is on screen."""
    for _ in range(max_scrolls):
        if _finance_on_screen():
            return True
        human_scroll(ticks=-random.randint(3, 5))
        human_delay(0.8, 1.8, reading_prob=0.3)
    found = _finance_on_screen()
    log_debug(f"Finance story on screen after scrolling: {found}")
    return found


def _page_view():
    """The page area actually on screen (left, top, right, bottom), or None."""
    doc = page_document()
    r = ui_find.rect_of(doc) if doc is not None else None
    if not r:
        return None
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    return (max(r[0], 0), max(r[1], 0), min(r[2], sw), min(r[3], sh - 40))


def _shown_part(rect, view, min_h=12):
    """The part of rect inside view, or None if too little of it shows."""
    if not rect or not view:
        return None
    part = (max(rect[0], view[0]), max(rect[1], view[1]), min(rect[2], view[2]), min(rect[3], view[3]))
    return part if part[2] - part[0] >= 20 and part[3] - part[1] >= min_h else None


def click_news_headline(tries: int = 3) -> bool:
    """Open a news story by clicking its headline link (a real link, as in the
    challenge's 'click on a link' example). Finance / market headlines are
    preferred, so the copied excerpt fits the research notes; if none is on
    screen, scroll on a little and look again. Only the part of a headline
    that shows in the page is clicked, and the click counts only if the story
    really opens (the window title changes); otherwise another one is tried.
    If the story opens as an error page (404 ...), the browser goes back to
    the list; after two such pages it stays on the list (False).
    Returns True if a story was opened."""
    tried, errors, searched = set(), 0, False
    for attempt in range(tries + 2):
        view = _page_view()
        shown = []
        for c in visible_links(min_len=25):
            name = ui_find.text_of(c).strip()
            part = _shown_part(ui_find.rect_of(c), view)
            if part and name not in tried:
                shown.append((c, name, part))
        finance = [s for s in shown if _FINANCE.search(s[1])]
        if not finance and not searched:                 # look further down the page first
            searched = True
            if scroll_to_finance():
                continue
        pool = finance or shown
        if not pool:
            log_debug("No headline link on screen")
            return False
        link, name, part = random.choice(pool[:6])
        tried.add(name)
        title_before = get_window_title(get_chrome_hwnd())
        log_debug(f"Opening {'finance ' if finance else ''}headline {name[:70]!r}")
        if ui_find.click_rect(part) and _wait_title_change(title_before, 8.0):
            human_delay(1.5, 3.0, reading_prob=0.2)       # let the story load
            if not _ERROR_PAGE.search(get_window_title(get_chrome_hwnd())):
                return True
            # An error page (404...): read it a moment, then go back to the list.
            log_debug("Story opened as an error page - going back")
            human_delay(1.0, 2.0, reading_prob=0.3)
            go_back()
            _wait_title_change(get_window_title(get_chrome_hwnd()), 6.0)
            human_delay(1.0, 2.0, reading_prob=0.2)
            errors += 1
            if errors >= 2:                               # stories don't open here: stay on the list
                return False
            continue
        log_debug("Story did not open - trying another headline")
        if len(tried) >= tries:
            break
    return False


# Window title of an error page instead of a story.
_ERROR_PAGE = re.compile(r"\b(404|403|500|502|503|not found|error|access denied|forbidden|"
                         r"page (is )?not available)\b", re.I)


# Links that lead to a price: a shown price, or Buy / Shop / Deal / options.
_PRICE_LINK = re.compile(r"[$€£]\s?\d|\bbuy\b|\bshop\b|price|deal|add to cart|"
                         r"see (all )?options|compare|\bsale\b", re.I)
# Site chrome, not data: account, cart / bag, menus, skip links.
_SKIP_LINK = re.compile(r"^(sign ?in|log ?in|account|menu|open menu|skip to\b.*|.*\b(cart|bag)\b.*|"
                        r"returns (&|and) orders|hello, sign in.*|privacy.*|cookie.*|terms.*)$", re.I)


def page_data_links():
    """(priced, pool, view): the links and named icon buttons in the page
    content a shopper would click to check a price, and the page area. The
    thin bar at the very top of the page and the left page edge (menus,
    logos) are left out."""
    links = visible_links(control_types=("HyperlinkControl", "ButtonControl"))
    doc = page_document() if links else None
    view = ui_find.rect_of(doc) if doc is not None else None
    if view is None:
        return [], [], None
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    l, t, r, b = max(view[0], 0), max(view[1], 0), min(view[2], sw), min(view[3], sh)

    def content(c):
        name = ui_find.text_of(c).strip()
        rc = ui_find.rect_of(c)
        if not rc or not 3 <= len(name) <= 90 or _SKIP_LINK.match(name):
            return False
        cx, cy = (rc[0] + rc[2]) // 2, (rc[1] + rc[3]) // 2
        return cx >= l + 0.10 * (r - l) and t + 30 <= cy <= b - 10

    pool = [c for c in links if content(c)]
    priced = [c for c in pool if _PRICE_LINK.search(ui_find.text_of(c))]
    return priced, pool, (l, t, r, b)


def _on_screen_part(rect, view):
    """The part of a (possibly tall) link that shows in the page area, so the
    click never lands on the toolbar above it or the taskbar below."""
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    return (max(rect[0], view[0], 0), max(rect[1], view[1], 0),
            min(rect[2], view[2], sw), min(rect[3], view[3], sh - 40))


def _wait_title_change(title_before: str, timeout: float = 6.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if get_window_title(get_chrome_hwnd()) != title_before:
            return True
        time.sleep(0.3)
    return False


def click_into_page_data() -> bool:
    """Check a price like a person would: click a visible link that leads to
    one (a price, Buy, Shop, a deal), let the page open, look at the price on
    it, and stay there. Whatever the site answers (an error page, a robot
    check) is simply left as it is. Returns True if a link was clicked."""
    priced, pool, view = [], [], None
    for attempt in range(3):
        priced, pool, view = page_data_links()
        if pool:
            break
        if attempt < 2:                     # nothing here: scroll on a little and look again
            human_scroll(ticks=-random.randint(2, 4))
            human_delay(0.6, 1.2, reading_prob=0.2)
    if not pool:
        log_debug("No clickable link or icon in the page content")
        return False
    choices = priced or pool
    # Mostly something in the upper / middle part of the screen, sometimes any.
    link = random.choice(choices[: max(4, len(choices) // 2)] if random.random() < 0.7 else choices)
    name = ui_find.text_of(link)
    title_before = get_window_title(get_chrome_hwnd())
    log_debug(f"Clicking {'price ' if priced else ''}{link.ControlTypeName} {name[:60]!r}")
    rect = ui_find.rect_of(link)              # re-read just before pressing
    if not rect or not ui_find.click_rect(_on_screen_part(rect, view)):
        return False
    if not _wait_title_change(title_before):
        # The first click may only have closed a pop-up / overlay: once more.
        again = next((c for c in visible_links(control_types=("HyperlinkControl", "ButtonControl"),
                                               retries=1)
                      if ui_find.text_of(c) == name), None)
        if again is not None and ui_find.rect_of(again):
            log_debug("Page did not change - clicking the link once more")
            ui_find.click_rect(_on_screen_part(ui_find.rect_of(again), view))
            _wait_title_change(title_before)
    human_delay(1.0, 2.0, reading_prob=0.0)
    human_scroll(ticks=-random.randint(1, 2))
    if not read_with_mouse(prefer_prices=True):     # look at the price, if one is shown
        human_delay(1.5, 3.0, reading_prob=0.3)
    return True


# How Chrome shows page text depends on its accessibility mode: as named
# TextControls (native UIA) or, through IAccessible2, as paragraph/group
# blocks with NO name whose text is not exposed as children. So text blocks
# are found by shape: a visible text control, or a childless block of a
# reading-sized box, never by requiring the text in Name.
_TEXT_BLOCK_TYPES = ["TextControl", "GroupControl", "CustomControl", "PaneControl",
                     "ListItemControl", "DataItemControl", "HyperlinkControl", "HeaderControl"]


def _is_leaf(control) -> bool:
    try:
        return control.GetFirstChildControl() is None
    except Exception:
        return False


def text_blocks(min_width: int = 60, min_height: int = 10, max_height: int = 300, limit: int = 40):
    """On-screen blocks of page text (words, numbers, paragraphs) in reading
    order, as (control, rect)."""
    doc = page_document()
    if doc is None:
        return []

    def accept(c, r):
        w, h = r[2] - r[0], r[3] - r[1]
        if w < min_width or not (min_height <= h <= max_height):
            return False
        if c.ControlTypeName == "TextControl":
            return True
        return _is_leaf(c)            # a container with no children holds its own text

    found = ui_find.visible_controls(doc, _TEXT_BLOCK_TYPES, accept=accept, limit=limit)
    out = []
    for c in found:
        r = ui_find.rect_of(c)
        if r:
            out.append((c, r))
    log_debug(f"{len(out)} text blocks on screen")
    return out


def _is_link_at(x: int, y: int) -> bool:
    """True if the point is on a link (pressing there would drag/open the link)."""
    ctl = ui_find.control_at(x, y)
    for _ in range(3):
        if ctl is None:
            return False
        try:
            if ctl.ControlTypeName == "HyperlinkControl":
                return True
            ctl = ctl.GetParentControl()
        except Exception:
            return False
    return False


_PRICE_TEXT = re.compile(r"[$€£]\s?\d|\d[\d,.]*\s?(usd|sgd)\b", re.I)


def _word_layout(text: str, rect):
    """Where the words of a text block actually are, estimated from the text
    length (a block's box is often wider than its words): (line_h, char_w,
    widths of each line in px)."""
    left, top, right, bottom = rect
    box_w, h = right - left, bottom - top
    line_h = h if h <= 34 else 24                     # one line, or ~body text lines
    char_w = max(5.0, line_h * 0.42)
    total = len(text) * char_w
    lines, widths = max(1, round(h / line_h)), []
    for _ in range(lines):
        widths.append(min(box_w, total))
        total -= box_w
        if total <= 0:
            break
    return line_h, char_w, widths


def _follow_words(x0: int, y: int, px: int, char_w: float) -> None:
    """Pointer follows ~px of words left to right the way eyes do: short hops
    from word to word with tiny pauses, not one long sweep."""
    human_io.human_move(x0, y + random.randint(-2, 2), jitter=False)
    x = x0
    while x < x0 + px:
        hop = char_w * random.uniform(4, 9)           # roughly one word
        nx = min(x0 + px, x + hop)
        secs = max(0.08, (nx - x) / random.uniform(220, 420))
        sx, ny = x, y + random.randint(-1, 1)
        human_io._glide(lambda t: (sx + (nx - sx) * t, ny), secs)
        x = nx
        time.sleep(random.uniform(0.05, 0.25))        # fixation on the word
        if random.random() < 0.06:
            time.sleep(random.uniform(0.4, 1.0))      # re-read / think


def read_with_mouse(blocks: int = 0, prefer_prices: bool = False) -> bool:
    """'Read' a little of what the page shows with the pointer on the words:
    pick one to three pieces of text whose words are known (a headline, a
    product name, a price), follow a phrase or part of a line, maybe carry on
    to the next line, then glance elsewhere. Never every line, never empty
    space. Returns False if no text with known words is on screen (the caller
    then just rests the pointer)."""
    named = [(c, r) for c, r in text_blocks()
             if len(ui_find.text_of(c).strip()) >= 3]
    if not named:
        return False
    if prefer_prices:
        priced = [b for b in named if _PRICE_TEXT.search(ui_find.text_of(b[0]))]
        named = priced + [b for b in named if b not in priced] if priced else named
        picks = named[:random.randint(1, 2)]
    else:
        picks = random.sample(named, k=min(len(named), blocks or random.randint(1, 3)))
    picks.sort(key=lambda cr: cr[1][1])               # top to bottom, like reading
    for control, rect in picks:
        text = " ".join(ui_find.text_of(control).split())
        line_h, char_w, widths = _word_layout(text, rect)
        left, top = rect[0], rect[1]
        for i, width in enumerate(widths[:3]):
            if i and random.random() < 0.6:
                break                                 # most of the time: not the next line
            # A phrase: the whole line when it is short, else a few words of it.
            phrase = width if width < char_w * 30 else width * random.uniform(0.35, 0.8)
            y = top + int(line_h * (i + 0.5))
            _follow_words(left + random.randint(1, 4), y, int(phrase), char_w)
        human_io.human_pause(0.3, 1.2, think_prob=0.1)
    return True


def highlight_and_copy_paragraph(min_chars: int = 80, headline_chars: int = 30):
    """Highlight useful text on the page by dragging the mouse across it, copy
    it (Ctrl+C) and return the copied text, or None. A real paragraph is
    preferred; on a front page where every headline is a LINK, a headline is
    highlighted instead by starting the drag in the margin just LEFT of the link
    (pressing on the link itself would drag the link, not select text). The
    clipboard is left holding plain text, so pasting in Writer brings no web
    formatting. Text about markets / the economy is preferred; short labels
    (a section name like 'CLIMATE') are never taken. If nothing about
    finance is on screen, the page is scrolled down to find something first;
    only when the page has nothing at all about it is other text taken."""
    if not _finance_on_screen():
        scroll_to_finance()
    view = _page_view()
    candidates = []
    # 1) Paragraph-shaped, non-link blocks (an article body). A block whose
    #    text is known must be paragraph-long; unnamed blocks are judged by
    #    the copied text afterwards.
    for c, r in text_blocks(min_width=250, min_height=30, max_height=320):
        name = ui_find.text_of(c).strip()
        part = _shown_part(r, view, min_h=20)
        if c.ControlTypeName != "HyperlinkControl" and part and (not name or len(name) >= min_chars):
            candidates.append(("para", c, part))
    candidates.sort(key=lambda t: (not _FINANCE.search(ui_find.text_of(t[1])),
                                   len(ui_find.text_of(t[1])) < min_chars, t[2][1]))
    # 2) Headline links (their text is in Name, so its length is known).
    heads = []
    for c in visible_links(min_len=headline_chars):
        part = _shown_part(ui_find.rect_of(c), view, min_h=20)
        if part and part[2] - part[0] >= 150:
            heads.append(("head", c, part))
    heads.sort(key=lambda t: (not _FINANCE.search(ui_find.text_of(t[1])), -len(ui_find.text_of(t[1]))))
    candidates += heads[:6]
    # Finance text on screen: take only that (unnamed blocks are kept, their
    # text is unknown until copied).
    on_topic = [t for t in candidates if _FINANCE.search(ui_find.text_of(t[1]))]
    if on_topic:
        unnamed = [t for t in candidates if t[0] == "para" and not ui_find.text_of(t[1]).strip()]
        candidates = ([t for t in on_topic if t[0] == "para"] + unnamed
                      + [t for t in on_topic if t[0] == "head"])

    tried = 0
    for kind, block, (left, top, right, bottom) in candidates:
        first_line = top + min(10, (bottom - top) // 2)
        ex, ey = right - 3, bottom - min(8, (bottom - top) // 3)
        if kind == "para":
            sx = left + 2
            if _is_link_at(sx, first_line) or _is_link_at((left + right) // 2, (top + bottom) // 2):
                continue
        else:
            # On a link, Chrome selects text instead of dragging the link
            # while Alt is held, so the drag runs over the headline itself.
            sx = left + random.randint(1, 3)
        tried += 1
        text = _drag_select_and_copy(sx, first_line, ex, ey, alt=(kind == "head"))
        need = min_chars if kind == "para" else headline_chars
        if len(text) >= need and on_topic and not _FINANCE.search(text):
            log_debug(f"Copied text is off topic ({text[:50]!r}) - trying another")
            continue
        if len(text) >= need:
            clipboard_set_text(text)              # plain text only
            log_debug(f"Copied {kind} ({len(text)} chars): {text[:60]!r}...")
            return text
        log_debug(f"Copy of {kind} gave {len(text)} chars - trying another")
        if tried >= 4:
            break
    log_debug(f"Nothing copied ({len(candidates)} candidates, {tried} tried)")
    return None


def _drag_select_and_copy(sx: int, sy: int, ex: int, ey: int, alt: bool = False) -> str:
    """Press at (sx, sy), drag to (ex, ey), release, Ctrl+C. Returns the
    copied text with whitespace collapsed ('' if nothing was copied).
    alt: hold Alt during the drag (selects a link's text in Chrome). Ctrl
    goes down before Alt comes up, so the lone Alt never opens a menu."""
    human_io.human_move(sx, sy)
    human_delay(0.3, 0.7, reading_prob=0.0)
    if alt:
        user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(random.uniform(0.08, 0.2))
    try:
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        try:
            time.sleep(random.uniform(0.08, 0.2))
            human_io._glide(lambda t: (sx + (ex - sx) * t, sy + (ey - sy) * t),
                            random.uniform(0.8, 1.8))
            human_io._set_cursor(ex, ey)
            time.sleep(random.uniform(0.1, 0.25))
        finally:
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        human_delay(0.4, 0.9, reading_prob=0.0)
        clipboard_set_text("")                    # so a failed copy is detectable
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
    finally:
        if alt:
            micro_delay()
            user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    micro_delay()
    send_char("c")
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    human_delay(0.4, 0.8, reading_prob=0.0)
    return " ".join(clipboard_get_text().split())


# --- clipboard (plain text) ---------------------------------------------------
_kernel32 = ctypes.WinDLL("kernel32")
_kernel32.GlobalAlloc.restype = ctypes.c_void_p
_kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
_kernel32.GlobalLock.restype = ctypes.c_void_p
_kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
_kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
_cb = ctypes.WinDLL("user32")                    # own instance for the clipboard calls
_cb.GetClipboardData.restype = ctypes.c_void_p
_cb.SetClipboardData.restype = ctypes.c_void_p
_cb.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
CF_UNICODETEXT = 13


def _open_clipboard() -> bool:
    for _ in range(10):
        if _cb.OpenClipboard(None):
            return True
        time.sleep(0.05)
    return False


def clipboard_get_text() -> str:
    if not _open_clipboard():
        return ""
    try:
        handle = _cb.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        ptr = _kernel32.GlobalLock(handle)
        try:
            return ctypes.wstring_at(ptr) if ptr else ""
        finally:
            _kernel32.GlobalUnlock(handle)
    finally:
        _cb.CloseClipboard()


def clipboard_set_text(text: str) -> None:
    if not _open_clipboard():
        return
    try:
        _cb.EmptyClipboard()
        data = ctypes.create_unicode_buffer(text)
        size = ctypes.sizeof(data)
        handle = _kernel32.GlobalAlloc(0x0002, size)          # GMEM_MOVEABLE
        ptr = _kernel32.GlobalLock(handle)
        ctypes.memmove(ptr, data, size)
        _kernel32.GlobalUnlock(handle)
        _cb.SetClipboardData(CF_UNICODETEXT, handle)
    finally:
        _cb.CloseClipboard()


def go_back() -> None:
    """Navigate back, clicking the real Back button (UI Automation) or Alt+Left."""
    if ui_find.available():
        back = ui_find.find_office(get_chrome_hwnd(), names=["Back"], control_types=["ButtonControl"],
                                   skip_into=("DocumentControl",), timeout=2.0, label="Chrome Back")
        if back is not None and ui_find.click_rect(ui_find.rect_of(back)):
            return
    user32.keybd_event(VK_MENU, 0, 0, 0)
    micro_delay()
    user32.keybd_event(VK_LEFT, 0, 0, 0)
    micro_delay()
    user32.keybd_event(VK_LEFT, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)


def browse_market_intelligence(
    urls: Optional[Union[str, List[str]]] = None,
    count: int = 1,
    close_when_done: bool = True
):
    """Workflow 2: Browses market intelligence across AP News, CoinGecko, Coinbase, etc."""
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
    #browse_market_intelligence(urls="https://www.coingecko.com", close_when_done=False)
    #print("[TEST] Browser is still open. Verify that focus can be handed to OpenOffice.")
    pass  # [INTEGRATION] an if-block of only comments is a SyntaxError on import

