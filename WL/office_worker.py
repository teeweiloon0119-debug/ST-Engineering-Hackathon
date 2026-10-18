import time
import random
import pyautogui
import ctypes
from ctypes import wintypes
import os


# ============================================================
# SETTINGS
# ============================================================

START_DELAY = 5
APP_LOAD_DELAY = 6

# Typing speed
MIN_CHAR_DELAY = 0.07
MAX_CHAR_DELAY = 0.20

# Pause between words
MIN_WORD_PAUSE = 0.08
MAX_WORD_PAUSE = 0.40

# Probability of typo
TYPO_PROBABILITY = 0.07

# Pause after making a typo
MIN_CORRECTION_PAUSE = 0.35
MAX_CORRECTION_PAUSE = 1.00

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

def random_typing_delay():
    """
    Generate a variable delay between keystrokes.
    """

    return random.uniform(
        MIN_CHAR_DELAY,
        MAX_CHAR_DELAY
    )


def generate_typo(word):
    """
    Generate a simple neighbouring-key typo.

    Returns:
        typo_position
        original_character
        incorrect_character
    """

    neighbours = {
        "q": "w",
        "w": "e",
        "e": "r",
        "r": "t",
        "t": "y",
        "y": "u",
        "u": "i",
        "i": "o",
        "o": "p",

        "a": "s",
        "s": "d",
        "d": "f",
        "f": "g",
        "g": "h",
        "h": "j",
        "j": "k",
        "k": "l",

        "z": "x",
        "x": "c",
        "c": "v",
        "v": "b",
        "b": "n",
        "n": "m"
    }

    possible_positions = []

    for i, character in enumerate(word):

        if character.lower() in neighbours:
            possible_positions.append(i)

    if not possible_positions:
        return None, None, None

    position = random.choice(
        possible_positions
    )

    original = word[position]

    incorrect = neighbours[
        original.lower()
    ]

    if original.isupper():
        incorrect = incorrect.upper()

    return position, original, incorrect


def type_character(character):
    """
    Type one character and wait a variable amount of time.
    """

    pyautogui.write(character)

    time.sleep(
        random_typing_delay()
    )


def type_word_with_possible_typo(word):
    """
    Type a word.

    If a typo occurs:

        correct text
             ↓
        wrong character
             ↓
          pause
             ↓
        backspace
             ↓
        correct character
             ↓
        continue typing
    """

    make_typo = (
        len(word) >= 3
        and random.random() < TYPO_PROBABILITY
    )

    if not make_typo:

        for character in word:
            type_character(character)

        return


    position, original, incorrect = generate_typo(word)

    if position is None:

        for character in word:
            type_character(character)

        return


    # --------------------------------------------------------
    # Type until the typo position
    # --------------------------------------------------------

    for i in range(position):

        type_character(
            word[i]
        )


    # --------------------------------------------------------
    # Type incorrect character
    # --------------------------------------------------------

    type_character(
        incorrect
    )


    # --------------------------------------------------------
    # Pause before correcting
    # --------------------------------------------------------

    time.sleep(
        random.uniform(
            MIN_CORRECTION_PAUSE,
            MAX_CORRECTION_PAUSE
        )
    )


    # --------------------------------------------------------
    # Delete incorrect character
    # --------------------------------------------------------

    pyautogui.press("backspace")

    time.sleep(
        random.uniform(
            0.1,
            0.3
        )
    )


    # --------------------------------------------------------
    # Type correct character
    # --------------------------------------------------------

    type_character(
        original
    )


    # --------------------------------------------------------
    # Continue with the rest of the word
    # --------------------------------------------------------

    for i in range(
        position + 1,
        len(word)
    ):

        type_character(
            word[i]
        )


def type_text(text):
    """
    Type a complete sentence/paragraph word by word.
    """

    words = text.split(" ")

    for index, word in enumerate(words):

        type_word_with_possible_typo(
            word
        )

        # Add space between words
        if index < len(words) - 1:

            pyautogui.press("space")

            time.sleep(
                random.uniform(
                    MIN_WORD_PAUSE,
                    MAX_WORD_PAUSE
                )
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

    pyautogui.write(
        "OpenOffice Writer",
        interval=0.15
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

def format_title_with_mouse():

    print("Formatting title...")

    # ========================================================
    # SELECT TITLE
    # ========================================================

    pyautogui.click(
        259,
        258,
        clicks=4,
        interval=0.20
    )

    time.sleep(1.0)

    # ========================================================
    # BOLD
    # ========================================================

    pyautogui.moveTo(
        430,
        86,
        duration=0.4
    )

    time.sleep(0.6)

    pyautogui.click()

    time.sleep(1.0)

    # ========================================================
    # FONT SIZE
    # ========================================================

    pyautogui.moveTo(
        375,
        95,
        duration=0.4
    )

    time.sleep(0.6)

    pyautogui.click()

    time.sleep(0.6)

    # Delete the existing font size
    pyautogui.press(
        "backspace",
        presses=2,
        interval=0.2
    )

    time.sleep(0.6)

    # Enter 18
    pyautogui.write(
        "18",
        interval=0.15
    )

    time.sleep(0.6)

    pyautogui.press("enter")

    time.sleep(1.5)

    print("Title formatting completed: Bold, 18 pt.")

def reset_content_formatting():

    print("Resetting content formatting...")

    # ========================================================
    # UNBOLD
    # ========================================================

    pyautogui.moveTo(
        430,
        86,
        duration=0.4
    )

    time.sleep(0.6)

    pyautogui.click()

    time.sleep(1.0)

    # ========================================================
    # FONT SIZE BACK TO 12
    # ========================================================

    pyautogui.moveTo(
        375,
        95,
        duration=0.4
    )

    time.sleep(0.6)

    pyautogui.click()

    time.sleep(0.6)

    # Delete existing "18"
    pyautogui.press(
        "backspace",
        presses=2,
        interval=0.2
    )

    time.sleep(0.6)

    # Enter 12
    pyautogui.write(
        "12",
        interval=0.15
    )

    time.sleep(0.6)

    pyautogui.press("enter")

    time.sleep(1.5)

    print(
        "Content formatting reset: regular, 12 pt."
    )
    
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
    # FORMAT TITLE WITH MOUSE
    # --------------------------------------------------------

    format_title_with_mouse()

    # --------------------------------------------------------
    # CLICK AFTER TITLE
    # --------------------------------------------------------

    pyautogui.click(
        500,
        140
    )

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

        time.sleep(
            random.uniform(
                1.5,
                4.0
            )
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
    pyautogui.write(
        filename,
        interval=0.10
    )

    time.sleep(1)

    # Save
    pyautogui.press(
        "enter"
    )

    # Wait for save
    time.sleep(5)

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

    user32 = ctypes.WinDLL("user32")  # own instance [INTEGRATION]

    hwnd = user32.GetForegroundWindow()

    rect = wintypes.RECT()

    user32.GetWindowRect(
        hwnd,
        ctypes.byref(rect)
    )

    close_x = rect.right - 15
    close_y = rect.top + 15

    print(
        f"Moving mouse to close button: "
        f"({close_x}, {close_y})"
    )

    pyautogui.moveTo(
        close_x,
        close_y,
        duration=0.4
    )

    time.sleep(0.5)

    pyautogui.click()

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
