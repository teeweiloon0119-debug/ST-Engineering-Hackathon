import time
import random
import pyautogui

import human_io  # [FINALIST] shared human-like mouse + typing
from calc_nav import focus_name_box, go_to_cell as calc_go_to_cell


# ============================================================
# SETTINGS
# ============================================================

# External SSD Quantity - C5
EXTERNAL_SSD_QTY = "C5"


# Typing speed now lives in human_io (content-aware).

pyautogui.FAILSAFE = True


# ============================================================
# WRITER-STYLE TYPING
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

    go_to_cell(
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
