"""
market_capture - copy ONE real value (the live Bitcoin price) from the
CoinGecko page that web_tasks has just browsed, for use in the notes/report.

Additive and fail-safe: called by the orchestrator right after the
CoinGecko visit (Chrome still open and in front). If the live value cannot be verified, return None. The notes and report
then omit the unverified price instead of inserting a stale placeholder.

Clipboard is read with ctypes (standard library only), never written.
"""

import ctypes
import random
import re
import time
from ctypes import wintypes

import pyautogui

import human_io
import ui_find    # read the live Bitcoin price straight from the page (UI Automation)

# The price parser targets the Bitcoin/BTC row in CoinGecko's page text.
# No hard-coded BTC price: on failure, skip the live-price sentence.

# Plausibility window for a BTC/USD price.
MIN_BTC_USD, MAX_BTC_USD = 10_000, 500_000

CHROME_CLASS = "Chrome_WidgetWin_1"
CF_UNICODETEXT = 13

# Own DLL instances so these argtypes never leak into other modules.
_user32 = ctypes.WinDLL("user32")
_kernel32 = ctypes.WinDLL("kernel32")
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetSystemMetrics.argtypes = [ctypes.c_int]
_user32.OpenClipboard.argtypes = [wintypes.HWND]
_user32.OpenClipboard.restype = wintypes.BOOL
_user32.CloseClipboard.restype = wintypes.BOOL
_user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
_user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
_user32.GetClipboardData.argtypes = [wintypes.UINT]
_user32.GetClipboardData.restype = wintypes.HANDLE
_user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
_kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalLock.restype = ctypes.c_void_p
_kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalUnlock.restype = wintypes.BOOL


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] [MarketCapture] {msg}")


# =====================================================================
# WINDOW + CLIPBOARD HELPERS
# =====================================================================

def _foreground():
    return _user32.GetForegroundWindow()


def _is_chrome(hwnd):
    if not hwnd:
        return False
    buf = ctypes.create_unicode_buffer(256)
    _user32.GetClassNameW(hwnd, buf, 256)
    return buf.value == CHROME_CLASS


def _title(hwnd):
    n = _user32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    _user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def read_clipboard_text():
    """Unicode text on the clipboard, or '' (never raises)."""
    for _ in range(5):                      # Chrome may hold it for a moment
        if _user32.OpenClipboard(None):
            break
        time.sleep(0.1)
    else:
        return ""
    try:
        if not _user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return ""
        handle = _user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        ptr = _kernel32.GlobalLock(handle)
        if not ptr:
            return ""
        try:
            return ctypes.wstring_at(ptr)
        finally:
            _kernel32.GlobalUnlock(handle)
    except Exception:
        return ""
    finally:
        _user32.CloseClipboard()


def _copy_selection():
    """Ctrl+C, then return the clipboard text only if it actually changed."""
    before = _user32.GetClipboardSequenceNumber()
    pyautogui.hotkey("ctrl", "c")
    for _ in range(10):
        time.sleep(0.1)
        if _user32.GetClipboardSequenceNumber() != before:
            return read_clipboard_text()
    return ""


# =====================================================================
# PARSING
# =====================================================================

_MONEY = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+|\d{4,7})(\.\d+)?")


def _plausible(text):
    """'$67,412.35' -> '67,412' if it is a plausible BTC price, else None."""
    match = _MONEY.search(text or "")
    if not match:
        return None
    try:
        value = float(match.group(1).replace(",", "") + (match.group(2) or ""))
    except ValueError:
        return None
    if not MIN_BTC_USD <= value <= MAX_BTC_USD:
        return None
    return f"{round(value):,}"


def parse_selected_price(text):
    """The triple-click selection -> formatted price or None. A short selection
    is the price cell itself; a longer one (whole row) must mention Bitcoin."""
    text = (text or "").strip()
    if not text:
        return None
    if len(text) <= 60:
        return _plausible(text)
    return parse_page_price(text)


def parse_page_price(text):
    """Whole-page text -> the first plausible $ price shortly after 'Bitcoin'."""
    for hit in re.finditer(r"Bitcoin", text or ""):
        window = text[hit.end():hit.end() + 160]
        for money in _MONEY.finditer(window):
            value = _plausible(money.group(0))
            if value:
                return value
    return None


# =====================================================================
# MAIN ENTRY
# =====================================================================

def _capture_uia():
    """Read the BTC price from the CoinGecko table via UI Automation: find the
    'Bitcoin BTC' row, then the first plausible $ price cell next to it.
    No clipboard, no page-wide Ctrl+A. Returns a formatted price or None."""
    if not ui_find.available():
        return None
    hwnd = ui_find.foreground_hwnd()
    if not _is_chrome(hwnd) or "coingecko" not in _title(hwnd).lower():
        return None
    coin = ui_find.find(hwnd, name="Bitcoin BTC", control_type="DataItemControl",
                        contains=True, timeout=2.0)
    if coin is None:
        return None
    try:
        row = coin.GetParentControl()
        cells = row.GetChildren() if row is not None else []
    except Exception:
        cells = []
    for cell in cells:
        price = _plausible(ui_find.text_of(cell))   # range filter excludes mcap/volume
        if price:
            return price
    return None


def capture_bitcoin_price():
    """Attempt a live BTC/USD capture from open CoinGecko; return str or None.

    Tries UI Automation first (reads the price cell directly), then the clipboard
    method. None is safe: the caller omits the price sentence.
    """
    try:
        price = _capture_uia()
        if price:
            log(f"Captured Bitcoin price from CoinGecko (UIA): ${price}")
            return price
    except pyautogui.FailSafeException:
        raise
    except Exception as error:
        log(f"UIA capture failed: {error!r}")

    try:
        price = _capture()
        if price:
            log(f"Captured Bitcoin price from CoinGecko (clipboard): ${price}")
            return price
    except pyautogui.FailSafeException:
        raise
    except Exception as error:
        log(f"Capture failed: {error!r}")
    log("CoinGecko price not verified; omitting live-price sentence")
    return None


def parse_coingecko_page_price(text):
    """Locate the Bitcoin/BTC row before accepting any displayed dollar amount.

    The public home-page table contains a 'Bitcoin BTC' row followed by a price.
    A generic money regex alone could accidentally pick up market cap or volume.
    """
    if not text:
        return None
    # Browser's copied page text may contain tabs or newlines in table rows.
    # Require adjacent Bitcoin and BTC labels to avoid nearby unrelated prices.
    pattern = re.compile(r"\bBitcoin\s+BTC\s+(?:Buy\s+)?(\$\s?[\d,]+(?:\.\d+)?)", re.I)
    for match in pattern.finditer(text):
        price = _plausible(match.group(1))
        if price:
            return price
    # Coin details page may print Bitcoin / BTC Price / rank / USD price.
    detail = re.compile(r"\bBitcoin\s+BTC\s+Price\s+#?\d+\s+(\$\s?[\d,]+(?:\.\d+)?)", re.I)
    for match in detail.finditer(text):
        price = _plausible(match.group(1))
        if price:
            return price
    return None


def _capture():
    hwnd = _foreground()
    if not _is_chrome(hwnd):
        log("Chrome is not in front; no copy attempted")
        return None
    if "coingecko" not in _title(hwnd).lower():
        log(f"Unexpected page '{_title(hwnd)}'; skipping")
        return None

    human_io.human_pause(0.5, 1.2)
    pyautogui.press("home")
    human_io.human_pause(0.8, 1.4)

    # Do not click into the page: an arbitrary position may contain a link.
    # Browsing/scrolling has already interacted with the page. If Ctrl+A
    # selects the wrong content, price parsing fails safely (returns None).
    human_io.human_pause(0.2, 0.5)
    if not _is_chrome(_foreground()) or "coingecko" not in _title(_foreground()).lower():
        return None

    pyautogui.hotkey("ctrl", "a")
    human_io.human_pause(0.3, 0.6)
    page_text = _copy_selection()
    pyautogui.press("home")
    return parse_coingecko_page_price(page_text)


def price_sentence(price):
    """Sentence used in the documents."""
    return f"Bitcoin was trading at around ${price} at the time of writing."
