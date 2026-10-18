import time
import random
import pyautogui


# ============================================================
# SETTINGS
# ============================================================

# OpenOffice Calc Name Box
NAME_BOX = (37, 126)

# Summary sheet → Reimbursement total → F23
SUMMARY_F23 = (637, 490)

# Summary sheet → Net Earnings → F31
SUMMARY_F31 = (627, 627)


# ============================================================
# TYPING SPEED
# ============================================================

# Same general typing speed used in Writer
MIN_CHAR_DELAY = 0.06
MAX_CHAR_DELAY = 0.16

MIN_WORD_PAUSE = 0.08
MAX_WORD_PAUSE = 0.35

LONG_PAUSE_PROBABILITY = 0.08
MIN_LONG_PAUSE = 0.5
MAX_LONG_PAUSE = 1.5


pyautogui.FAILSAFE = True


# ============================================================
# WRITER-STYLE TYPING
# ============================================================

def type_like_writer(text):

    words = text.split(" ")

    for index, word in enumerate(words):

        # Type each character
        for character in word:

            pyautogui.write(character)

            time.sleep(
                random.uniform(
                    MIN_CHAR_DELAY,
                    MAX_CHAR_DELAY
                )
            )

        # Space between words
        if index < len(words) - 1:

            pyautogui.press("space")

            time.sleep(
                random.uniform(
                    MIN_WORD_PAUSE,
                    MAX_WORD_PAUSE
                )
            )

            # Occasional longer pause
            if random.random() < LONG_PAUSE_PROBABILITY:

                time.sleep(
                    random.uniform(
                        MIN_LONG_PAUSE,
                        MAX_LONG_PAUSE
                    )
                )


# ============================================================
# GO TO SUMMARY SHEET
# ============================================================

def go_to_summary():

    print(
        "Navigating to Summary sheet..."
    )

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

    # Select existing text
    pyautogui.hotkey(
        "ctrl",
        "a"
    )

    time.sleep(
        random.uniform(0.3, 0.5)
    )

    # Type ONLY "Summary"
    print(
        "Typing 'Summary'..."
    )

    type_like_writer(
        "Summary"
    )

    time.sleep(
        random.uniform(0.5, 0.8)
    )

    pyautogui.press(
        "enter"
    )

    time.sleep(
        random.uniform(1.2, 1.8)
    )

    print(
        "Summary sheet selected."
    )


# ============================================================
# SELECT CELL WITH MOUSE
# ============================================================

def click_cell(position):

    x, y = position

    print(
        f"Moving mouse to ({x}, {y})..."
    )

    pyautogui.moveTo(
        x,
        y,
        duration=random.uniform(0.4, 0.7)
    )

    time.sleep(
        random.uniform(0.6, 1.0)
    )

    pyautogui.click()

    time.sleep(
        random.uniform(0.7, 1.1)
    )


# ============================================================
# TYPE CELL VALUE
# ============================================================

def type_cell_value(value):

    print(
        f"Entering: {value}"
    )

    type_like_writer(
        str(value)
    )

    time.sleep(
        random.uniform(0.4, 0.8)
    )

    # Commit the value
    pyautogui.press(
        "enter"
    )

    time.sleep(
        random.uniform(0.9, 1.3)
    )


# ============================================================
# SAVE
# ============================================================

def save_spreadsheet():

    print()
    print(
        "Saving spreadsheet..."
    )

    time.sleep(
        random.uniform(0.8, 1.5)
    )

    # Save
    pyautogui.hotkey(
        "ctrl",
        "s"
    )

    time.sleep(
        random.uniform(2.0, 3.0)
    )

    print(
        "Spreadsheet saved."
    )


# ============================================================
# CLOSE CALC WITH MOUSE
# ============================================================

def close_calc_with_mouse():

    print(
        "Preparing to close Calc..."
    )

    time.sleep(
        random.uniform(1.0, 2.0)
    )

    # Get current screen size
    screen_width, screen_height = pyautogui.size()

    # Move to the Calc close button
    close_x = screen_width - 15
    close_y = 12

    print(
        f"Moving to Calc close button: "
        f"({close_x}, {close_y})"
    )

    pyautogui.moveTo(
        close_x,
        close_y,
        duration=random.uniform(0.5, 0.8)
    )

    time.sleep(
        random.uniform(0.8, 1.2)
    )

    # Click close button
    print(
        "Closing Calc..."
    )

    pyautogui.click()

    time.sleep(
        random.uniform(2.0, 3.0)
    )

    print(
        "Calc closed."
    )


# ============================================================
# PART 4
# ============================================================

def part4_finish():

    print()
    print("=" * 60)
    print("PART 4 — FINALISE MONTHLY REPORT")
    print("=" * 60)

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Part 3 already finished on Reimbursement.
    #
    # We therefore DO NOT navigate to Reimbursement again.
    # We only need to go back to Summary.
    # --------------------------------------------------------

    print(
        "Returning from Reimbursement to Summary..."
    )

    go_to_summary()

    # --------------------------------------------------------
    # Select Summary F23
    # --------------------------------------------------------

    print(
        "Selecting Summary F23..."
    )

    click_cell(
        SUMMARY_F23
    )

    # --------------------------------------------------------
    # Enter total reimbursement
    #
    # Apple Laptop = 1299
    # External SSD = 60
    #
    # Total = 1359
    # --------------------------------------------------------

    print(
        "Entering total reimbursement: 1359"
    )

    type_cell_value(
        1359
    )

   # --------------------------------------------------------
# Calculate Net Earnings in F31 using mouse-selected cells
# --------------------------------------------------------

    print(
        "Calculating Net Earnings..."
    )

    # Select F31
    click_cell(
        SUMMARY_F31
    )
    
    # Start formula
    type_like_writer(
        "="
    )

    time.sleep(
        random.uniform(0.5, 0.8)
    )
    
# --------------------------------------------------------
# Mouse → F28
# Earnings Before Taxes
# --------------------------------------------------------

    print(
        "Selecting Earnings Before Taxes F28..."
    )

    click_cell(
        (632, 574)
    )

    time.sleep(
        random.uniform(0.5, 0.8)
    )

# Type subtraction operator
    type_like_writer(
        "-"
    )

    time.sleep(
        random.uniform(0.5, 0.8)
    )

# --------------------------------------------------------
# Mouse → F30
# Income Taxes
# --------------------------------------------------------

    print(
        "Selecting Income Taxes F30..."
    )

    click_cell(
        (627, 609)
    )

    time.sleep(
        random.uniform(0.5, 0.8)
    )

# --------------------------------------------------------
# Confirm formula
# --------------------------------------------------------

    pyautogui.press(
        "enter"
    )

    time.sleep(
        random.uniform(1.0, 1.5)
    )

    print(
        "Net Earnings calculated using F28 - F30."
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_spreadsheet()

    # --------------------------------------------------------
    # CLOSE WITH MOUSE
    # --------------------------------------------------------

    close_calc_with_mouse()

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PART 4 COMPLETED")
    print("=" * 60)

    print(
        "Summary!F23 = 1359"
    )

    print(
        "Summary!F31 = F28-F30"
    )

    print(
        "Spreadsheet saved."
    )

    print(
        "Calc closed."
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("SPREADSHEET PART 4 STARTING")
    print("=" * 60)

    try:

        # The spreadsheet should already be open.
        #
        # Part 3 should have just finished on the
        # Reimbursement sheet.

        part4_finish()

        print()
        print("=" * 60)
        print("PART 4 FINISHED SUCCESSFULLY")
        print("=" * 60)

    except pyautogui.FailSafeException:

        print()
        print(
            "Emergency stop activated."
        )

    except Exception as error:

        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)

        print(
            repr(error)
        )
