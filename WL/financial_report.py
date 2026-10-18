#!/usr/bin/env python3
"""FINANCIAL REPORT — STAGE 3 (OpenOffice Writer, Windows VM)

Run AFTER Research_Notes_Part1_CoinMarketCap.py and
Research_Notes_Part2_APNews.py, while the Research Notes Writer window is OPEN.

- Reads the selected topic from Desktop/research_notes_session.json.
- Creates a NEW Writer document via the Windows Start menu (not Ctrl+N).
- Puts Research Notes on the left and Financial Report on the right.
- Types a topic-matched report with the same typing/typo behavior as Scenario 1.
- Saves the report to Desktop as Financial_Report1.odt (or next available).
- Closes both Writer documents with the mouse after saving.

This file is standalone. It does not import either Research Notes Python script.
"""

import ctypes
from ctypes import wintypes
import json
import os
import random
import time

import pyautogui


# ============================================================
# SETTINGS — SAME AS YOUR ORIGINAL SCENARIO 1
# ============================================================

START_DELAY = 5
APP_LOAD_DELAY = 5

MIN_CHAR_DELAY = 0.07
MAX_CHAR_DELAY = 0.20
MIN_WORD_PAUSE = 0.08
MAX_WORD_PAUSE = 0.40
TYPO_PROBABILITY = 0.07
MIN_CORRECTION_PAUSE = 0.35
MAX_CORRECTION_PAUSE = 1.00
MIN_PARAGRAPH_PAUSE = 1.5
MAX_PARAGRAPH_PAUSE = 4.0

pyautogui.FAILSAFE = True

DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
SESSION_FILE = os.path.join(DESKTOP, 'research_notes_session.json')


# ============================================================
# REPORTS — MATCH THE 10 OPTIONS IN RESEARCH NOTES PART 1
# No dates or invented live prices.
# ============================================================

REPORTS = [
    {
        'topic': 'Market Research',
        'summary': 'This report reviews broad cryptocurrency activity together with the economic themes considered in the accompanying research notes. The objective is to identify the principal indicators and risks, rather than to predict short-term market returns.',
        'market': 'Bitcoin and Ethereum are useful reference assets because they have prominent positions within cryptocurrency markets. Market capitalization provides a measure of relative size, while daily percentage changes and trading volume indicate recent activity. These measures should be interpreted together rather than used as stand-alone signals.',
        'news': 'The research notes refer to AP News coverage of United States equities, inflation and interest-rate expectations. These subjects are relevant because changes in financing costs and investor confidence may affect demand for risk-sensitive assets. However, the notes do not establish a measured relationship between individual headlines and cryptocurrency returns.',
        'assessment': 'The principal risks include abrupt price movements, uncertain liquidity conditions and shifts in the economic outlook. Daily market data may reflect temporary sentiment rather than a durable trend. Comparisons should therefore use consistent time periods and distinguish observed changes from interpretation.',
        'recommendation': 'Continue tracking the major cryptocurrency indicators alongside reputable financial news. A subsequent report should add verified, time-stamped market figures before reaching any numerical performance conclusion. On the available notes, a cautious and evidence-led assessment is appropriate.'
    },
    {
        'topic': 'Bitcoin Market',
        'summary': 'This report evaluates Bitcoin market activity using the indicators identified in the research notes, supported by a review of relevant economic and financial news. It focuses on monitoring conditions and risk rather than making a price forecast.',
        'market': 'Bitcoin price movements and reported trading volume can help describe short-term participation in the market. A larger trading volume can accompany either buying or selling pressure; it is not, by itself, evidence that a price trend will persist. Market capitalization offers useful context for the size of the asset.',
        'news': 'The AP News component of the notes concerns economic developments that may affect investor appetite for risk. Inflation, interest-rate expectations and broader equity-market conditions can all be relevant background factors. Their effect on Bitcoin should not be assumed without supporting market evidence.',
        'assessment': 'Bitcoin remains exposed to substantial volatility and rapid changes in sentiment. A short period of positive or negative performance may be misleading if trading conditions are unusually thin or driven by a single headline. Position sizing and liquidity considerations are therefore important.',
        'recommendation': 'Monitor price movements, volume and market context over a consistent period. Check reputable financial headlines before interpreting abrupt changes, and avoid treating a single session as a reliable indicator of long-term direction.'
    },
    {
        'topic': 'Ethereum Market',
        'summary': 'This report considers Ethereum in comparison with Bitcoin, with attention to market size, trading activity and the wider environment for digital assets. It builds on the qualitative observations in the research notes.',
        'market': 'Market capitalization helps compare the relative scale of Ethereum and Bitcoin, while daily performance and trading volume provide a snapshot of their respective activity. Differences across these indicators do not by themselves establish whether either asset is fairly valued or likely to outperform.',
        'news': 'Financial conditions and technology-related developments can influence investor views toward digital assets. The research notes use AP News for broader market context rather than as a direct source of Ethereum pricing. This distinction matters when making causal claims.',
        'assessment': 'Ethereum may experience large and rapid price fluctuations even when its overall market capitalization is substantial. The assessment should also distinguish asset-specific developments from market-wide changes in risk appetite. Neither factor can be measured fully from the brief notes alone.',
        'recommendation': 'Compare Ethereum and Bitcoin using time-matched price, market-capitalization and trading-volume data. Keep news commentary separate from observed numerical trends, and update conclusions only when reliable figures are available.'
    },
    {
        'topic': 'Financial Markets',
        'summary': 'This report provides a cross-market overview of cryptocurrency indicators and the broader financial environment. The purpose is to connect market observations with relevant macroeconomic context while recognizing the limits of the available research.',
        'market': 'Cryptocurrency rankings, daily percentage changes and trading volume show how digital-asset markets are evolving. Relative rankings describe market size rather than the attractiveness of an investment. Short-term performance should therefore be viewed as only one element of a broader assessment.',
        'news': 'AP News coverage of United States stock markets and economic events provides a useful perspective on market confidence. Equities and digital assets may both respond to shifts in investor expectations, but their valuation frameworks and sensitivities are not identical.',
        'assessment': 'Cross-market comparisons can be misleading when they use different time periods or overlook asset-specific risks. Volatility, liquidity and uncertainty about policy developments should be considered explicitly. Current notes do not include sufficient data for statistical conclusions.',
        'recommendation': 'Maintain a consistent record of daily observations from both market-data and news sources. Separate facts from interpretations and review any conclusions after additional evidence becomes available.'
    },
    {
        'topic': 'Inflation and Markets',
        'summary': 'This report examines how inflation-related developments may inform a financial-market assessment, using cryptocurrency activity as a reference for risk-sensitive market behavior.',
        'market': 'Cryptocurrency prices can change rapidly during periods of economic uncertainty. Trading volume and daily movements provide an initial description of activity but cannot confirm which macroeconomic variable caused a particular movement. That limitation should remain explicit in the analysis.',
        'news': 'Inflation reports, energy costs and borrowing conditions can influence expectations for interest-rate policy. Such expectations may affect financing costs, consumer spending and asset valuations. AP News coverage is used here as background context, not as a substitute for official economic statistics.',
        'assessment': 'An unexpected inflation outcome could increase uncertainty regarding future rates and market valuations. However, the direction and magnitude of asset-price responses depend on what investors previously expected and on other prevailing conditions.',
        'recommendation': 'Track official inflation releases alongside reputable financial reporting and time-stamped price data. Avoid claiming that any single cryptocurrency movement was caused by inflation without corroborating evidence.'
    },
    {
        'topic': 'Energy and Market Conditions',
        'summary': 'This report considers energy-market news alongside cryptocurrency trading activity to evaluate broader economic risks. The analysis is qualitative and does not estimate the future direction of oil or digital-asset prices.',
        'market': 'Changes in cryptocurrency trading volume can indicate differing levels of market participation. Nevertheless, volume alone does not establish the strength or persistence of a trend, and it should be interpreted with observed price movements.',
        'news': 'Energy-market headlines are relevant because changes in oil and other input costs can influence business expenses and consumer prices. AP News provides context for these developments. The degree to which energy costs affect financial markets varies by industry and economic conditions.',
        'assessment': 'Higher energy costs may increase inflation pressure and contribute to financial uncertainty. At the same time, different sectors can respond differently to the same energy-price development. Simple conclusions about the entire market should therefore be avoided.',
        'recommendation': 'Review verified energy-price movements, inflation indicators and financial-market data together. Clearly separate reported events from potential economic implications when preparing later assessments.'
    },
    {
        'topic': 'Investor Sentiment',
        'summary': 'This report reviews indicators commonly associated with investor sentiment across cryptocurrency and traditional financial markets. It emphasizes the difference between visible trading activity and durable changes in confidence.',
        'market': 'Daily cryptocurrency price changes and trading volume can provide signs of active market participation. A sharp movement, however, may be temporary. Neither the scale of a move nor the volume associated with it is sufficient to demonstrate the existence of a sustained investment trend.',
        'news': 'News regarding corporate results, economic conditions and major stock indexes can influence expectations about growth and risk. The research notes use AP News to provide broader context, rather than claiming a verified immediate impact on cryptocurrency prices.',
        'assessment': 'Sentiment is difficult to measure from a small set of headlines and market observations. Interpretation is especially uncertain when other developments occur at the same time. Overconfidence based on one trading session is a key risk.',
        'recommendation': 'Consider longer observation periods, corroborating news sources and consistent measures of market activity. Record competing explanations before assigning causes to changes in investor sentiment.'
    },
    {
        'topic': 'Investment Risk',
        'summary': 'This report outlines the main investment risks identified through the market and news research. The emphasis is on prudent assessment rather than security selection or immediate trading decisions.',
        'market': 'Market capitalization distinguishes relatively large cryptocurrency assets from smaller tokens, but size does not eliminate the possibility of sharp price changes. Trading volume can offer some insight into market activity, yet reported figures should not be treated as a complete measure of liquidity.',
        'news': 'Reports on economic uncertainty and financial-market fluctuations highlight the external factors that may shape risk appetite. AP News is useful for background awareness; assessing an investment still requires asset-specific information and verified market data.',
        'assessment': 'Key risks include volatility, liquidity constraints, unreliable assumptions about future returns and sensitivity to news events. An asset may appear attractive based on a brief observation while remaining unsuitable for an investor with a limited risk tolerance.',
        'recommendation': 'Apply a clear risk framework before any investment decision. Review exposure limits, confirm data reliability and consider several plausible market scenarios rather than relying on a single headline or price movement.'
    },
    {
        'topic': 'Stocks and Cryptocurrency',
        'summary': 'This report compares the types of information used to assess cryptocurrencies and United States equities. Its purpose is to recognize important differences in valuation and market drivers.',
        'market': 'Bitcoin and Ethereum provide examples of major digital assets for which market capitalization, daily price movements and trading volume are widely monitored. These indicators describe trading conditions but do not serve the same role as company financial statements in equity analysis.',
        'news': 'Corporate earnings, stock-index performance and economic news can be central to an equity-market assessment. AP News coverage helps identify relevant themes. Cryptocurrency prices may respond to some of the same macroeconomic conditions but should not be evaluated as if they were company shares.',
        'assessment': 'Stocks and digital assets can differ in the nature of their underlying value, cash-flow characteristics and sources of risk. Their daily returns are not directly comparable without controlling for time horizon and volatility.',
        'recommendation': 'Use asset-appropriate analytical criteria and label all comparisons carefully. Future work should incorporate verified price data and, for equities, fundamental business information before discussing relative attractiveness.'
    },
    {
        'topic': 'Financial Research Summary',
        'summary': 'This report consolidates the selected research notes into a structured financial-market overview. Its purpose is to describe available observations, explain their relevance and identify the evidence needed for further analysis.',
        'market': 'Crypto rankings, market capitalization, daily percentage changes and trading volume are practical starting points for market monitoring. Each measure provides a different perspective; no single figure is adequate for an overall investment assessment.',
        'news': 'Financial coverage relating to inflation, interest rates and United States stock markets provides the macroeconomic setting for the market review. AP News helps identify major themes, although specific causal claims require further verification.',
        'assessment': 'The available observations are qualitative and provide limited support for numerical forecasts. Rapid price movements, shifts in investor expectations and changing financial conditions remain material considerations.',
        'recommendation': 'Maintain a consistent research process that combines trusted data and clearly identified news sources. Record exact figures and observation times when performing deeper analysis, and revise the report when new evidence materially changes the outlook.'
    },
]


# ============================================================
# EXACT ORIGINAL TYPING + TYPO LOGIC (SCENARIO 1)
# ============================================================

def random_typing_delay():
    return random.uniform(MIN_CHAR_DELAY, MAX_CHAR_DELAY)


def generate_typo(word):
    neighbours = {
        'q': 'w', 'w': 'e', 'e': 'r', 'r': 't', 't': 'y',
        'y': 'u', 'u': 'i', 'i': 'o', 'o': 'p',
        'a': 's', 's': 'd', 'd': 'f', 'f': 'g', 'g': 'h',
        'h': 'j', 'j': 'k', 'k': 'l',
        'z': 'x', 'x': 'c', 'c': 'v', 'v': 'b', 'b': 'n',
        'n': 'm'
    }
    positions = [i for i, char in enumerate(word) if char.lower() in neighbours]
    if not positions:
        return None, None, None
    position = random.choice(positions)
    original = word[position]
    incorrect = neighbours[original.lower()]
    if original.isupper():
        incorrect = incorrect.upper()
    return position, original, incorrect


def type_character(character):
    pyautogui.write(character)
    time.sleep(random_typing_delay())


def type_word_with_possible_typo(word):
    make_typo = len(word) >= 3 and random.random() < TYPO_PROBABILITY
    if not make_typo:
        for character in word:
            type_character(character)
        return

    position, original, incorrect = generate_typo(word)
    if position is None:
        for character in word:
            type_character(character)
        return

    for i in range(position):
        type_character(word[i])
    type_character(incorrect)
    time.sleep(random.uniform(MIN_CORRECTION_PAUSE, MAX_CORRECTION_PAUSE))
    pyautogui.press('backspace')
    time.sleep(random.uniform(0.1, 0.3))
    type_character(original)
    for i in range(position + 1, len(word)):
        type_character(word[i])


def type_text(text):
    words = str(text).split(' ')
    for index, word in enumerate(words):
        type_word_with_possible_typo(word)
        if index < len(words) - 1:
            pyautogui.press('space')
            time.sleep(random.uniform(MIN_WORD_PAUSE, MAX_WORD_PAUSE))


def paragraph(text):
    type_text(text)
    pyautogui.press('enter', presses=2, interval=0.16)
    time.sleep(random.uniform(MIN_PARAGRAPH_PAUSE, MAX_PARAGRAPH_PAUSE))


def bold_heading(text):
    # Keyboard-based formatting works even after Writer is resized to half screen.
    pyautogui.hotkey('ctrl', 'b')
    type_text(text)
    pyautogui.hotkey('ctrl', 'b')
    pyautogui.press('enter', presses=2, interval=0.16)
    time.sleep(random.uniform(0.5, 1.2))


# ============================================================
# WINDOWS API: IDENTIFY THE CORRECT WRITER WINDOWS
# ============================================================

# [INTEGRATION] Own user32 instance, so the argtypes declared below do not
# leak into web_tasks.py / other modules running in the same process.
user32 = ctypes.WinDLL("user32")
WIN_CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

# Declare pointer-sized Windows argument types (important on 64-bit Windows).
user32.EnumWindows.argtypes = [WIN_CALLBACK, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.UINT
]
user32.SetWindowPos.restype = wintypes.BOOL
user32.SystemParametersInfoW.argtypes = [
    wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT
]
user32.SystemParametersInfoW.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD


def open_writer_windows():
    matches = {}

    @WIN_CALLBACK
    def enum_window(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, len(buffer))
        name = buffer.value
        if 'openoffice writer' in name.lower():
            matches[int(hwnd)] = name
        return True

    user32.EnumWindows(enum_window, 0)
    return matches


def window_process_id(hwnd):
    """Get the owning process ID so new Writer windows can be detected by app."""
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def window_title(hwnd):
    size = user32.GetWindowTextLengthW(hwnd)
    if size <= 0:
        return ''
    buf = ctypes.create_unicode_buffer(size + 1)
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value


def visible_windows_for_process(pid):
    """Find visible, titled top-level windows belonging to OpenOffice."""
    matches = {}

    @WIN_CALLBACK
    def enum_window(hwnd, _):
        if user32.IsWindowVisible(hwnd) and window_process_id(hwnd) == pid:
            title = window_title(hwnd)
            if title:
                matches[int(hwnd)] = title
        return True

    user32.EnumWindows(enum_window, 0)
    return matches


def focus_window(hwnd):
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE

    # Focus using a mouse click on the window title bar.
    # Avoid pressing Alt alone: it can activate Writer's menus.
    user32.SetForegroundWindow(hwnd)
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError('Unable to read the intended Writer window position.')
    title_x = rect.left + min(120, max(30, (rect.right - rect.left) // 2))
    title_y = rect.top + 12
    pyautogui.moveTo(title_x, title_y, duration=0.4)
    pyautogui.click()
    time.sleep(0.7)

    if int(user32.GetForegroundWindow()) != int(hwnd):
        raise RuntimeError('Unable to activate the intended Writer window. Please click it and retry.')


def get_work_area():
    area = wintypes.RECT()
    # SPI_GETWORKAREA avoids covering the Windows taskbar.
    result = user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(area), 0)
    if not result:
        raise RuntimeError('Could not read Windows desktop work area.')
    return area



def launch_new_writer_from_start_menu(notes_hwnd):
    """Use Scenario 1's working Start-menu launch, never Ctrl+N.

    The second window must have a NEW HWND. This prevents the script from
    mistakenly entering financial-report text into the original Research Notes.
    """
    print('Opening second OpenOffice Writer from Windows Start menu...')
    before = open_writer_windows()
    print('Writer windows before launch:', before)

    pyautogui.press('win')
    time.sleep(random.uniform(0.8, 1.5))
    pyautogui.write('OpenOffice Writer', interval=0.15)
    time.sleep(random.uniform(0.8, 1.5))
    pyautogui.press('enter')

    def await_new_window(seconds):
        for _ in range(seconds * 2):
            time.sleep(0.5)
            after = open_writer_windows()
            fresh = [(hwnd, title) for hwnd, title in after.items()
                     if hwnd not in before and hwnd != notes_hwnd]
            if fresh:
                # Prefer the untitled blank Writer window, if present.
                fresh.sort(key=lambda item: not item[1].lower().startswith('untitled'))
                hwnd, title = fresh[0]
                print('Second Writer window found:', title)
                return hwnd
        return None

    report_hwnd = await_new_window(15)
    if report_hwnd is not None:
        return report_hwnd

    # Rare case: Start-menu launch only brought back the existing document.
    # [INTEGRATION] Retry the Start-menu launch once. (The old fallback ran
    # swriter.exe via subprocess, which makes python the parent process.)
    print('Start menu did not create a second window; retrying Start menu once...')
    pyautogui.press('esc')
    time.sleep(random.uniform(1.0, 2.0))
    pyautogui.press('win')
    time.sleep(random.uniform(0.8, 1.5))
    pyautogui.write('OpenOffice Writer', interval=0.15)
    time.sleep(random.uniform(0.8, 1.5))
    pyautogui.press('enter')
    report_hwnd = await_new_window(15)
    if report_hwnd is not None:
        return report_hwnd

    print('Writer windows after launch:', open_writer_windows())
    print('Currently active window:', window_title(user32.GetForegroundWindow()))
    raise RuntimeError(
        'A separate blank Writer document did not open. '
        'Research Notes were NOT modified. '
        'Please open a new Writer document manually and rerun after closing '
        'any extra blank Writer documents, or check the OpenOffice installation.'
    )


def arrange_split_screen(notes_hwnd, report_hwnd):
    """Position both Writer windows flush together, without a centre gap.

    Windows 11 includes invisible resizing borders around a normal window.
    Splitting the OUTER rectangles at the centre can therefore leave a
    visible gap.  We correct each window using its actual visible DWM edges.
    """
    area = get_work_area()  # excludes the taskbar
    middle = area.left + (area.right - area.left) // 2
    height = area.bottom - area.top

    SW_RESTORE = 9
    SWP_NOZORDER = 0x0004
    SWP_NOACTIVATE = 0x0010
    flags = SWP_NOZORDER | SWP_NOACTIVATE

    user32.ShowWindow(notes_hwnd, SW_RESTORE)
    user32.ShowWindow(report_hwnd, SW_RESTORE)
    time.sleep(0.6)

    # First put each window in its ordinary half of the screen.
    ok_left = user32.SetWindowPos(
        notes_hwnd, 0, area.left, area.top,
        middle - area.left, height, flags
    )
    ok_right = user32.SetWindowPos(
        report_hwnd, 0, middle, area.top,
        area.right - middle, height, flags
    )
    if not (ok_left and ok_right):
        raise RuntimeError('Unable to position the Writer windows.')
    time.sleep(0.5)

    # Query the actual VISIBLE bounds. GetWindowRect includes a hidden
    # resize frame, which can create a roughly 10-20 pixel centre gap.
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL

    dwmapi = ctypes.windll.dwmapi
    dwmapi.DwmGetWindowAttribute.argtypes = [
        wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD
    ]
    dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long
    DWMWA_EXTENDED_FRAME_BOUNDS = 9

    def get_outer_rect(hwnd):
        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise RuntimeError('Could not read Writer window coordinates.')
        return rect

    def get_visible_rect(hwnd):
        rect = wintypes.RECT()
        result = dwmapi.DwmGetWindowAttribute(
            hwnd, DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect), ctypes.sizeof(rect)
        )
        return rect if result == 0 else None

    def fit_window(hwnd, target_left, target_right):
        outer = get_outer_rect(hwnd)
        visible = get_visible_rect(hwnd)

        if visible is not None:
            # Thickness of the invisible border on every side.
            inset_l = visible.left - outer.left
            inset_r = outer.right - visible.right
            inset_t = visible.top - outer.top
            inset_b = outer.bottom - visible.bottom

            # If DPI virtualization produces mismatched coordinate systems,
            # fall back to a modest overlap rather than moving windows wildly.
            borders = (inset_l, inset_r, inset_t, inset_b)
            usable = all(0 <= v <= 24 for v in borders)
        else:
            usable = False

        if usable:
            x = target_left - inset_l
            y = area.top - inset_t
            width = target_right - target_left + inset_l + inset_r
            win_height = height + inset_t + inset_b
        else:
            # Fallback for VM/DWM configurations that do not report the
            # visible frame accurately. Hide the invisible centre borders.
            overlap = 10
            x = target_left - overlap
            y = area.top
            width = target_right - target_left + 2 * overlap
            win_height = height

        if not user32.SetWindowPos(hwnd, 0, x, y, width, win_height, flags):
            raise RuntimeError('Could not remove gap between Writer windows.')

    fit_window(notes_hwnd, area.left, middle)
    fit_window(report_hwnd, middle, area.right)
    time.sleep(0.6)

    # Measure again after resizing, so any remaining gap is visible in IDLE.
    left_visual = get_visible_rect(notes_hwnd)
    right_visual = get_visible_rect(report_hwnd)
    if left_visual is not None and right_visual is not None:
        gap = right_visual.left - left_visual.right
        print(f'Visible centre gap: {gap} pixel(s) (0 means flush).')
        # Some window managers adjust geometry asynchronously: close residual
        # positive gaps by expanding the notes and report toward the centre.
        if 0 < gap <= 30:
            left_outer = get_outer_rect(notes_hwnd)
            right_outer = get_outer_rect(report_hwnd)
            grow_left = gap // 2
            move_right = gap - grow_left
            user32.SetWindowPos(
                notes_hwnd, 0, left_outer.left, left_outer.top,
                left_outer.right - left_outer.left + grow_left,
                left_outer.bottom - left_outer.top, flags
            )
            user32.SetWindowPos(
                report_hwnd, 0, right_outer.left - move_right,
                right_outer.top,
                right_outer.right - right_outer.left + move_right,
                right_outer.bottom - right_outer.top, flags
            )

    print('Research Notes LEFT; Financial Report RIGHT; no centre gap.')


# ============================================================
# SAVE THE NEW REPORT ON THE DESKTOP
# ============================================================

def next_report_path():
    # [INTEGRATION] Realistic name: 'Financial Report', or
    # 'Financial Report 18 Oct' (then '... (2)') if taken. Was Financial_Report{n}.
    base = 'Financial Report'
    if not os.path.exists(os.path.join(DESKTOP, base + '.odt')):
        return os.path.join(DESKTOP, base + '.odt')
    now = time.localtime()
    dated = f"{base} {now.tm_mday} {time.strftime('%b', now)}"
    name, n = dated, 2
    while os.path.exists(os.path.join(DESKTOP, name + '.odt')):
        name = f'{dated} ({n})'
        n += 1
    return os.path.join(DESKTOP, name + '.odt')


def save_report(report_path):
    # Same Save As process as Scenario 1: type the filename only.
    # The Save As dialog uses its current folder (normally Desktop in this VM).
    filename = os.path.splitext(os.path.basename(report_path))[0]
    print('Saving as:', filename + '.odt')

    pyautogui.hotkey('ctrl', 'shift', 's')
    time.sleep(3)
    pyautogui.hotkey('alt', 'n')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.write(filename, interval=0.10)
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)

    if os.path.isfile(report_path):
        print('Report saved on Desktop.')
    else:
        print('Save action completed. Check the current Save As folder if the file is not on Desktop.')


# ============================================================
# CLOSE BOTH WRITER WINDOWS AFTER SAVING
# ============================================================

def close_writer_with_mouse(hwnd, document_name):
    """Close the intended Writer window using its actual close button."""
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL

    if not user32.IsWindow(hwnd):
        print(f'{document_name} is already closed.')
        return

    print(f'Closing {document_name}...')
    focus_window(hwnd)
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError(f'Could not locate the close button for {document_name}.')

    # Same mouse-based closing approach as Scenario 1.
    close_x = rect.right - 15
    close_y = rect.top + 15
    pyautogui.moveTo(close_x, close_y, duration=0.4)
    time.sleep(0.5)
    pyautogui.click()
    time.sleep(2)

    if user32.IsWindow(hwnd):
        raise RuntimeError(
            f'{document_name} did not close. Check for an unsaved-changes dialog.'
        )
    print(f'{document_name} closed.')


# ============================================================
# MAIN — FINANCIAL REPORT SPLIT SCREEN
# ============================================================

def run_financial_report(document_index=None, notes_filename=None, notes_hwnd=None):
    """[INTEGRATION] The orchestrator passes the topic index, notes filename and
    (optionally) the notes window handle in memory. With no arguments
    (standalone run) the json written by Research Notes Part 1 is used."""
    print('=' * 60)
    print('STAGE 3 — FINANCIAL REPORT WITH SPLIT SCREEN')
    print('=' * 60)

    if document_index is None:
        print(f'Starting in {START_DELAY} seconds...')
        time.sleep(START_DELAY)

        if not os.path.isfile(SESSION_FILE):
            raise FileNotFoundError(
                'Missing research_notes_session.json. Run Research Notes Part 1 first.'
            )
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            session = json.load(f)

        document_index = session['document_index']
        notes_filename = session['filename']

    document_index = int(document_index)
    if not 0 <= document_index < len(REPORTS):
        raise ValueError('Invalid research topic index in the session file.')

    report = REPORTS[document_index]
    print('Research Notes:', notes_filename)
    print('Selected report topic:', report['topic'])

    # 1. Locate the exact existing Research Notes window.
    #    [INTEGRATION] Use the handle from the orchestrator if it is still valid.
    windows_before = open_writer_windows()
    if notes_hwnd is None or int(notes_hwnd) not in windows_before:
        notes_windows = [
            hwnd for hwnd, title in windows_before.items()
            if notes_filename.lower() in title.lower()
        ]
        if not notes_windows:
            raise RuntimeError(
                f'Cannot find {notes_filename} in OpenOffice Writer. '
                'Leave the Research Notes document OPEN after Part 2.'
            )
        notes_hwnd = notes_windows[0]
    notes_hwnd = int(notes_hwnd)
    focus_window(notes_hwnd)

    # 2. Launch Writer from Start menu, as in Scenario 1 (NO Ctrl+N).
    report_hwnd = launch_new_writer_from_start_menu(notes_hwnd)

    # 3. Split windows: notes on LEFT, report on RIGHT.
    arrange_split_screen(notes_hwnd, report_hwnd)
    focus_window(report_hwnd)
    pyautogui.hotkey('ctrl', 'home')

    # 4. Write a formal, topic-matched report, using Scenario 1 typing speed.
    print('Typing formal financial report...')
    bold_heading('FINANCIAL MARKET RESEARCH REPORT')
    bold_heading('Research Focus: ' + report['topic'])

    # Keep ONLY three report sections. Do not merge the omitted sections.
    bold_heading('1. Research Scope and Sources')
    paragraph('This report draws on the research notes compiled from CoinMarketCap '
              'and AP News. CoinMarketCap provides cryptocurrency market indicators, '
              'while AP News provides wider financial and economic context.')

    time.sleep(random.uniform(1.5, 3.0))
    bold_heading('2. Cryptocurrency Market Review')
    paragraph(report['market'])

    time.sleep(random.uniform(1.5, 3.0))
    bold_heading('3. Financial News and Economic Context')
    paragraph(report['news'])

    # 5. Save the Financial Report, then close BOTH Writer documents.
    save_report(next_report_path())

    # Avoid closing either window if the report is still untitled/unsaved.
    if window_title(report_hwnd).lower().startswith('untitled'):
        raise RuntimeError('Financial Report appears unsaved. Both Writer windows remain open.')

    # Close the saved report first, then the already-saved Research Notes.
    close_writer_with_mouse(report_hwnd, 'Financial Report')
    close_writer_with_mouse(notes_hwnd, 'Research Notes')

    print('=' * 60)
    print('FINANCIAL REPORT COMPLETED')
    print('Both Writer windows closed after saving.')
    print('=' * 60)


if __name__ == '__main__':
    try:
        run_financial_report()
    except pyautogui.FailSafeException:
        print('Emergency stop activated.')
    except Exception as error:
        print('ERROR:', error)
