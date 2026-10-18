import os
import time
import random
from pathlib import Path

import pyautogui


# ============================================================
# SETTINGS
# ============================================================

# Profit and Loss Statement.ods desktop icon
SPREADSHEET_ICON = (40, 649)

# OpenOffice Calc Name Box
NAME_BOX = (17, 124)

# Salary sheet → Wei Loon's salary, E4
SALARY_E4 = (561,216)

# Summary sheet → Salaries, Benefits & Wages, F19
SUMMARY_F19 = (638,424)


# ============================================================
# WRITER-STYLE TYPING SETTINGS
# ============================================================

MIN_CHAR_DELAY = 0.06
MAX_CHAR_DELAY = 0.16

MIN_WORD_PAUSE = 0.08
MAX_WORD_PAUSE = 0.35

LONG_PAUSE_PROBABILITY = 0.08
MIN_LONG_PAUSE = 0.5
MAX_LONG_PAUSE = 1.5

TYPE_INTERVAL = 0.15

pyautogui.FAILSAFE = True


# ============================================================
# TYPING FUNCTION
# ============================================================

def type_like_writer(text):

    words = text.split(" ")

    for i, word in enumerate(words):

        for character in word:

            pyautogui.write(character)

            time.sleep(
                random.uniform(
                    MIN_CHAR_DELAY,
                    MAX_CHAR_DELAY
                )
            )

        if i < len(words) - 1:

            pyautogui.press("space")

            time.sleep(
                random.uniform(
                    MIN_WORD_PAUSE,
                    MAX_WORD_PAUSE
                )
            )

            if random.random() < LONG_PAUSE_PROBABILITY:

                time.sleep(
                    random.uniform(
                        MIN_LONG_PAUSE,
                        MAX_LONG_PAUSE
                    )
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

    # Move mouse to the spreadsheet icon
    pyautogui.moveTo(
        SPREADSHEET_ICON[0],
        SPREADSHEET_ICON[1],
        duration=0.5
    )

    time.sleep(0.8)

    # Double-click the .ods file
    pyautogui.doubleClick(
        SPREADSHEET_ICON[0],
        SPREADSHEET_ICON[1],
        interval=0.15
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
# NAVIGATE TO SHEET USING NAME BOX
# ============================================================

def go_to_sheet(sheet_name):

    print(f"Navigating to {sheet_name} sheet...")

    # Move mouse to Name Box
    pyautogui.moveTo(
        NAME_BOX[0],
        NAME_BOX[1],
        duration=random.uniform(0.4, 0.7)
    )

    time.sleep(
        random.uniform(0.6, 1.0)
    )

    # Click Name Box
    pyautogui.click()

    time.sleep(
        random.uniform(0.5, 0.8)
    )

    # Select current contents
    pyautogui.doubleClick(
        NAME_BOX[0],
        NAME_BOX[1],
        interval=0.12
    )

    time.sleep(
        random.uniform(0.4, 0.7)
    )

    # Type ONLY the sheet name
    type_like_writer(
        sheet_name
    )

    time.sleep(
        random.uniform(0.5, 0.9)
    )

    pyautogui.press("enter")

    time.sleep(
        random.uniform(1.2, 1.8)
    )

    print(
        f"{sheet_name} sheet selected."
    )


# ============================================================
# SELECT CELL WITH MOUSE
# ============================================================

def click_cell(position):

    x, y = position

    print(
        f"Selecting cell at ({x}, {y})..."
    )

    pyautogui.moveTo(
        x,
        y,
        duration=0.45
    )

    time.sleep(0.7)

    pyautogui.click()

    time.sleep(0.8)


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
    # 2. SELECT E4 WITH MOUSE
    # --------------------------------------------------------

    print(
        "Selecting Wei Loon's salary cell E4..."
    )

    click_cell(
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
    # 6. SELECT F19 WITH MOUSE
    # --------------------------------------------------------

    print(
        "Selecting Summary F19..."
    )

    click_cell(
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
