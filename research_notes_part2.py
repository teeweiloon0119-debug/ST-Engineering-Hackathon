#!/usr/bin/env python3
"""Part 2 of Research Notes: add AP News and conclusion to the open Writer document.

Run Part 1 first. Keep Writer open. Save both Python files in the same folder.
This script does NOT create a document, add a date, or close Writer.
"""
import ctypes
from ctypes import wintypes
import json
import os
import time
import random
import pyautogui

import human_io  # [FINALIST] shared human-like pauses

# Import the EXACT original Scenario 1 typing / typo-correction routines
# and the same 10 note options selected by Part 1.
from research_notes_part1 import (
    DOCUMENTS,
    SESSION_FILE,
    START_DELAY,
    MIN_PARAGRAPH_PAUSE,
    MAX_PARAGRAPH_PAUSE,
    type_text,
)

pyautogui.FAILSAFE = True


def focus_research_notes(filename):
    """Bring the Writer document saved by Part 1 to the foreground."""
    user32 = ctypes.WinDLL("user32")  # own instance [INTEGRATION]
    found = []

    CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @CALLBACK
    def check_window(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        title = buf.value.lower()
        if filename.lower() in title and 'openoffice writer' in title:
            found.append(hwnd)
        return True

    user32.EnumWindows(check_window, 0)
    if not found:
        raise RuntimeError(
            f"Cannot find the open Writer window for {filename}. "
            "Keep Part 1's document open before running Part 2."
        )

    hwnd = found[0]
    # Restore a minimized window, but do not split or reposition it.
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE

    # [INTEGRATION] Already in front (the orchestrator focuses it first):
    # skip the lone Alt press, which would open Writer's menu bar.
    if user32.GetForegroundWindow() == hwnd:
        return

    # Give Windows an Alt key event to permit foreground activation.
    pyautogui.press('alt')
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.5)

    if user32.GetForegroundWindow() != hwnd:
        raise RuntimeError(
            'Could not focus the research notes Writer window. '
            'Click the Writer document and try again.'
        )


def run_research_notes_part2(document_index=None, filename=None, excerpt=None):
    """[INTEGRATION] The orchestrator passes document_index + filename in
    memory. With no arguments (standalone run) the json from Part 1 is used.
    excerpt: a paragraph copied from the news site; it is still on the
    clipboard and gets pasted (Ctrl+V) under the AP News paragraph."""
    print('=' * 60)
    print('RESEARCH NOTES — PART 2: AP NEWS AND CONCLUSION')
    print('=' * 60)

    if document_index is None:
        print(f'Starting in {START_DELAY} seconds...')
        time.sleep(START_DELAY)

        if not os.path.isfile(SESSION_FILE):
            raise FileNotFoundError(
                'No Part 1 session was found. Run Research_Notes_Part1_CoinMarketCap.py first.'
            )

        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            session = json.load(f)

        document_index = session['document_index']
        filename = session['filename']

    document = DOCUMENTS[document_index]
    print('Continuing document:', filename)
    print('Topic:', document['title'])

    # Reactivate the SAME open Writer document after browsing or IDLE.
    focus_research_notes(filename)

    # Part 1 left the cursor after its CoinMarketCap paragraph.
    # Ctrl+End ensures Part 2 appends instead of overwriting earlier text.
    pyautogui.hotkey('ctrl', 'end')
    time.sleep(0.7)

    # AP News paragraph — keep Scenario 1 typing delays and corrections.
    type_text(document['news'])
    pyautogui.press('enter')
    pyautogui.press('enter')
    human_io.human_pause(MIN_PARAGRAPH_PAUSE, MAX_PARAGRAPH_PAUSE)

    # Paste the paragraph highlighted and copied on the news site.
    if excerpt:
        type_text('Excerpt from AP News:')
        pyautogui.press('enter')
        human_io.human_pause(0.5, 1.2)
        pyautogui.hotkey('ctrl', 'v')
        human_io.human_pause(0.8, 1.6)
        pyautogui.press('enter')
        pyautogui.press('enter')
        human_io.human_pause(MIN_PARAGRAPH_PAUSE, MAX_PARAGRAPH_PAUSE)

    # Self-conclusion, matched to the random topic chosen in Part 1.
    type_text(document['conclusion'])
    pyautogui.press('enter')
    pyautogui.press('enter')
    human_io.human_pause(MIN_PARAGRAPH_PAUSE, MAX_PARAGRAPH_PAUSE)

    # Save changes but KEEP Writer open for the later financial-report stage.
    pyautogui.hotkey('ctrl', 's')
    time.sleep(2)
    print('Part 2 completed and saved. Writer remains OPEN.')


if __name__ == '__main__':
    try:
        run_research_notes_part2()
    except pyautogui.FailSafeException:
        print('Emergency stop activated.')
    except Exception as error:
        print('ERROR:', error)