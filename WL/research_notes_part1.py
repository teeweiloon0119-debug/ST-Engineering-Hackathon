import time
import random
import pyautogui
import os
import json


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
# RESEARCH OPTIONS (TITLE + COINMARKETCAP / AP NEWS / CONCLUSION)
# ============================================================

DOCUMENTS = [
    {
        "title": 'Market Research Notes',
        "coinmarketcap": 'CoinMarketCap: Reviewed Bitcoin and Ethereum rankings, market caps and 24h trading volumes.',
        "news": 'AP News: Followed coverage of US shares, inflation and interest rate expectations.',
        "conclusion": 'Takeaway: Compare crypto volatility with broader market sentiment before forming an outlook.'
    },
    {
        "title": 'Bitcoin Market Research',
        "coinmarketcap": 'CoinMarketCap: Bitcoin price changes and trading volume are useful for spotting short term activity.',
        "news": 'AP News: Economic and financial headlines can influence investor appetite for risk.',
        "conclusion": 'Takeaway: Watch Bitcoin volatility alongside macroeconomic developments, not in isolation.'
    },
    {
        "title": 'Ethereum Research Notes',
        "coinmarketcap": 'CoinMarketCap: Compared Ethereum with Bitcoin by market value, daily movement and volume.',
        "news": 'AP News: Technology and financial market reports provide context for changing sentiment.',
        "conclusion": 'Takeaway: A large market cap does not remove price risk, especially during uncertain conditions.'
    },
    {
        "title": 'Financial Market Brief',
        "coinmarketcap": 'CoinMarketCap: Checked how crypto market rankings and 24h changes can shift over time.',
        "news": 'AP News: Monitored headlines on US stock markets and the wider economy.',
        "conclusion": 'Takeaway: Stocks and crypto both react to news, though their risks and drivers differ.'
    },
    {
        "title": 'Inflation Research Notes',
        "coinmarketcap": 'CoinMarketCap: Reviewed recent crypto market activity and its short term price swings.',
        "news": 'AP News: Looked for reporting on consumer prices, energy costs and borrowing conditions.',
        "conclusion": 'Takeaway: Inflation surprises may affect interest rate forecasts and the valuation of risky assets.'
    },
    {
        "title": 'Energy Market Research',
        "coinmarketcap": 'CoinMarketCap: Noted changes in crypto trading volume as one measure of market activity.',
        "news": 'AP News: Followed oil price and energy market headlines for economic context.',
        "conclusion": 'Takeaway: Higher energy costs can add inflation pressure and influence financial market sentiment.'
    },
    {
        "title": 'Investor Sentiment Notes',
        "coinmarketcap": 'CoinMarketCap: Compared daily crypto price movements with their trading volumes.',
        "news": 'AP News: Followed market coverage about company results and investor confidence.',
        "conclusion": 'Takeaway: Strong price movement alone is not enough to judge whether a trend will continue.'
    },
    {
        "title": 'Market Risk Research',
        "coinmarketcap": 'CoinMarketCap: Checked whether major coins and smaller tokens have different market sizes.',
        "news": 'AP News: Read financial headlines involving economic uncertainty and market fluctuations.',
        "conclusion": 'Takeaway: Liquidity, market size and changing news can all influence investment risk.'
    },
    {
        "title": 'Stocks and Crypto Notes',
        "coinmarketcap": 'CoinMarketCap: Reviewed Bitcoin and Ethereum as indicators of large crypto asset activity.',
        "news": 'AP News: Looked at coverage of US equity indexes and corporate earnings.',
        "conclusion": 'Takeaway: Equity returns depend on business performance, while crypto has different valuation drivers.'
    },
    {
        "title": 'Daily Research Summary',
        "coinmarketcap": 'CoinMarketCap: Used rankings, daily percentage changes and volume as key reference fields.',
        "news": 'AP News: Focused on financial news about inflation, interest rates and stock markets.',
        "conclusion": 'Takeaway: Combine market data with credible news coverage before drafting a financial report.'
    },
]

# Record which option was selected so Part 2 continues the SAME document.
SESSION_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "research_notes_session.json")

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

def type_document():
    """Stage 1: write the title and ONLY the CoinMarketCap information."""

    document_index = random.randrange(len(DOCUMENTS))
    document = DOCUMENTS[document_index]

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
    # START NOTES UNDER TITLE (DEFAULT WRITER FORMATTING)
    # --------------------------------------------------------

    pyautogui.press("enter")
    pyautogui.press("enter")

    time.sleep(
        random.uniform(
            1.0,
            2.5
        )
    )

    # --------------------------------------------------------
    # TYPE PARAGRAPHS
    # --------------------------------------------------------

    for paragraph in [document["coinmarketcap"]]:

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
        "CoinMarketCap notes completed."
    )

    return document_index
    
# ============================================================
# SAVE DOCUMENT
# ============================================================

def realistic_filename(base, folder):
    """'Research Notes', or 'Research Notes 18 Oct' (then '... (2)') if taken."""

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
    # PICK A REALISTIC FILE NAME  [INTEGRATION: was Research_Notes{n}]
    # ========================================================

    desktop = os.path.join(
        os.path.expanduser("~"),
        "Desktop"
    )

    filename = realistic_filename("Research Notes", desktop)

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

    return f"{filename}.odt"
    
# ============================================================
# PART 1 — COINMARKETCAP NOTES ONLY
# ============================================================

def run_research_notes_part1():
    print("=" * 60)
    print("RESEARCH NOTES — PART 1: COINMARKETCAP")
    print("=" * 60)
    print(f"Starting in {START_DELAY} seconds...")
    time.sleep(START_DELAY)

    try:
        # 1. Open Writer (keep maximized — no split screen).
        open_openoffice_writer()

        # 2. Choose one of the 10 original note options at random.
        #    Type ONLY its title and CoinMarketCap paragraph.
        document_index = type_document()

        # 3. Save once, so Part 2 can use Ctrl+S to update the same file.
        filename = save_document()

        # 4. Remember the chosen topic and saved filename for Part 2.
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"document_index": document_index,
                       "filename": filename}, f, indent=2)

        print(f"Part 1 done — {filename} remains OPEN in Writer.")
        print("Next: run Research_Notes_Part2_APNews.py")

    except pyautogui.FailSafeException:
        print("Emergency stop activated.")
    except Exception as error:
        print("ERROR:", error)


if __name__ == "__main__":
    run_research_notes_part1()
