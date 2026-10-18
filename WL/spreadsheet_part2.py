import time
import random
import pyautogui


# ============================================================
# SETTINGS
# ============================================================

# OpenOffice Calc Name Box
NAME_BOX = (37, 126)

# Apple Laptop Quantity - C2
APPLE_QTY = (332, 184)


# ============================================================
# TYPING SPEED
# ============================================================

# Same general typing speed used in your Writer program
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

    """
    Type text using the same general timing as the Writer
    automation.
    """

    words = text.split(" ")

    for index, word in enumerate(words):

        # ----------------------------------------------------
        # Type each character
        # ----------------------------------------------------

        for character in word:

            pyautogui.write(character)

            time.sleep(
                random.uniform(
                    MIN_CHAR_DELAY,
                    MAX_CHAR_DELAY
                )
            )

        # ----------------------------------------------------
        # Space between words
        # ----------------------------------------------------

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
# GO TO SHEET USING NAME BOX
# ============================================================

def go_to_sheet(sheet_name):

    print(
        f"Navigating to {sheet_name} sheet..."
    )

    # --------------------------------------------------------
    # Move mouse to Name Box
    # --------------------------------------------------------

    pyautogui.moveTo(
        NAME_BOX[0],
        NAME_BOX[1],
        duration=random.uniform(0.4, 0.7)
    )

    time.sleep(
        random.uniform(0.6, 1.0)
    )

    # --------------------------------------------------------
    # Click Name Box
    # --------------------------------------------------------

    pyautogui.click()

    time.sleep(
        random.uniform(0.5, 0.8)
    )

    # --------------------------------------------------------
    # Select existing contents
    #
    # The mouse is used to locate the Name Box.
    # Ctrl+A is only used to clear the existing text.
    # --------------------------------------------------------

    pyautogui.hotkey(
        "ctrl",
        "a"
    )

    time.sleep(
        random.uniform(0.3, 0.5)
    )

    # --------------------------------------------------------
    # Type ONLY the sheet name
    # --------------------------------------------------------

    print(
        f"Typing '{sheet_name}'..."
    )

    type_like_writer(
        sheet_name
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
        f"{sheet_name} sheet selected."
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
# TYPE INTO CURRENT CELL
# ============================================================

def type_cell_value(value):

    print(
        f"Typing: {value}"
    )

    type_like_writer(
        str(value)
    )

    time.sleep(
        random.uniform(0.4, 0.8)
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Commit the cell before using arrow keys.
    # --------------------------------------------------------

    pyautogui.press(
        "enter"
    )

    time.sleep(
        random.uniform(0.8, 1.2)
    )


# ============================================================
# PART 2 — APPLE LAPTOP
# ============================================================

def part2_apple_laptop():

    print()
    print("=" * 60)
    print("PART 2 — APPLE LAPTOP")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. MAKE SURE WE ARE ON REIMBURSEMENT
    # --------------------------------------------------------

    print(
        "Making sure Reimbursement sheet is active..."
    )

    go_to_sheet(
        "Reimbursement"
    )

    time.sleep(
        random.uniform(0.8, 1.3)
    )

    # --------------------------------------------------------
    # 2. SELECT APPLE LAPTOP QUANTITY C2
    # --------------------------------------------------------

    print(
        "Selecting Apple Laptop quantity C2..."
    )

    click_cell(
        APPLE_QTY
    )

    # --------------------------------------------------------
    # 3. TYPE QUANTITY = 1
    # --------------------------------------------------------

    print(
        "Entering Apple Laptop quantity: 1"
    )

    type_cell_value(
        1
    )

    # --------------------------------------------------------
    # 4. AFTER ENTER:
    #
    # Selection is now C3.
    #
    # Use arrow keys:
    #
    # C3
    # ↑
    # C2
    # →
    # D2
    #
    # No mouse is used here.
    # --------------------------------------------------------

    print(
        "Navigating to Apple Laptop unit price..."
    )

    pyautogui.press(
        "up"
    )

    time.sleep(
        random.uniform(0.4, 0.7)
    )

    pyautogui.press(
        "right"
    )

    time.sleep(
        random.uniform(0.7, 1.1)
    )

    # --------------------------------------------------------
    # 5. TYPE UNIT PRICE = 1299
    # --------------------------------------------------------

    print(
        "Entering Apple Laptop unit price: 1299"
    )

    type_cell_value(
        1299
    )

    # --------------------------------------------------------
    # 6. AFTER ENTER:
    #
    # Selection is now D3.
    #
    # Use arrow keys:
    #
    # D3
    # ↑
    # D2
    # →
    # E2
    # →
    # F2
    #
    # No mouse is used.
    # --------------------------------------------------------

    print(
        "Navigating to Apple Laptop approval status..."
    )

    pyautogui.press(
        "up"
    )

    time.sleep(
        random.uniform(0.4, 0.6)
    )

    pyautogui.press(
        "right"
    )

    time.sleep(
        random.uniform(0.4, 0.6)
    )

    pyautogui.press(
        "right"
    )

    time.sleep(
        random.uniform(0.7, 1.1)
    )

    # --------------------------------------------------------
    # 7. CHANGE PENDING → APPROVED
    # --------------------------------------------------------

    print(
        "Changing Apple Laptop status to Approved..."
    )

    type_cell_value(
        "Approved"
    )

    time.sleep(
        random.uniform(1.0, 1.5)
    )

    # --------------------------------------------------------
    # 8. RECALCULATE
    # --------------------------------------------------------

    print(
        "Recalculating Reimbursement sheet..."
    )

    pyautogui.press(
        "f9"
    )

    time.sleep(
        random.uniform(1.0, 1.5)
    )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PART 2 COMPLETED")
    print("=" * 60)

    print(
        "Apple Laptop"
    )

    print(
        "Qty      = 1"
    )

    print(
        "Unit Price = 1299"
    )

    print(
        "Status   = Approved"
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("SPREADSHEET PART 2 STARTING")
    print("=" * 60)

    try:

        # The spreadsheet should already be open.
        part2_apple_laptop()

        print()
        print("=" * 60)
        print("PART 2 FINISHED SUCCESSFULLY")
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
