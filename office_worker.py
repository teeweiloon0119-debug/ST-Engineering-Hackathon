import time
import random
import pyautogui
import os

import human_io  # [FINALIST] shared human-like mouse + typing
import ui_find    # [FINALIST] locate real toolbar controls (UI Automation)


# ============================================================
# SETTINGS
# ============================================================

START_DELAY = 5
APP_LOAD_DELAY = 6

# Typing speed / word pauses / typo correction now live in human_io.

# Probability of typo (per word)
TYPO_PROBABILITY = 0.07

# Pause between paragraphs
MIN_PARAGRAPH_PAUSE = 1.5
MAX_PARAGRAPH_PAUSE = 4.0

pyautogui.FAILSAFE = True

# ============================================================
# DOCUMENT OPTIONS
# ============================================================

DOCUMENTS = [

    {
        "title": "Weekly Operations Meeting Notes",
        "paragraphs": [
            "Date: 12 October 2026",
            "Time: 10:00 AM | Location: Meeting Room 2",
            "Attendees: Department Manager, Finance Executive, Operations Executive, Secretary",
            "The meeting began with a review of the department's activities from the previous week.",
            "The team discussed two outstanding administrative tasks and the upcoming reporting deadline.",
            "The Finance Executive provided an update on the month's expenditure and pending invoices.",
            "Action Items: Operations team to complete outstanding tasks. Finance Executive to update the expenditure figures. Secretary to circulate the meeting notes.",
            "The meeting ended at 10:45 AM."
        ]
    },

    {
        "title": "Monthly Department Meeting Minutes",
        "paragraphs": [
            "Date: 12 October 2026",
            "Time: 2:00 PM | Location: Conference Room A",
            "Attendees: Department Manager, Team Leads, Finance Executive, Secretary",
            "The team reviewed the department's performance and activities for the month.",
            "Team leads provided updates on ongoing tasks and highlighted several items requiring follow-up.",
            "The Finance Executive presented the preliminary monthly expenditure figures.",
            "Action Items: Team leads to complete outstanding reports. Finance Executive to finalise the monthly figures. Secretary to prepare the next meeting agenda.",
            "The meeting concluded at 3:00 PM."
        ]
    },

    {
        "title": "Project Progress Meeting Notes",
        "paragraphs": [
            "Date: 12 October 2026",
            "Time: 11:30 AM | Location: Project Meeting Room",
            "Attendees: Project Manager, Project Team, Finance Representative, Secretary",
            "The Project Manager provided an update on the current project progress.",
            "The team discussed the remaining documentation and confirmed that the project remains on schedule.",
            "The Finance Representative confirmed that project spending remains within the current budget.",
            "Action Items: Project team to complete the outstanding documents. Finance Representative to update the expenditure record.",
            "The meeting ended at 12:15 PM."
        ]
    },

    {
        "title": "Finance and Administration Meeting Minutes",
        "paragraphs": [
            "Date: 12 October 2026",
            "Time: 9:30 AM | Location: Finance Meeting Room",
            "Attendees: Finance Manager, Accounts Executive, Operations Executive, Secretary",
            "The meeting focused on the department's monthly financial position.",
            "The Accounts Executive reviewed revenue, salaries, office supplies and other administrative expenses.",
            "The Finance Manager requested that all outstanding invoices be submitted before monthly closing.",
            "Action Items: Accounts Executive to finalise the monthly figures. Operations Executive to submit outstanding documents. Secretary to circulate the minutes.",
            "The meeting concluded at 10:15 AM."
        ]
    },

    {
        "title": "Team Coordination Meeting Notes",
        "paragraphs": [
            "Date: 12 October 2026",
            "Time: 3:30 PM | Location: Meeting Room 3",
            "Attendees: Department Manager, Operations Team, Finance Representative, Secretary",
            "The team reviewed the current workload and upcoming deadlines.",
            "The Operations Team provided updates on ongoing tasks and identified several items requiring follow-up.",
            "The Finance Representative reminded staff to submit pending expense claims before month-end.",
            "Action Items: Operations Team to complete outstanding tasks. Staff to submit expense claims. Secretary to prepare the next meeting schedule.",
            "The meeting ended at 4:15 PM."
        ]
    }
]


# ============================================================
# TYPING FUNCTIONS
# ============================================================

def type_text(text):
    """
    Type a complete sentence/paragraph like a person.

    [FINALIST] Delegates to human_io.human_type: variable per-character
    delays, longer pauses at spaces/punctuation, occasional neighbouring-key
    typo + Backspace + correction, and slower typing for numbers / symbols.
    """

    human_io.human_type(
        text,
        typo_rate=TYPO_PROBABILITY
    )


# ============================================================
# OPEN OPENOFFICE WRITER
# ============================================================

def open_openoffice_writer():

    print("Opening OpenOffice Writer...")

    pyautogui.press("win")

    time.sleep(
        random.uniform(0.8, 1.5)
    )

    human_io.human_type(
        "OpenOffice Writer",
        typo_rate=0
    )

    time.sleep(
        random.uniform(0.8, 1.5)
    )

    pyautogui.press("enter")

    time.sleep(APP_LOAD_DELAY)

    # Maximize the Windows application window
    pyautogui.hotkey(
        "alt",
        "space"
    )

    time.sleep(0.5)

    pyautogui.press("x")

    time.sleep(2)

    print(
        "OpenOffice Writer opened and maximized."
    )

def _writer_hwnd():
    """The Writer window to act on: located by title and brought to the front
    (OpenOffice only exposes its toolbar to UI Automation while in front)."""
    hwnd = ui_find.window_by_title("OpenOffice Writer") if ui_find.available() else 0
    if hwnd:
        ui_find.ensure_foreground(hwnd)
        return hwnd
    return ui_find.foreground_hwnd()


def _set_font_size(size):
    """Click the real Font Size box (UI Automation) and type a new size.
    Returns True if the box was found and used."""
    # OpenOffice exposes Font Size as a combo box (with an inner edit); click its
    # text field, not the drop-down arrow.
    box = ui_find.find_office(_writer_hwnd(), names=["Font Size"],
                              control_types=["ComboBoxControl", "EditControl"])
    if box is None or not ui_find.click_text_field(box):
        return False
    human_io.human_pause(0.2, 0.6)
    pyautogui.hotkey("ctrl", "a")          # select the current size
    human_io.human_pause(0.1, 0.3, think_prob=0)
    human_io.human_type(str(size), typo_rate=0)
    human_io.human_pause(0.2, 0.5)
    pyautogui.press("enter")               # applies and returns focus to the text
    human_io.human_pause(0.3, 0.8)
    return True


def _click_bold():
    """Click the real Bold toolbar button (UI Automation). Returns True/False."""
    # A toggle toolbar item can surface as a Button or a CheckBox via the bridge.
    bold = ui_find.find_office(_writer_hwnd(), names=["Bold"],
                               control_types=["ButtonControl", "CheckBoxControl"])
    return ui_find.click(bold)


def _select_title_with_mouse(title):
    """Triple-click the title paragraph (found via UI Automation) to select it:
    in Writer a triple-click selects the sentence, and the titles have no full
    stop, so that is the whole title. Returns True/False."""
    hwnd = _writer_hwnd()
    doc = ui_find.find_office(hwnd, control_types=["DocumentControl"], timeout=2.0,
                              label="Writer document")
    rect = ui_find.text_block_rect(doc, title) if doc is not None else None
    if not rect:
        return False
    # Land on the first word: the block spans the full line width, the text
    # itself only starts at its left edge.
    x = rect[0] + random.randint(6, max(7, min(45, (rect[2] - rect[0]) // 4)))
    y = (rect[1] + rect[3]) // 2 + random.randint(-2, 2)
    human_io.human_click(x, y, clicks=3)
    return True


def format_title(title=None):
    """Make the title bold and larger using the REAL toolbar controls, clicked
    with the human mouse (UI Automation). Falls back to the Heading 1 paragraph
    style (Ctrl+1) if the toolbar controls are not found."""
    print("Formatting title...")
    human_io.human_pause(0.6, 1.4)

    # Select the title with the mouse (triple-click on the real paragraph);
    # fallback: keyboard, the cursor is at the end of the just-typed title.
    selected = bool(title) and ui_find.available() and _select_title_with_mouse(title)
    if not selected:
        pyautogui.press("home")
        human_io.human_pause(0.2, 0.5, think_prob=0)
        pyautogui.hotkey("shift", "end")
    human_io.human_pause(0.3, 0.8)

    used_toolbar = False
    if ui_find.available():
        bold_ok = _click_bold()
        human_io.human_pause(0.4, 1.0)
        size_ok = _set_font_size(18)
        used_toolbar = bold_ok and size_ok

    if not used_toolbar:
        # Fallback: Heading 1 paragraph style (keyboard, no pixels).
        pyautogui.hotkey("ctrl", "1")
        human_io.human_pause(0.4, 1.0)
        print("Title formatting completed: Heading 1 (fallback).")
        return

    print("Title formatting completed: Bold, 18 pt (toolbar).")


def reset_content_formatting():
    """Return to normal body text before typing the notes."""
    print("Resetting content formatting...")

    used_toolbar = False
    if ui_find.available():
        # Turn Bold back off and set the size back to 12 via the toolbar.
        bold_ok = _click_bold()
        human_io.human_pause(0.4, 1.0)
        size_ok = _set_font_size(12)
        used_toolbar = bold_ok and size_ok

    if not used_toolbar:
        pyautogui.hotkey("ctrl", "0")      # Text Body paragraph style (fallback)
        human_io.human_pause(0.4, 1.0)
        print("Content formatting reset: Text Body (fallback).")
        return

    print("Content formatting reset: regular, 12 pt (toolbar).")
    
def type_document():

    document = random.choice(DOCUMENTS)

    print(
        f"Selected document: {document['title']}"
    )

    # --------------------------------------------------------
    # TYPE TITLE
    # --------------------------------------------------------

    type_text(
        document["title"]
    )

    time.sleep(0.5)

    # --------------------------------------------------------
    # FORMAT TITLE (MOUSE ON REAL CONTROLS, NO PIXEL POSITIONS)
    # --------------------------------------------------------

    format_title(document["title"])

    # The cursor is still on the title line: no click needed to leave it.
    pyautogui.press("end")
    pyautogui.press("enter")
    pyautogui.press("enter")

    time.sleep(
        random.uniform(
            1.0,
            2.5
        )
    )

    reset_content_formatting()

    # --------------------------------------------------------
    # TYPE PARAGRAPHS
    # --------------------------------------------------------

    for paragraph in document["paragraphs"]:

        type_text(paragraph)

        pyautogui.press("enter")
        pyautogui.press("enter")

        human_io.human_pause(
            MIN_PARAGRAPH_PAUSE,
            MAX_PARAGRAPH_PAUSE
        )

    print(
        "Document typing completed."
    )
    
# ============================================================
# SAVE DOCUMENT
# ============================================================

def realistic_filename(base, folder):
    """'Meeting Notes', or 'Meeting Notes 18 Oct' (then '... (2)') if taken."""

    if not os.path.exists(os.path.join(folder, f"{base}.odt")):
        return base

    now = time.localtime()
    dated = f"{base} {now.tm_mday} {time.strftime('%b', now)}"
    name, n = dated, 2

    while os.path.exists(os.path.join(folder, f"{name}.odt")):
        name = f"{dated} ({n})"
        n += 1

    return name


def save_document():

    print("Opening Save As...")

    pyautogui.hotkey(
        "ctrl",
        "shift",
        "s"
    )

    time.sleep(3)

    # ========================================================
    # PICK A REALISTIC FILE NAME  [INTEGRATION: was Notes{n}]
    # ========================================================

    desktop = os.path.join(
        os.path.expanduser("~"),
        "Desktop"
    )

    filename = realistic_filename("Meeting Notes", desktop)

    print(
        f"Saving as: {filename}.odt"
    )

    # ========================================================
    # FILE NAME BOX
    # ========================================================

    # Focus the File name field
    pyautogui.hotkey(
        "alt",
        "n"
    )

    time.sleep(0.5)

    # Select the existing filename
    pyautogui.hotkey(
        "ctrl",
        "a"
    )

    # Type filename only
    human_io.human_type(
        filename
    )

    time.sleep(1)

    # Save
    pyautogui.press(
        "enter"
    )

    # Same name already on the Desktop? Answer the replace prompt with Yes.
    ui_find.confirm_replace_if_asked()

    # Wait for save
    time.sleep(3)

    print(
        f"Document saved as {filename}.odt"
    )
    
# ============================================================
# CLOSE WRITER
# ============================================================

def close_writer():

    print("Closing OpenOffice Writer...")

    time.sleep(
        random.uniform(1.0, 2.0)
    )

    # Alt+F4 on the Writer window in front (no close-button pixel).
    human_io.close_foreground_window()

    time.sleep(4)

    print("OpenOffice Writer closed.")
    
# ============================================================
# MAIN OFFICE WORKER
# ============================================================

def run_office_worker():

    print("=" * 60)
    print("OFFICE WORKER STARTING")
    print("=" * 60)

    print(
        f"Starting in {START_DELAY} seconds..."
    )

    time.sleep(
        START_DELAY
    )

    try:

        # 1. Open Writer
        open_openoffice_writer()

        # 2. Type document
        type_document()

        # 3. Save document
        save_document()

        # 4. Close Writer
        close_writer()

        print("=" * 60)
        print("OFFICE WORKER COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except pyautogui.FailSafeException:

        print(
            "Emergency stop activated."
        )

    except Exception as error:

        print("=" * 60)
        print("ERROR")
        print("=" * 60)

        print(error)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    run_office_worker()
