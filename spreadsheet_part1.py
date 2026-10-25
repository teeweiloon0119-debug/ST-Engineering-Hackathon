import os
import time
import random
from pathlib import Path

import pyautogui

import human_io  # [FINALIST] shared human-like mouse + typing
import ui_find    # [FINALIST] double-click the real desktop icon (UI Automation)
from calc_nav import focus_name_box, go_to_sheet, go_to_cell as calc_go_to_cell


# ============================================================
# SETTINGS
# ============================================================

# Desktop icon label (from the VM). Fallback pixel if UIA can't find it.
SPREADSHEET_ICON_NAME = "Profit and Loss Statement"
SPREADSHEET_ICON = (40, 649)

# Salary sheet → Wei Loon's salary, E4
SALARY_E4 = "E4"

# Summary sheet → Salaries, Benefits & Wages, F19
SUMMARY_F19 = "F19"


# Typing speed now lives in human_io (content-aware).

pyautogui.FAILSAFE = True


# ============================================================
# TYPING FUNCTION
# ============================================================

def type_like_writer(text):

    """
    [FINALIST] Human-like typing via human_io: variable per-character
    delays, and content-aware speed - numbers and formulas are typed more
    slowly than words. Typos are disabled inside Calc so a correction can
    never corrupt a cell value.
    """

    human_io.human_type(
        str(text),
        typo_rate=0
    )


# ============================================================
# OPEN EXISTING SPREADSHEET DIRECTLY
# ============================================================

def open_spreadsheet():

    print("=" * 55)
    print("OPENING PROFIT AND LOSS STATEMENT")
    print("=" * 55)

    print(
        "Opening spreadsheet from desktop..."
    )

    # Double-click the REAL desktop icon, found by name via UI Automation
    # (no pixel position). Fall back to the known icon coordinates.
    opened = False
    if ui_find.available():
        opened = ui_find.click_desktop_icon(SPREADSHEET_ICON_NAME, double=True)

    if not opened:
        human_io.human_move(
            SPREADSHEET_ICON[0],
            SPREADSHEET_ICON[1]
        )
        human_io.human_pause(0.5, 1.2)
        human_io.human_double_click(
            SPREADSHEET_ICON[0],
            SPREADSHEET_ICON[1],
            jitter=False
        )

    print(
        "Waiting for OpenOffice Calc..."
    )

    time.sleep(7)

    time.sleep(1.5)

    print(
        "Spreadsheet opened."
    )


# ============================================================
# NAVIGATE TO SHEET
# ============================================================
# go_to_sheet now lives in calc_nav: it clicks the real sheet tab via UI
# Automation (what a person does), and falls back to typing the sheet name
# into the Name Box. Imported at the top of this module.


# ============================================================
# SELECT CELL BY ADDRESS (NAME BOX)
# ============================================================

def go_to_cell(address):

    """
    [FINALIST] Target a cell by its ADDRESS instead of its pixel position:
    calc_nav clicks the real cell when it is on screen (UI Automation),
    otherwise types the address into the Name Box. The address applies to
    the sheet that is currently active.
    """

    print(
        f"Going to cell {address}..."
    )

    calc_go_to_cell(address)


# ============================================================
# ENTER VALUE
# ============================================================

def enter_value(value):

    print(
        f"Entering {value}..."
    )

    type_like_writer(
        str(value)
    )

    time.sleep(0.6)

    pyautogui.press(
        "enter"
    )

    time.sleep(1.2)


# ============================================================
# PART 1 — SALARY UPDATE
# ============================================================

def update_salary():

    print()
    print("=" * 55)
    print("PART 1 - SALARY UPDATE")
    print("=" * 55)

    # --------------------------------------------------------
    # 1. MAKE SURE WE ARE ON SALARY FIRST
    # --------------------------------------------------------

    print(
        "Making sure Salary sheet is active..."
    )

    go_to_sheet(
        "Salary"
    )

    time.sleep(1.0)

    # --------------------------------------------------------
    # 2. SELECT E4 BY ADDRESS (NAME BOX)
    # --------------------------------------------------------

    print(
        "Selecting Wei Loon's salary cell E4..."
    )

    go_to_cell(
        SALARY_E4
    )

    # --------------------------------------------------------
    # 3. CHANGE SALARY
    # --------------------------------------------------------

    print(
        "Changing Wei Loon's salary:"
    )

    print(
        "$1,500 -> $1,600"
    )

    enter_value(
        1600
    )

    # --------------------------------------------------------
    # 4. RECALCULATE
    # --------------------------------------------------------

    print(
        "Recalculating Salary sheet..."
    )

    pyautogui.press(
        "f9"
    )

    time.sleep(1.5)

    # --------------------------------------------------------
    # 5. GO TO SUMMARY
    # --------------------------------------------------------

    print(
        "Returning to Summary..."
    )

    go_to_sheet(
        "Summary"
    )

    time.sleep(1.0)

    # --------------------------------------------------------
    # 6. SELECT F19 BY ADDRESS (NAME BOX)
    # --------------------------------------------------------

    print(
        "Selecting Summary F19..."
    )

    go_to_cell(
        SUMMARY_F19
    )

    # --------------------------------------------------------
    # 7. ENTER TOTAL SALARY
    # --------------------------------------------------------

    print(
        "Updating total salary:"
    )

    print(
        "$5,200 -> $5,300"
    )

    enter_value(
        5300
    )

    # --------------------------------------------------------
    # 8. RECALCULATE
    # --------------------------------------------------------

    print(
        "Recalculating Summary..."
    )

    pyautogui.press(
        "f9"
    )

    time.sleep(1.5)

    print()
    print("=" * 55)
    print("PART 1 COMPLETED")
    print("=" * 55)

    print(
        "Salary!E4 = 1600"
    )

    print(
        "Summary!F19 = 5300"
    )

    print("=" * 55)


# ============================================================
# MAIN
# ============================================================

def run_part1():

    print()
    print("=" * 55)
    print("OFFICE SPREADSHEET - PART 1")
    print("=" * 55)

    try:

        # Directly open the .ods file
        open_spreadsheet()

        # Perform Part 1
        update_salary()

        print()
        print(
            "PART 1 FINISHED SUCCESSFULLY"
        )

    except pyautogui.FailSafeException:

        print()
        print(
            "Emergency stop activated."
        )

    except Exception as error:

        print()
        print("=" * 55)
        print("ERROR")
        print("=" * 55)

        print(error)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import random

    run_part1()
