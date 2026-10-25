"""
Synthetic Human Agent - orchestrator (ONE process; run with pythonw.exe).

Imports the teammates' modules from DF/ and WL/ and calls their functions in
sequence. No python subprocesses are spawned, and every app is still launched
the way a person does (Start menu search / desktop icon double-click), so
ParentImage stays explorer.exe.

Scenarios: both run once per session, in random order.
  S1 Office Secretary   : meeting notes -> Calc salary -> browse + reimbursements -> net earnings
  S2 Financial Researcher: browse + research notes (2 passes) -> split-screen financial report

Emergency stop: hold Shift+Esc (a background watcher kills the process at once).
Second net: pyautogui FAILSAFE (slam the mouse into a screen corner).
"""

import ctypes
import math
import os
import random
import sys
import threading
import time
from ctypes import wintypes

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "DF"), os.path.join(HERE, "WL")]


# =====================================================================
# TUNABLE KNOBS
# =====================================================================

DEBUG = False        # True: progress goes to the console (run with python.exe). Never to disk.
CALIBRATION = False  # True: minimal between-stage pauses + per-stage timing report (implies DEBUG)

TARGET_MINUTES = 15  # whole session, start to "Session finished"

# --- Adaptive time budget -------------------------------------------------
# Only the pauses BETWEEN stages/scenarios are sized by the budget. At every
# such pause: slack = target - elapsed - (estimated remaining work x observed
# pace), shared across the remaining pauses by weight, then log-normal
# randomized and clamped to [floor, cap]. Work inside a stage is never touched.
#
# Estimated pure work per stage (s). Paste the dict printed by a CALIBRATION run.
STAGE_ESTIMATE_S = {
    "S1.1 meeting notes": 260,
    "S1.2 salary update": 50,
    "S1.3a Apple + reimbursement": 75,
    "S1.3b Amazon + reimbursement": 70,
    "S1.4 net earnings + save": 45,
    "S1 close Chrome": 5,
    "S2.1 research notes": 220,
    "S2.2 financial report": 330,
    "S2 close Chrome": 2,
}
DEFAULT_STAGE_ESTIMATE_S = 30

# pause kind: (share weight, randomized floor range s, cap s)
PAUSES = {
    "start":    (8.0,  (3.0, 6.0), 30.0),    # before the first scenario
    "stage":    (6.0,  (2.0, 4.0), 75.0),    # between stages
    "step":     (3.0,  (1.2, 2.5), 25.0),    # between two halves of a stage (S1.3a -> S1.3b, before closing Chrome)
    "scenario": (25.0, (4.0, 8.0), 120.0),   # between the two scenarios
}
PAUSE_SIGMA = 0.35
PACE_CLAMP = (0.6, 1.8)   # limits on (actual / estimated) work ratio used to rescale estimates

# Fixed small pauses INSIDE a stage (not budgeted): (median s, min s, max s)
INNER_PAUSE  = (3.0, 1.2, 8.0)    # between browsing and note-taking in S2.1
SWITCH_PAUSE = (1.4, 0.6, 4.0)    # hesitation before Alt+Tab

WINDOW_WAIT_S = 20   # extra wait for an app window AFTER the teammate's own fixed sleep (the floor)
STOP_POLL_S = 0.05   # Shift+Esc poll interval

# Explicit whitelisted URLs only (no random sampling).
S1_URLS = ["https://www.apple.com", "https://www.amazon.com"]
S2_URLS = ["https://www.coingecko.com", "https://apnews.com"]

WRITER = "OpenOffice Writer"   # window-title fragments
CALC = "OpenOffice Calc"
CHROME_CLASS = "Chrome_WidgetWin_1"


# =====================================================================
# LOGGER - every print() in every module lands here; silent unless DEBUG
# =====================================================================

DEBUG = DEBUG or CALIBRATION


class _Log:
    encoding = "utf-8"

    def __init__(self, stream):
        self._stream = stream

    def isatty(self):
        return False

    def write(self, text):
        if DEBUG and self._stream is not None:
            try:
                self._stream.write(text)
            except Exception:
                pass
        return len(text)

    def flush(self):
        if DEBUG and self._stream is not None:
            try:
                self._stream.flush()
            except Exception:
                pass


sys.stdout = _Log(sys.stdout)   # under pythonw these are None -> fully silent
sys.stderr = _Log(sys.stderr)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] [Orchestrator] {msg}")


import pyautogui  # noqa: E402  (after sys.path / logger setup)

import human_io              # noqa: E402  shared human-like input (repo root)
import market_capture        # noqa: E402  live BTC price copy (repo root)
import web_tasks             # noqa: E402  DF
import office_worker         # noqa: E402  WL
import spreadsheet_part1     # noqa: E402
import spreadsheet_part2     # noqa: E402
import spreadsheet_part3     # noqa: E402
import spreadsheet_part4     # noqa: E402
import research_notes_part1  # noqa: E402
import research_notes_part2  # noqa: E402
import financial_report      # noqa: E402

pyautogui.FAILSAFE = True


# =====================================================================
# WIN32 HELPERS (own user32 instance)
# =====================================================================

user32 = ctypes.WinDLL("user32")
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsZoomed.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.WindowFromPoint.argtypes = [wintypes.POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short

SW_RESTORE = 9
SW_MAXIMIZE = 3
WM_CLOSE = 0x0010
GA_ROOT = 2
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
VK_SHIFT, VK_CONTROL, VK_MENU, VK_ESCAPE, VK_LWIN = 0x10, 0x11, 0x12, 0x1B, 0x5B


def _title(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def foreground():
    return int(user32.GetForegroundWindow() or 0)


def windows_with(title_part):
    """Visible top-level windows whose title contains title_part."""
    found = []

    @WNDENUMPROC
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd) and title_part.lower() in _title(hwnd).lower():
            found.append(int(hwnd))
        return True

    user32.EnumWindows(cb, 0)
    return found


def is_chrome(hwnd):
    return bool(hwnd) and _class(hwnd) == CHROME_CLASS


def chrome_open():
    h = web_tasks.get_chrome_hwnd()
    return bool(h and user32.IsWindowVisible(h))


def wait_for_window(title_part, before, timeout):
    """Poll (0.5 s) for a new window containing title_part, or a matching foreground one."""
    end = time.time() + timeout
    while True:
        new = [h for h in windows_with(title_part) if h not in before]
        if new:
            return new[0]
        fg = foreground()
        if fg and title_part.lower() in _title(fg).lower():
            return fg
        if time.time() >= end:
            return None
        time.sleep(0.5)


def ensure_foreground(hwnd):
    """SetForegroundWindow, then a title-bar click if that point really belongs to hwnd."""
    if not hwnd or not user32.IsWindow(hwnd):
        return False
    if foreground() == hwnd:
        return True
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.6)
    if foreground() == hwnd:
        return True

    rect = wintypes.RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        x = rect.left + min(120, max(30, (rect.right - rect.left) // 2))
        y = max(rect.top + 12, 2)
        under = user32.GetAncestor(user32.WindowFromPoint(wintypes.POINT(x, y)), GA_ROOT)
        if int(under or 0) == hwnd:
            human_io.human_click(x, y)
            time.sleep(0.7)
    return foreground() == hwnd


def release_inputs():
    for vk in (VK_MENU, VK_CONTROL, VK_SHIFT, VK_LWIN):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


# =====================================================================
# EMERGENCY STOP - background watcher, Shift+Esc -> os._exit
# =====================================================================

def _stop_watcher():
    while True:
        if (user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) and (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000):
            release_inputs()
            os._exit(0)
        time.sleep(STOP_POLL_S)


# =====================================================================
# PAUSES, STAGES, APP SESSIONS
# =====================================================================

def pause(spec):
    """Small fixed-range pause INSIDE a stage (not budgeted)."""
    median, lo, hi = spec
    time.sleep(min(hi, max(lo, random.lognormvariate(math.log(median), PAUSE_SIGMA))))


class SkipStage(Exception):
    """A stage whose prerequisite failed earlier (e.g. Calc never opened)."""


def run_stage(name, fn):
    """One stage = one try/except, so a failure does not kill the session.
    Never swallows the emergency stop: FailSafeException is re-raised, and
    SystemExit (web_tasks' own Shift+Esc check) is a BaseException so it is
    never caught here. Shift+Esc normally ends the process via os._exit first."""
    log(f"--- {name}")
    try:
        fn()
        return "ok"
    except pyautogui.FailSafeException:
        raise
    except SkipStage as why:
        log(f"    {name} skipped: {why}")
        return "skipped"
    except Exception as error:
        log(f"!!! {name} FAILED: {error!r}")
        release_inputs()
        return "failed"


class Budget:
    """Sizes the between-stage pauses so the session ends close to TARGET_MINUTES."""

    def __init__(self, plan):
        self.plan = plan
        self.t0 = time.time()
        self.target = TARGET_MINUTES * 60.0
        self.done = []   # (name, status, seconds)

    def record(self, name, status, seconds):
        self.done.append((name, status, seconds))
        log(f"    {name}: {status} in {seconds:.0f}s (estimate {self._estimate(name):.0f}s)")

    @staticmethod
    def _estimate(name):
        return STAGE_ESTIMATE_S.get(name, DEFAULT_STAGE_ESTIMATE_S)

    def _pace(self):
        """Observed actual/estimated work ratio over successful stages so far."""
        actual = sum(s for _, st, s in self.done if st == "ok")
        est = sum(self._estimate(n) for n, st, _ in self.done if st == "ok")
        if est <= 0:
            return 1.0
        return min(PACE_CLAMP[1], max(PACE_CLAMP[0], actual / est))

    def pause_at(self, index):
        kind = self.plan[index]
        weight, floor_range, cap = PAUSES[kind]
        floor = random.uniform(*floor_range)

        if CALIBRATION:
            log(f"    pause[{kind}] {floor:.1f}s (calibration)")
            time.sleep(floor)
            return

        rest = self.plan[index + 1:]
        elapsed = time.time() - self.t0
        work_left = self._pace() * sum(self._estimate(item[0]) for item in rest if isinstance(item, tuple))
        weights_left = weight + sum(PAUSES[k][0] for k in rest if isinstance(k, str))
        slack = self.target - elapsed - work_left
        share = slack * weight / weights_left

        if share <= floor:
            seconds = floor   # behind schedule: shortest human-looking pause
        else:
            # Log-normal around the share; median shifted down so the MEAN equals the share.
            seconds = random.lognormvariate(math.log(share) - PAUSE_SIGMA ** 2 / 2, PAUSE_SIGMA)
            # Never start a pause that alone eats more than the whole remaining slack.
            seconds = max(floor, min(seconds, cap, slack))

        log(f"    pause[{kind}] {seconds:.1f}s  (elapsed {elapsed / 60:.1f} min, "
            f"work left ~{work_left / 60:.1f} min, slack {slack / 60:.1f} min)")
        time.sleep(seconds)

    def report(self):
        total = time.time() - self.t0
        log(f"Session finished in {total / 60:.1f} min (target {TARGET_MINUTES} min)")
        if CALIBRATION:
            work = sum(s for _, _, s in self.done)
            log(f"Pure stage work: {work / 60:.1f} min. Paste into STAGE_ESTIMATE_S:")
            for name, status, seconds in self.done:
                note = "" if status == "ok" else f"   # {status} - not a valid measurement"
                log(f'    "{name}": {seconds:.0f},{note}')


def open_app(open_fn, title_part, maximize=False):
    """Teammate's own launch (Start menu / desktop icon) + its fixed sleep as the
    floor, then wait for the window to really exist. Retry the launch once."""
    for attempt in (1, 2):
        before = set(windows_with(title_part))
        open_fn()
        hwnd = wait_for_window(title_part, before, WINDOW_WAIT_S)
        if hwnd:
            if maximize and not user32.IsZoomed(hwnd):
                # Window appeared after the teammate's Alt+Space,X - maximize it now.
                user32.ShowWindow(hwnd, SW_MAXIMIZE)
                time.sleep(1.0)
            ensure_foreground(hwnd)
            return hwnd
        log(f"{title_part} did not appear (attempt {attempt})")
        pyautogui.press("esc")   # dismiss a Start menu left open by a failed launch
        time.sleep(random.uniform(1.5, 3.0))
    raise RuntimeError(f"{title_part} did not open after a retry")


def alt_tab_to(is_target):
    pause(SWITCH_PAUSE)
    pyautogui.hotkey("alt", "tab")
    time.sleep(random.uniform(0.6, 1.0))
    return is_target(foreground())


def close_chrome_quietly():
    h = web_tasks.get_chrome_hwnd()
    if h and user32.IsWindowVisible(h):
        user32.PostMessageW(h, WM_CLOSE, 0, 0)
        time.sleep(1.5)


def close_chrome():
    """Close Chrome with the mouse (DF's routine) only if it is really in front."""
    if not chrome_open():
        return
    if is_chrome(foreground()) or ensure_foreground(web_tasks.get_chrome_hwnd()) or is_chrome(foreground()):
        web_tasks.close_chrome_with_mouse()
    else:
        close_chrome_quietly()


def hand_over_to_chrome():
    """Before browsing again with Chrome already open: Alt+Tab to it. If it can't
    be focused, close it - browse() then reopens it (desktop icon / Start menu). This prevents a
    URL being typed into Calc/Writer."""
    if not chrome_open() or is_chrome(foreground()):
        return
    if alt_tab_to(is_chrome):
        return
    ensure_foreground(web_tasks.get_chrome_hwnd())
    if is_chrome(foreground()):
        return
    log("Could not focus Chrome - closing it so it is relaunched cleanly")
    close_chrome_quietly()


def back_to(hwnd, name):
    """Return to an app window: Alt+Tab, then SetForegroundWindow, then close Chrome."""
    if foreground() == hwnd:
        return
    if alt_tab_to(lambda h: h == hwnd):
        return
    if ensure_foreground(hwnd):
        return
    log(f"Could not focus {name} - closing Chrome as fallback")
    close_chrome_quietly()
    if not ensure_foreground(hwnd):
        raise RuntimeError(f"Could not bring {name} to the front")


def show_desktop_if_covered():
    """Calc is opened by double-clicking the desktop icon - make sure it is visible."""
    if windows_with("OpenOffice") or chrome_open():
        pyautogui.hotkey("win", "d")
        time.sleep(random.uniform(1.0, 1.8))


# =====================================================================
# SCENARIO 1 - OFFICE SECRETARY
# =====================================================================

# A scenario is a PLAN: a list of ("stage name", function) tuples and pause
# kinds (strings, see PAUSES). The Budget needs the whole plan up front to
# know how much work and how many pauses remain.

def scenario1_office_secretary():
    ctx = {}

    def need_calc():
        if not ctx.get("calc"):
            raise SkipStage("Calc never opened")

    # Stage 1: Writer meeting notes -> save -> close
    def stage1():
        open_app(office_worker.open_openoffice_writer, WRITER, maximize=True)
        office_worker.type_document()
        office_worker.save_document()
        office_worker.close_writer()

    # Stage 2: open Calc (stays open through Stage 4) -> salary + summary
    def stage2():
        show_desktop_if_covered()
        ctx["calc"] = open_app(spreadsheet_part1.open_spreadsheet, CALC)
        spreadsheet_part1.update_salary()

    # Stage 3: browse Apple -> Calc (apple row) -> browse Amazon -> Calc (SSD row)
    #          Chrome stays open; focus is switched back to Calc with Alt+Tab.
    def stage3a():
        need_calc()
        web_tasks.browse_hardware_procurement(urls=[S1_URLS[0]], close_when_done=False)
        back_to(ctx["calc"], "Calc")
        spreadsheet_part2.part2_apple_laptop()

    def stage3b():
        need_calc()
        hand_over_to_chrome()
        web_tasks.browse_hardware_procurement(urls=[S1_URLS[1]], close_when_done=False)
        back_to(ctx["calc"], "Calc")
        spreadsheet_part3.part3_external_ssd()

    # Stage 4: Summary net earnings -> save -> close Calc (part4 does save + close)
    def stage4():
        need_calc()
        back_to(ctx["calc"], "Calc")
        spreadsheet_part4.part4_finish()

    return [
        ("S1.1 meeting notes", stage1),
        "stage",
        ("S1.2 salary update", stage2),
        "stage",
        ("S1.3a Apple + reimbursement", stage3a),
        "step",
        ("S1.3b Amazon + reimbursement", stage3b),
        "stage",
        ("S1.4 net earnings + save", stage4),
        "step",
        ("S1 close Chrome", close_chrome),
    ]


# =====================================================================
# SCENARIO 2 - FINANCIAL RESEARCHER
# =====================================================================

def scenario2_financial_researcher():
    ctx = {}   # in-memory handoff (replaces research_notes_session.json)

    # Stage 1: CoinGecko (+ attempt live BTC price capture) -> notes pass 1 -> AP News -> notes pass 2
    def stage1():
        web_tasks.browse_market_intelligence(urls=[S2_URLS[0]], close_when_done=False)
        ctx["btc_price"] = market_capture.capture_bitcoin_price()   # None if live price cannot be verified

        # Click into the live data like a person: open Bitcoin's page, read it,
        # then go back. Non-fatal: any failure just skips the interaction.
        try:
            if web_tasks.click_coin_row("Bitcoin"):
                pause(INNER_PAUSE)
                web_tasks.go_back()
                pause(INNER_PAUSE)
        except pyautogui.FailSafeException:
            raise
        except Exception as error:
            log(f"coin-row interaction skipped: {error!r}")

        pause(INNER_PAUSE)
        ctx["notes_hwnd"] = open_app(research_notes_part1.open_openoffice_writer, WRITER, maximize=True)
        ctx["topic"] = research_notes_part1.type_document(btc_price=ctx["btc_price"])
        notes_file = research_notes_part1.save_document()            # e.g. "Research Notes.odt"
        ctx["notes_name"] = os.path.splitext(notes_file)[0]          # matches title with or without .odt
        pause(INNER_PAUSE)

        hand_over_to_chrome()
        web_tasks.browse_market_intelligence(urls=[S2_URLS[1]], close_when_done=False)

        # Open a story, highlight a useful paragraph with the mouse and copy it
        # for the notes. Non-fatal: without an excerpt the notes are typed only.
        excerpt = None
        try:
            if web_tasks.click_news_headline():
                pause(INNER_PAUSE)
                web_tasks.human_scroll(ticks=-random.randint(2, 4))
                web_tasks.read_with_mouse()
            excerpt = web_tasks.highlight_and_copy_paragraph()
        except pyautogui.FailSafeException:
            raise
        except Exception as error:
            log(f"news excerpt skipped: {error!r}")
        pause(INNER_PAUSE)
        close_chrome()

        if not ensure_foreground(ctx["notes_hwnd"]):
            raise RuntimeError("Could not bring Research Notes back to the front")
        research_notes_part2.run_research_notes_part2(ctx["topic"], ctx["notes_name"], excerpt=excerpt)

    # Stage 2: second Writer, split screen, topic-matched report -> save -> close both
    def stage2():
        if "notes_name" not in ctx:
            raise SkipStage("no research notes were saved")
        financial_report.run_financial_report(ctx["topic"], ctx["notes_name"], ctx["notes_hwnd"],
                                              btc_price=ctx.get("btc_price"))

    return [
        ("S2.1 research notes", stage1),
        "stage",
        ("S2.2 financial report", stage2),
        ("S2 close Chrome", close_chrome),   # no-op unless a failure left Chrome open
    ]


# =====================================================================
# MAIN
# =====================================================================

def main():
    threading.Thread(target=_stop_watcher, name="stop-watcher", daemon=True).start()

    scenarios = [scenario1_office_secretary, scenario2_financial_researcher]
    random.shuffle(scenarios)
    plan = ["start"] + scenarios[0]() + ["scenario"] + scenarios[1]()
    log("Order: " + " -> ".join(s.__name__ for s in scenarios))

    # OpenOffice exposes its controls to UI Automation only if an assistive tool
    # is reported when it STARTS, so switch the flag on before any app opens.
    import ui_find
    reader_was_on = ui_find.set_screen_reader_flag(True)
    log(f"Screen-reader flag on (was {'on' if reader_was_on else 'off'})")

    budget = Budget(plan)
    try:
        for index, item in enumerate(plan):
            if isinstance(item, str):
                budget.pause_at(index)
                continue
            name, fn = item
            t0 = time.time()
            status = run_stage(name, fn)
            budget.record(name, status, time.time() - t0)
    except pyautogui.FailSafeException:
        log("FAILSAFE (mouse in screen corner) - stopping")
        release_inputs()
        return
    finally:
        if not reader_was_on:
            ui_find.set_screen_reader_flag(False)

    budget.report()


if __name__ == "__main__":
    main()
