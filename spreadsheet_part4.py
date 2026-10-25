import time
import random
import pyautogui

import human_io  # [FINALIST] shared human-like mouse + typing
from calc_nav import focus_name_box, go_to_sheet, go_to_cell as calc_go_to_cell


# ============================================================
# SETTINGS
# ============================================================

# Summary sheet → Reimbursement total → F23
SUMMARY_F23 = "F23"

# Summary sheet → Net Earnings → F31
SUMMARY_F31 = "F31"


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
# GO TO SUMMARY SHEET
# ============================================================

def go_to_summary():
    # Clicks the real Summary tab via UI Automation (calc_nav), falling back to
    # typing "Summary" into the Name Box.
    print(
        "Navigating to Summary sheet..."
    )
    go_to_sheet("Summary")


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

def close_calc():

    print(
        "Preparing to close Calc..."
    )

    time.sleep(
        random.uniform(1.0, 2.0)
    )

    # Alt+F4 on the Calc window in front (no close-button pixel).
    print(
        "Closing Calc..."
    )

    human_io.close_foreground_window()

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

    go_to_cell(
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
# Calculate Net Earnings in F31 = F28 - F30
#
# [FINALIST] The references are TYPED instead of clicked: pointing
# at cells mid-formula can't go through the Name Box (clicking it
# would leave formula entry), and the old pixel clicks broke on any
# resolution / scroll change. The resulting formula is identical.
# --------------------------------------------------------

    print(
        "Calculating Net Earnings..."
    )

    # Select F31
    go_to_cell(
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
# Reference → F28
# Earnings Before Taxes
# --------------------------------------------------------

    print(
        "Referencing Earnings Before Taxes F28..."
    )

    type_like_writer(
        "F28"
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
# Reference → F30
# Income Taxes
# --------------------------------------------------------

    print(
        "Referencing Income Taxes F30..."
    )

    type_like_writer(
        "F30"
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
    # CLOSE (ALT+F4)
    # --------------------------------------------------------

    close_calc()

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
