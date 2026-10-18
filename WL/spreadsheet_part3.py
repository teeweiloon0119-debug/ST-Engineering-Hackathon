import time
import random
import pyautogui


# ============================================================
# SETTINGS
# ============================================================

# OpenOffice Calc Name Box
NAME_BOX = (37, 126)

# External SSD Quantity - C5
EXTERNAL_SSD_QTY = (340, 235)


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

    # Commit the cell before using arrow keys
    pyautogui.press(
        "enter"
    )

    time.sleep(
        random.uniform(0.8, 1.2)
    )


# ============================================================
# PART 3 — EXTERNAL SSD
# ============================================================

def part3_external_ssd():

    print()
    print("=" * 60)
    print("PART 3 — EXTERNAL SSD")
    print("=" * 60)

    # --------------------------------------------------------
    # 2. SELECT EXTERNAL SSD QUANTITY C5
    # --------------------------------------------------------

    print(
        "Selecting External SSD quantity C5..."
    )

    click_cell(
        EXTERNAL_SSD_QTY
    )

    # --------------------------------------------------------
    # 3. TYPE QUANTITY = 1
    # --------------------------------------------------------

    print(
        "Entering External SSD quantity: 1"
    )

    type_cell_value(
        1
    )

    # --------------------------------------------------------
    # 4. AFTER ENTER:
    #
    # Selection is now C6.
    #
    # Use arrow keys:
    #
    # C6
    # ↑
    # C5
    # →
    # D5
    #
    # --------------------------------------------------------

    print(
        "Navigating to External SSD unit price..."
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
    # 5. TYPE UNIT PRICE = 60
    # --------------------------------------------------------

    print(
        "Entering External SSD unit price: 60"
    )

    type_cell_value(
        60
    )

    # --------------------------------------------------------
    # 6. AFTER ENTER:
    #
    # Selection is now D6.
    #
    # Use arrow keys:
    #
    # D6
    # ↑
    # D5
    # →
    # E5
    # →
    # F5
    #
    # --------------------------------------------------------

    print(
        "Navigating to External SSD approval status..."
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
        "Changing External SSD status to Approved..."
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
    print("PART 3 COMPLETED")
    print("=" * 60)

    print(
        "External SSD"
    )

    print(
        "Qty        = 1"
    )

    print(
        "Unit Price = 60"
    )

    print(
        "Status     = Approved"
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("SPREADSHEET PART 3 STARTING")
    print("=" * 60)

    try:

        # The spreadsheet should already be open.
        # The code will first navigate to Reimbursement.
        part3_external_ssd()

        print()
        print("=" * 60)
        print("PART 3 FINISHED SUCCESSFULLY")
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
