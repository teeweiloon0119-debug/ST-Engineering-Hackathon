"""
human_io - shared human-like input primitives for the WL (Writer / Calc) modules.

Based on the proven logic in DF/web_tasks.py (Bezier mouse paths, log-normal
timing, adjacent-key typos), packaged so every module moves and types the same
way instead of teleporting the cursor and typing at a constant rate.

- Mouse: own user32 instance + SetCursorPos / mouse_event (same as web_tasks).
- Keyboard: pyautogui.write / press per key with _pause=False, so pyautogui's
  FAILSAFE (mouse slammed into a screen corner) still fires on every keystroke.
- Shift+Esc: checked at every step (SystemExit, like web_tasks). The
  orchestrator's background watcher still ends the process on its own.
"""

import ctypes
import math
import random
import re
import time
from ctypes import wintypes

import pyautogui

# Own user32 instance: argtypes set by other modules must not leak in here.
user32 = ctypes.WinDLL("user32")
user32.GetForegroundWindow.restype = wintypes.HWND
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

WM_CLOSE = 0x0010
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_SHIFT, VK_CONTROL, VK_MENU, VK_ESCAPE, VK_LWIN = 0x10, 0x11, 0x12, 0x1B, 0x5B


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


# Left-hand neighbour on a QWERTY row (same table as web_tasks.ADJACENT_KEYS).
ADJACENT_KEYS = {
    'a': 's', 'b': 'v', 'c': 'x', 'd': 's', 'e': 'w', 'f': 'd',
    'g': 'f', 'h': 'g', 'i': 'u', 'j': 'h', 'k': 'j', 'l': 'k',
    'm': 'n', 'n': 'b', 'o': 'i', 'p': 'o', 'q': 'w', 'r': 'e',
    's': 'a', 't': 'r', 'u': 'y', 'v': 'c', 'w': 'q', 'x': 'z',
    'y': 't', 'z': 'x'
}


# =====================================================================
# SAFETY
# =====================================================================

def release_all_modifiers():
    for vk in (VK_MENU, VK_CONTROL, VK_SHIFT, VK_LWIN):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def check_emergency_stop():
    if (user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) and (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000):
        release_all_modifiers()
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        raise SystemExit("Emergency abort: Shift + ESC pressed.")


def _failsafe_check():
    """pyautogui's corner failsafe, also honoured during ctypes mouse moves."""
    check = getattr(pyautogui, "failSafeCheck", None)
    if check is not None:
        check()


def _sleep(seconds):
    """Sleep in short slices so Shift+Esc is noticed during long pauses."""
    end = time.time() + max(0.0, seconds)
    while True:
        check_emergency_stop()
        left = end - time.time()
        if left <= 0:
            return
        time.sleep(min(0.05, left))


# =====================================================================
# TIMING
# =====================================================================

def _lognorm_between(lo, hi, sigma=0.6):
    """Log-normal value above lo (right-skewed, never uniform). lo is a hard
    floor (callers use it as a 'the window needs at least this long' wait);
    the long tail may run to 1.6x the nominal range instead of piling up at hi."""
    raw = random.lognormvariate(0.0, sigma)
    return max(lo, min(lo + 1.6 * (hi - lo), lo + (raw / 2.2) * (hi - lo)))


def human_pause(min_s=0.4, max_s=1.8, think_prob=0.08):
    """Pause between actions. Wide log-normal spread, with an occasional (~8%)
    long 'thinking' pause whose length is itself log-normal (2.5 s up to ~10 s)."""
    if random.random() < think_prob:
        duration = max(2.5, max_s) + random.lognormvariate(math.log(1.2), 0.7)
        duration = min(duration, max(10.0, max_s * 3.0))
    else:
        duration = _lognorm_between(min_s, max_s)
    _sleep(duration)


def micro_pause():
    _sleep(max(0.04, min(0.6, random.lognormvariate(math.log(0.11), 0.5))))


# =====================================================================
# MOUSE
# =====================================================================

def get_mouse_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def _screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def _clamp(x, y):
    # Stay 1px off the edges so a path never lands exactly on a FAILSAFE corner.
    w, h = _screen_size()
    return max(1, min(w - 2, int(round(x)))), max(1, min(h - 2, int(round(y))))


def _set_cursor(x, y):
    check_emergency_stop()
    _failsafe_check()
    user32.SetCursorPos(*_clamp(x, y))


def _start_jitter():
    """Hand-on-mouse wobble before setting off: sometimes none at all, sometimes
    a few twitches whose size and spacing both vary."""
    if random.random() < 0.35:
        return
    cx, cy = get_mouse_pos()
    amp = max(1.0, min(14.0, random.lognormvariate(math.log(4.0), 0.6)))
    for _ in range(random.randint(1, 4)):
        _set_cursor(cx + random.uniform(-amp, amp), cy + random.uniform(-amp, amp))
        time.sleep(random.uniform(0.012, 0.06))


def _move_duration(dist):
    """Fitts's-law style travel time: grows with log(distance), times a wide
    log-normal factor so no two moves of the same length take the same time."""
    base = 0.18 + 0.11 * math.log2(1.0 + dist / 24.0)
    return max(0.14, min(1.9, base * random.lognormvariate(0.0, 0.30)))


def _min_jerk(t):
    """Minimum-jerk position profile: bell-shaped velocity, like a real hand."""
    return t * t * t * (10.0 + t * (-15.0 + 6.0 * t))


def _glide(points_fn, duration):
    """Drive the cursor along points_fn(progress 0..1) for `duration` seconds.
    Time-based (not step-count based): ~120 cursor updates per second however
    long the move is, so the path never reads as a teleport in an input trace."""
    start = time.time()
    while True:
        s = (time.time() - start) / duration
        if s >= 1.0:
            return
        x, y = points_fn(_min_jerk(s))
        _set_cursor(x, y)
        time.sleep(random.uniform(0.005, 0.011))


def human_move(target_x, target_y, jitter=True):
    """Cubic Bezier path travelled with a minimum-jerk speed profile over a
    Fitts's-law duration, a slight overshoot past the target on longer moves,
    a short corrective sub-movement back, then a micro-settle onto the target."""
    target_x, target_y = int(target_x), int(target_y)
    if jitter:
        _start_jitter()

    sx, sy = get_mouse_pos()
    dx, dy = target_x - sx, target_y - sy
    dist = math.hypot(dx, dy)
    if dist < 3:
        _set_cursor(target_x, target_y)
        return

    # Overshoot a few px along the travel direction on longer moves.
    overshoot = dist > 60 and random.random() < 0.75
    if overshoot:
        over = random.uniform(3, min(14, dist * 0.04))
        ex = target_x + dx / dist * over + random.uniform(-2, 2)
        ey = target_y + dy / dist * over + random.uniform(-2, 2)
    else:
        ex, ey = target_x, target_y

    px, py = -dy / dist, dx / dist
    arc = min(140.0, max(12.0, dist * random.uniform(0.08, 0.30)))
    side = random.choice((-1.0, 1.0))
    c1x = sx + dx * random.uniform(0.2, 0.38) + px * arc * side + random.randint(-12, 12)
    c1y = sy + dy * random.uniform(0.2, 0.38) + py * arc * side + random.randint(-12, 12)
    c2x = sx + dx * random.uniform(0.62, 0.82) + px * arc * random.uniform(0.3, 0.8) * side + random.randint(-12, 12)
    c2y = sy + dy * random.uniform(0.62, 0.82) + py * arc * random.uniform(0.3, 0.8) * side + random.randint(-12, 12)

    def bezier(t):
        u = 1.0 - t
        return (u ** 3 * sx + 3 * u * u * t * c1x + 3 * u * t * t * c2x + t ** 3 * ex,
                u ** 3 * sy + 3 * u * u * t * c1y + 3 * u * t * t * c2y + t ** 3 * ey)

    _glide(bezier, _move_duration(dist))
    _set_cursor(ex, ey)

    if overshoot:
        # Corrective sub-movement: a short, slower glide from the overshoot back onto the target.
        time.sleep(random.uniform(0.03, 0.12))
        _glide(lambda t: (ex + (target_x - ex) * t, ey + (target_y - ey) * t),
               random.uniform(0.07, 0.2))

    # Micro-settle onto the real target (0-3 tiny corrections).
    for _ in range(random.randint(0, 3)):
        _set_cursor(target_x + random.randint(-2, 2), target_y + random.randint(-2, 2))
        time.sleep(random.uniform(0.03, 0.09))
    _set_cursor(target_x, target_y)
    time.sleep(random.uniform(0.04, 0.14))


def human_click(x, y, clicks=1, interval=None, jitter=True):
    """Move along a human path, hesitate, then press/release with variable hold.
    clicks=2 / 3 / 4 for double / triple / quadruple click."""
    human_move(x, y, jitter=jitter)
    _sleep(random.uniform(0.08, 0.35))
    for n in range(max(1, int(clicks))):
        _failsafe_check()
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.12))
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        if n < clicks - 1:
            # Must stay well inside the Windows double-click time (500 ms).
            gap = interval if interval is not None else random.uniform(0.07, 0.16)
            time.sleep(min(0.25, gap * random.uniform(0.8, 1.2)))
    micro_pause()


def human_double_click(x, y, jitter=True):
    human_click(x, y, clicks=2, jitter=jitter)


def close_foreground_window(expected_hwnd=None):
    """Close a window by clicking its REAL title-bar Close button with the mouse
    (found via UI Automation), the way a person does. Falls back to a WM_CLOSE
    message if the button can't be found. Windows' normal close handling runs,
    so an unsaved-changes prompt still appears exactly as it would for a person.

    expected_hwnd: the window to close. If given and not in front, it is closed
    with WM_CLOSE so a click can never land on the wrong window."""
    human_pause(0.4, 1.2, think_prob=0)

    target = int(expected_hwnd) if expected_hwnd else int(user32.GetForegroundWindow() or 0)
    front = int(user32.GetForegroundWindow() or 0)

    # Only click when the intended window is actually in front.
    if target and target == front:
        try:
            import ui_find   # lazy: ui_find imports human_io, so avoid a cycle at load
            if ui_find.available() and ui_find.click_name(target, "Close", control_type="ButtonControl"):
                return
        except Exception:
            pass

    if target:
        user32.PostMessageW(target, WM_CLOSE, 0, 0)


# =====================================================================
# KEYBOARD
# =====================================================================

_WORD_PUNCT = set(".,;:!?")


def token_difficulty(token):
    """>1 means slow down. Numbers, symbols, formulas and long words are harder
    to type than ordinary prose."""
    if not token or token.isspace():
        return 1.0
    factor = 1.0
    core = token.strip(".,;:!?\"'()")
    if token.startswith("="):
        factor = 1.9                                  # spreadsheet formula
    elif core and re.fullmatch(r"[\d.,$%+\-]+", core):
        factor = 1.7                                  # numeric value
    elif any(c.isdigit() for c in token):
        factor = 1.5                                  # mixed, e.g. E4, 10:00, 2026
    elif re.search(r"[^A-Za-z.,;:!?'\"()\-]", token):
        factor = 1.35                                 # symbols: | & / @ ...
    if len(core) >= 10:
        factor *= 1.2                                 # long word
    return factor


def _press(key):
    check_emergency_stop()
    pyautogui.press(key, _pause=False)


def _write_char(ch):
    check_emergency_stop()
    if ch == "\n":
        pyautogui.press("enter", _pause=False)
    elif ch == "\t":
        pyautogui.press("tab", _pause=False)
    else:
        pyautogui.write(ch, _pause=False)


def _char_delay(speed):
    # Median ~0.15 s for ordinary prose; scaled up for harder content.
    return max(0.035, min(1.1, random.lognormvariate(math.log(0.15), 0.45) * speed))


_tempo = 1.0


def _drift_tempo():
    """Typing speed wanders from word to word (fast bursts, slow stretches)
    instead of holding one rhythm for the whole text. Mean-reverting walk."""
    global _tempo
    _tempo = max(0.65, min(1.6, 1.0 + (_tempo - 1.0) * 0.7 + random.gauss(0.0, 0.14)))
    return _tempo


# Keys either side on the same QWERTY row: a slipped finger hits one of these.
_ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm")
NEIGHBOURS = {row[i]: (row[i - 1] if i else "") + (row[i + 1] if i + 1 < len(row) else "")
              for row in _ROWS for i in range(len(row))}

# Words a writer may type, reconsider and replace with a plainer one. The
# replacement stays in the text (the person changed their mind).
SYNONYMS = {
    "difficult": "hard", "approximately": "about", "purchase": "buy", "purchased": "bought",
    "assist": "help", "begin": "start", "require": "need", "required": "needed",
    "obtain": "get", "sufficient": "enough", "additional": "extra", "currently": "now",
    "significant": "notable", "commence": "start", "utilise": "use", "utilize": "use",
    "numerous": "many", "regarding": "about", "therefore": "so", "rapidly": "quickly",
    "large": "big", "ensure": "make sure", "observed": "seen",
}

_WORD = re.compile(r"([\"'(\[]*)([A-Za-z]+)([^A-Za-z]*)")


def _slip(ch):
    """A neighbouring key for ch, keeping its case."""
    keys = NEIGHBOURS.get(ch.lower()) or ADJACENT_KEYS.get(ch.lower(), ch)
    wrong = random.choice(keys)
    return wrong.upper() if ch.isupper() else wrong


def _type_chars(chars, speed):
    for ch in chars:
        _write_char(ch)
        _sleep(_char_delay(speed))
        if ch in _WORD_PUNCT:
            _sleep(random.uniform(0.12, 0.45) * min(speed, 1.6))


def _backspace(n):
    for _ in range(n):
        _press("backspace")
        _sleep(random.uniform(0.04, 0.13))


def _notice():
    _sleep(random.uniform(0.3, 1.1))          # eyes catch the mistake


def _type_word_with_slip(word, speed):
    """Type one alphabetic word with a mistake that is then corrected, so the
    final text is exactly `word`. Kinds: one wrong key; a burst of 2-3 wrong
    keys; two letters swapped; a wrong FIRST letter not noticed until the word
    is finished, then fixed by retyping the word or by arrowing back to it."""
    n = len(word)
    kind = random.choices(["key", "burst", "swap", "start"], weights=[35, 25, 15, 25])[0]

    if kind == "start":
        _type_chars(_slip(word[0]) + word[1:], speed)       # e.g. 'qriter' for 'writer'
        _notice()
        if n > 9 or random.random() < 0.5:
            _backspace(n)                                    # wipe the word, type it again
            _sleep(random.uniform(0.15, 0.4))
            _type_chars(word, speed)
        else:
            for _ in range(n - 1):                           # arrow back to the bad letter
                _press("left")
                _sleep(random.uniform(0.05, 0.14))
            _press("backspace")
            _sleep(random.uniform(0.1, 0.3))
            _type_chars(word[0], speed)
            for _ in range(n - 1):                           # and back to the end
                _press("right")
                _sleep(random.uniform(0.04, 0.11))
        return

    i = random.randrange(0, n - 1)
    if kind == "swap":
        wrong = word[i + 1] + word[i]
    elif kind == "burst":
        k = min(random.randint(2, 3), n - i)
        wrong = "".join(_slip(c) for c in word[i:i + k])
    else:
        wrong = _slip(word[i])
    _type_chars(word[:i] + wrong, speed)
    extra = word[i + len(wrong):i + len(wrong) + random.randint(0, 2)]
    _type_chars(extra, speed)                                # keep going a moment...
    _notice()
    _backspace(len(wrong) + len(extra))                      # ...then back to the error
    _sleep(random.uniform(0.1, 0.3))
    _type_chars(word[i:], speed)


def _type_word_then_rephrase(word, speed):
    """Type `word`, reconsider, delete it and type a plainer synonym instead."""
    better = SYNONYMS[word.lower()]
    if word[0].isupper():
        better = better[0].upper() + better[1:]
    _type_chars(word, speed)
    _sleep(random.uniform(0.6, 1.8))                         # hmm, simpler word
    if random.random() < 0.35:
        pyautogui.hotkey("ctrl", "backspace", _pause=False)  # delete the whole word
        _sleep(random.uniform(0.15, 0.35))
    else:
        _backspace(len(word))
    _type_chars(better, speed)


def human_type(text, difficulty=1.0, typo_rate=0.06):
    """Type text with variable per-character delays, longer pauses at spaces and
    punctuation, and realistic mistakes (see _type_word_with_slip): one or more
    wrong keys, swapped letters, a wrong first letter noticed only at the end of
    the word, and now and then a word replaced by a plainer synonym.

    Content-aware: tokens containing digits / symbols, long words and formulas
    are typed more slowly and preceded by a short 'reading' pause.
    difficulty: optional hint that scales the overall speed (>1 = slower).
    typo_rate: per-word chance of a mistake in an alphabetic word (0 disables
    all mistakes and synonym swaps, e.g. for numbers in Calc).
    """
    text = str(text)
    hint = max(0.3, float(difficulty or 1.0))
    for token in re.split(r"(\s+)", text):
        if not token:
            continue
        if token.isspace():
            for ch in token:
                _write_char(ch)
                _sleep(_lognorm_between(0.06, 0.55) * min(hint, 1.5))
                if random.random() < 0.04:
                    _sleep(random.uniform(0.6, 1.8))   # brief hesitation mid-sentence
            continue

        speed = token_difficulty(token) * hint   # content difficulty only
        tempo = _drift_tempo()                   # per-word rhythm, applied to delays below
        if speed > 1.25:
            _sleep(random.uniform(0.25, 0.8) * speed)  # read it before typing it

        m = _WORD.fullmatch(token)
        if typo_rate and speed < 1.25 and m:
            lead, word, trail = m.groups()
            _type_chars(lead, speed * tempo)
            if word.lower() in SYNONYMS and random.random() < min(0.5, typo_rate * 4):
                _type_word_then_rephrase(word, speed * tempo)
            elif len(word) >= 3 and random.random() < typo_rate:
                _type_word_with_slip(word, speed * tempo)
            else:
                _type_chars(word, speed * tempo)
            _type_chars(trail, speed * tempo)
            continue

        _type_chars(token, speed * tempo)
