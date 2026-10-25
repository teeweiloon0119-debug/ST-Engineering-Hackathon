"""
ui_find - locate real UI controls with Windows UI Automation (the `uiautomation`
package) and click them with the human-like mouse in human_io.

Two lookups:
- find(): uiautomation's own search. NOTE it is NOT native FindFirst: the library
  walks the whole subtree depth-first in Python and only checks the timeout
  after a full pass. Fine for Chrome and the desktop.
- find_office(): a bounded breadth-first walk for OpenOffice. It does not descend
  into the document / cell grid (Calc's grid alone can stall a full walk), matches
  names loosely ("Bold (Ctrl+B)" == "Bold") and accepts several control types,
  because OpenOffice exposes the Name Box and Font Size as COMBO boxes, not edits.

Every click lands on a random point inside the control's CURRENT rectangle, so
no screen position is hardcoded. Lookups return None / False when a control is
not found, and callers keep a fallback, so a missing control never stops a run.
Each OpenOffice lookup prints why it succeeded or failed (visible with DEBUG).

OpenOffice exposes its control tree only while its window is IN FRONT, so helpers
that act on OpenOffice locate the window by title and bring it forward first
(window_by_title + ensure_foreground).
"""

import ctypes
import random
import time
from collections import deque
from ctypes import wintypes

import human_io

try:
    import uiautomation as auto
except Exception:            # library missing -> every lookup returns None, callers fall back
    auto = None

if auto is not None:
    try:
        auto.uiautomation.SetGlobalSearchTimeout(2)
    except Exception:
        pass

_WHOLE_SUBTREE = 0xFFFFFFFF

# Own user32 instance; argtypes set by other modules must not leak in here.
user32 = ctypes.WinDLL("user32")
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
_WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]

MOUSEEVENTF_WHEEL = 0x0800
SW_RESTORE = 9


def available():
    """True when the uiautomation library imported."""
    return auto is not None


# =====================================================================
# ACCESSIBILITY SWITCH (must be on BEFORE OpenOffice starts)
# =====================================================================
# OpenOffice only builds its accessibility tree (toolbar, document, cells) when
# Windows reports an assistive tool. Without it UIA sees just the window frame
# (title bar + caption buttons). The flag below is that report. It is set
# without SPIF_UPDATEINIFILE, so it is not saved and reverts at logoff.

SPI_GETSCREENREADER = 0x0046
SPI_SETSCREENREADER = 0x0047
SPIF_SENDCHANGE = 0x0002
user32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]


def screen_reader_flag():
    value = wintypes.BOOL()
    user32.SystemParametersInfoW(SPI_GETSCREENREADER, 0, ctypes.byref(value), 0)
    return bool(value.value)


def set_screen_reader_flag(on):
    """Set the 'screen reader present' flag. Returns its previous state."""
    previous = screen_reader_flag()
    user32.SystemParametersInfoW(SPI_SETSCREENREADER, 1 if on else 0, None, SPIF_SENDCHANGE)
    return previous


# =====================================================================
# WINDOWS BY TITLE + FOREGROUND
# =====================================================================

def foreground_hwnd():
    return int(user32.GetForegroundWindow() or 0)


def _title(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def window_by_title(fragment):
    """HWND of the first visible top-level window whose title contains fragment,
    or 0. Preferred over 'whatever is in front', which can be racy."""
    found = []

    @_WNDENUMPROC
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd) and fragment.lower() in _title(hwnd).lower():
            found.append(int(hwnd))
        return True

    user32.EnumWindows(cb, 0)
    return found[0] if found else 0


_VK_MENU = 0x12
_KEYEVENTF_KEYUP = 0x0002


def ensure_foreground(hwnd):
    """Bring hwnd to the front (OpenOffice only exposes its controls while in
    front). Returns True if it is in front afterwards.

    Windows blocks SetForegroundWindow from a process that doesn't own the
    current foreground. A tap of the Alt key clears that lock, which is the
    standard workaround, so the agent can reliably raise its own windows."""
    if not hwnd:
        return False
    for _ in range(3):
        if foreground_hwnd() == int(hwnd):
            return True
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        # Alt down/up to release the foreground lock, then raise the window.
        user32.keybd_event(_VK_MENU, 0, 0, 0)
        user32.keybd_event(_VK_MENU, 0, _KEYEVENTF_KEYUP, 0)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
    return foreground_hwnd() == int(hwnd)


# =====================================================================
# FINDING CONTROLS (native uiautomation descendant search)
# =====================================================================

def _window_control(hwnd):
    if auto is None or not hwnd:
        return None
    try:
        return auto.ControlFromHandle(int(hwnd))
    except Exception:
        return None


def _finder(root, control_type):
    """The uiautomation method that searches for a given control type
    (method name == type name, e.g. 'EditControl'). Falls back to generic."""
    if control_type:
        meth = getattr(root, control_type, None)
        if meth is not None:
            return meth
    return lambda **kw: auto.Control(searchFromControl=root, **kw)


def _props(name, contains, class_name, found_index=1, depth=_WHOLE_SUBTREE):
    props = {"searchDepth": depth, "foundIndex": found_index}
    if name is not None:
        props["SubName" if contains else "Name"] = name
    if class_name is not None:
        props["ClassName"] = class_name
    return props


def find(root_hwnd, name=None, control_type=None, contains=False, class_name=None,
         depth=_WHOLE_SUBTREE, timeout=3.0):
    """First descendant of a window matching the filters, via native FindFirst.

    name: exact Name, or a substring when contains=True.
    control_type: e.g. 'ButtonControl', 'EditControl', 'TabItemControl'.
    class_name: exact ClassName (disambiguates, e.g. Chrome's caption Close
    'WindowsCaptionButton' vs a tab's 'TabCloseButton'). Returns control or None.
    """
    root = _window_control(root_hwnd)
    if root is None:
        return None
    try:
        ctl = _finder(root, control_type)(**_props(name, contains, class_name, depth=depth))
        if ctl.Exists(timeout, 0.3):
            return ctl
    except Exception:
        return None
    return None


def find_all(root_hwnd, name=None, control_type=None, contains=True, class_name=None,
             depth=_WHOLE_SUBTREE, limit=25):
    """Up to `limit` matching descendants (native search, increasing foundIndex)."""
    root = _window_control(root_hwnd)
    if root is None:
        return []
    out = []
    for i in range(1, limit + 1):
        try:
            ctl = _finder(root, control_type)(**_props(name, contains, class_name, found_index=i, depth=depth))
            if not ctl.Exists(0.5, 0.2):
                break
        except Exception:
            break
        out.append(ctl)
    return out


# Containers find_office() does not walk into: the text / cell content of a
# document, where none of the toolbar controls live.
OFFICE_SKIP_INTO = ("DocumentControl", "TableControl", "DataGridControl")


def _norm(text):
    """Lower-case name without mnemonic marks or a trailing '(Ctrl+B)' hint."""
    t = (text or "").replace("~", "").replace("&", "").strip().lower()
    cut = t.find("(")
    return t[:cut].strip() if cut > 0 else t


def find_office(root_hwnd, names=None, control_types=None, skip_into=OFFICE_SKIP_INTO,
                timeout=4.0, max_nodes=2500, max_children=300, label=None, class_name=None):
    """First visible descendant whose (normalized) Name is in `names` and whose
    ControlTypeName is in `control_types` (None = any), by a bounded
    breadth-first walk that never enters `skip_into` containers. Re-walks until
    `timeout`, because OpenOffice builds its accessible tree lazily on first
    query. Returns the control or None."""
    root = _window_control(root_hwnd)
    label = label or (names[0] if names else str(control_types))
    if root is None:
        print(f"[uia] {label}: no window / uiautomation unavailable")
        return None
    wanted = {_norm(n) for n in names} if names else None
    types = set(control_types) if control_types else None
    deadline = time.time() + timeout
    seen = 0
    near = []   # name matched but type/rect did not: printed to explain a miss
    while True:
        seen = 0
        queue = deque([(root, 0)])
        while queue and seen < max_nodes and time.time() < deadline:
            ctl, depth = queue.popleft()
            try:
                ctype = ctl.ControlTypeName
                if depth > 0:
                    seen += 1
                    if wanted is None or _norm(ctl.Name) in wanted:
                        if (types is None or ctype in types) and rect_of(ctl) \
                                and (class_name is None or ctl.ClassName == class_name):
                            print(f"[uia] {label}: found {ctype} {ctl.Name!r} {rect_of(ctl)} "
                                  f"after {seen} controls")
                            return ctl
                        if wanted is not None and len(near) < 5:
                            near.append(f"{ctype} {ctl.Name!r} rect={rect_of(ctl)}")
                    if ctype in skip_into:
                        continue
                child = ctl.GetFirstChildControl()
                n = 0
                while child is not None and n < max_children:
                    queue.append((child, depth + 1))
                    n += 1
                    child = child.GetNextSiblingControl()
            except Exception:
                continue
        if time.time() + 0.5 >= deadline:
            break
        time.sleep(0.5)
    print(f"[uia] {label}: NOT found (walked {seen} controls)"
          + (f"; same name but wrong type/off-screen: {near}" if near else ""))
    return None


def visible_controls(container, control_types, accept=None, limit=40, max_nodes=2500, timeout=4.0,
                     center_only=False):
    """Controls of the given types that are on screen inside `container` (e.g.
    a web page), in reading order. Depth-first, but subtrees whose rectangle
    lies completely outside the container's visible area are skipped, so a long
    page costs only what is on screen. accept(control, rect) can filter more.
    center_only: a control counts once its centre is in view (web links: big
    tiles and links cut by the window edge are still clickable)."""
    view = rect_of(container)
    if view is None:
        return []
    # A web page may report its full (scrollable) height: only the part that
    # is actually on the screen counts as visible.
    sw, sh = _screen_size()
    view = (max(view[0], 0), max(view[1], 0), min(view[2], sw), min(view[3], sh))
    if view[2] <= view[0] or view[3] <= view[1]:
        return []
    types = set(control_types)
    deadline = time.time() + timeout
    found, seen = [], 0
    stack = [container]
    while stack and len(found) < limit and seen < max_nodes and time.time() < deadline:
        ctl = stack.pop()
        try:
            children = []
            child = ctl.GetFirstChildControl()
            while child is not None and len(children) < 400:
                children.append(child)
                child = child.GetNextSiblingControl()
        except Exception:
            continue
        for child in reversed(children):          # reversed: pop() keeps page order
            seen += 1
            r = rect_of(child)
            if r and (r[2] <= view[0] or r[0] >= view[2] or r[3] <= view[1] or r[1] >= view[3]):
                continue                          # off screen: skip it and everything inside
            stack.append(child)
        for child in children:
            try:
                r = rect_of(child)
                if not r or child.ControlTypeName not in types:
                    continue
                if center_only:
                    cx, cy = (r[0] + r[2]) // 2, (r[1] + r[3]) // 2
                    inside = view[0] <= cx < view[2] and view[1] <= cy < view[3]
                else:
                    inside = r[0] >= view[0] and r[2] <= view[2] and r[1] >= view[1] and r[3] <= view[3]
                if inside and (accept is None or accept(child, r)):
                    found.append(child)
            except Exception:
                continue
    return found[:limit]


def text_block_rect(container, text, max_nodes=120):
    """On-screen rect of the text block (paragraph) inside a document control
    that shows `text`: the one whose Name contains its start, else the topmost
    line-sized block. Bounded walk of the container only. Returns rect or None."""
    box = rect_of(container)
    if box is None:
        return None
    key = _norm(text)[:12]
    by_name, topmost = None, None
    queue = deque([container])
    seen = 0
    while queue and seen < max_nodes:
        ctl = queue.popleft()
        try:
            child = ctl.GetFirstChildControl()
            while child is not None and seen < max_nodes:
                seen += 1
                r = rect_of(child)
                if r and box[0] <= r[0] and r[2] <= box[2] + 2 and box[1] <= r[1] < box[3] \
                        and 8 <= r[3] - r[1] <= 150:
                    if key and key in _norm(child.Name):
                        by_name = by_name or r
                    if topmost is None or r[1] < topmost[1]:
                        topmost = r
                if child.ControlTypeName not in ("TableControl", "DataGridControl"):
                    queue.append(child)
                child = child.GetNextSiblingControl()
        except Exception:
            continue
    rect = by_name or topmost
    print(f"[uia] text block {text[:20]!r}: "
          + (f"{'by name' if by_name else 'topmost'} {rect}" if rect else f"NOT found ({seen} controls)"))
    return rect


def text_field_rect(control):
    """Rect to click to TYPE into an edit or combo box. A combo's own rect
    includes its drop-down arrow, so use its Edit child, or else its left 70%."""
    if control is None:
        return None
    try:
        if control.ControlTypeName == "ComboBoxControl":
            child = control.GetFirstChildControl()
            while child is not None:
                if child.ControlTypeName == "EditControl" and rect_of(child):
                    return rect_of(child)
                child = child.GetNextSiblingControl()
            r = rect_of(control)
            if r:
                return (r[0], r[1], r[0] + max(4, int((r[2] - r[0]) * 0.7)), r[3])
    except Exception:
        pass
    return rect_of(control)


def control_at(x, y):
    """The control under a screen point (UIA ElementFromPoint), or None."""
    if auto is None:
        return None
    try:
        return auto.ControlFromPoint(int(x), int(y))
    except Exception:
        return None


def rect_of(control):
    """(left, top, right, bottom) or None. Off-screen/zero rect returns None."""
    try:
        r = control.BoundingRectangle
    except Exception:
        return None
    if r is None or r.right <= r.left or r.bottom <= r.top:
        return None
    return (r.left, r.top, r.right, r.bottom)


def text_of(control):
    try:
        return control.Name or ""
    except Exception:
        return ""


# =====================================================================
# CLICKING A CONTROL WITH THE HUMAN MOUSE
# =====================================================================

def _random_point_in(rect, margin=0.22):
    left, top, right, bottom = rect
    w, h = right - left, bottom - top
    mx, my = int(w * margin), int(h * margin)
    x = random.randint(left + mx, right - mx) if w > 2 * mx + 1 else (left + right) // 2
    y = random.randint(top + my, bottom - my) if h > 2 * my + 1 else (top + bottom) // 2
    return x, y


def _screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def _on_screen(rect):
    sw, sh = _screen_size()
    cx, cy = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
    return 0 <= cx < sw and 0 <= cy < sh


def _scroll(ticks):
    direction = 1 if ticks > 0 else -1
    for _ in range(abs(ticks)):
        human_io.check_emergency_stop()
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, direction * 120, 0)
        time.sleep(random.uniform(0.08, 0.2))


def scroll_into_view(control, tries=12):
    """Wheel-scroll (like a person) until the control's rect is on screen."""
    rect = rect_of(control)
    if rect and _on_screen(rect):
        return rect
    _, sh = _screen_size()
    for _ in range(tries):
        rect = rect_of(control)
        if rect and _on_screen(rect):
            return rect
        if not rect:
            _scroll(-3)
        else:
            mid = (rect[1] + rect[3]) // 2
            _scroll(-4 if mid > sh else 4)
        human_io.human_pause(0.3, 0.9, think_prob=0)
    rect = rect_of(control)
    return rect if rect and _on_screen(rect) else None


def click(control, double=False):
    """Move to a random point inside the control and click, scrolling it into
    view first. Returns True on success, False if it could not be reached."""
    if control is None:
        return False
    rect = scroll_into_view(control)
    if rect is None:
        return False
    return click_rect(rect, double=double)


def click_rect(rect, double=False):
    """Human click on a random point inside a screen rect. Returns True/False."""
    if not rect or not _on_screen(rect):
        return False
    x, y = _random_point_in(rect)
    if double:
        human_io.human_double_click(x, y)
    else:
        human_io.human_click(x, y)
    return True


def click_text_field(control):
    """Click into the typing area of an edit / combo box (see text_field_rect)."""
    return click_rect(text_field_rect(control))


def click_name(hwnd, name, control_type=None, contains=False, class_name=None, double=False):
    """Find a control by name under a window and click it. Returns True/False."""
    return click(find(hwnd, name=name, control_type=control_type, contains=contains,
                      class_name=class_name), double=double)


def confirm_replace_if_asked(timeout=5.0):
    """Call right after pressing Enter in a Save As dialog. If a 'file already
    exists - replace it?' prompt comes up, click its Yes button with the mouse
    (keyboard Alt+Y if UIA can't see it). Returns True if a prompt was answered."""
    start = time.time()
    while time.time() - start < timeout:
        hwnd = foreground_hwnd()
        title = _title(hwnd)
        if "OpenOffice" in title:
            if time.time() - start > 1.5:     # back in the document: saved, no prompt
                return False
        elif hwnd and title != "Save As":     # some other dialog is in front
            yes = find_office(hwnd, names=["Yes"], control_types=["ButtonControl"],
                              timeout=0.8, label="replace prompt Yes") if auto else None
            if yes is not None and click(yes):
                return True
            if "confirm" in title.lower() or "replace" in title.lower():
                human_io.human_pause(0.3, 0.8, think_prob=0)
                import pyautogui
                pyautogui.hotkey("alt", "y")
                return True
        time.sleep(0.3)
    return False


def click_desktop_icon(name, contains=True, double=True):
    """Double-click a desktop icon by name (a ListItemControl under the shell's
    'Program Manager' window). Returns True/False."""
    if auto is None:
        return False
    progman = int(user32.FindWindowW("Progman", None) or 0)
    if not progman:
        return False
    return click(find(progman, name=name, control_type="ListItemControl", contains=contains),
                 double=double)


# =====================================================================
# QUICK VM CHECK:  py ui_find.py  (run with Calc in front)
# =====================================================================

if __name__ == "__main__":
    if auto is None:
        print("uiautomation is not installed.")
        raise SystemExit(1)
    hwnd = window_by_title("OpenOffice Calc") or foreground_hwnd()
    print("target window:", hwnd, repr(_title(hwnd)))
    ensure_foreground(hwnd)
    for nm in ("Name Box", "Bold", "Summary"):
        find_office(hwnd, names=[nm])
