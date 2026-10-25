import time
import random
import pyautogui
import os
import json

import human_io  # [FINALIST] shared human-like mouse + typing
import ui_find   # answers the Save As "replace existing file?" prompt


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
# RESEARCH OPTIONS (TITLE + COINGECKO / AP NEWS / CONCLUSION)
# ============================================================

DOCUMENTS = [
    {
        "title": 'Market Research Notes',
        "coingecko": 'CoinGecko: Reviewed Bitcoin and Ethereum rankings, market caps and 24h trading volumes.',
        "news": 'AP News: Followed coverage of US shares, inflation and interest rate expectations.',
        "conclusion": 'Takeaway: Compare crypto volatility with broader market sentiment before forming an outlook.'
    },
    {
        "title": 'Bitcoin Market Research',
        "coingecko": 'CoinGecko: Bitcoin price changes and trading volume are useful for spotting short term activity.',
        "news": 'AP News: Economic and financial headlines can influence investor appetite for risk.',
        "conclusion": 'Takeaway: Watch Bitcoin volatility alongside macroeconomic developments, not in isolation.'
    },
    {
        "title": 'Ethereum Research Notes',
        "coingecko": 'CoinGecko: Compared Ethereum with Bitcoin by market value, daily movement and volume.',
        "news": 'AP News: Technology and financial market reports provide context for changing sentiment.',
        "conclusion": 'Takeaway: A large market cap does not remove price risk, especially during uncertain conditions.'
    },
    {
        "title": 'Financial Market Brief',
        "coingecko": 'CoinGecko: Checked how crypto market rankings and 24h changes can shift over time.',
        "news": 'AP News: Monitored headlines on US stock markets and the wider economy.',
        "conclusion": 'Takeaway: Stocks and crypto both react to news, though their risks and drivers differ.'
    },
    {
        "title": 'Inflation Research Notes',
        "coingecko": 'CoinGecko: Reviewed recent crypto market activity and its short term price swings.',
        "news": 'AP News: Looked for reporting on consumer prices, energy costs and borrowing conditions.',
        "conclusion": 'Takeaway: Inflation surprises may affect interest rate forecasts and the valuation of risky assets.'
    },
    {
        "title": 'Energy Market Research',
        "coingecko": 'CoinGecko: Noted changes in crypto trading volume as one measure of market activity.',
        "news": 'AP News: Followed oil price and energy market headlines for economic context.',
        "conclusion": 'Takeaway: Higher energy costs can add inflation pressure and influence financial market sentiment.'
    },
    {
        "title": 'Investor Sentiment Notes',
        "coingecko": 'CoinGecko: Compared daily crypto price movements with their trading volumes.',
        "news": 'AP News: Followed market coverage about company results and investor confidence.',
        "conclusion": 'Takeaway: Strong price movement alone is not enough to judge whether a trend will continue.'
    },
    {
        "title": 'Market Risk Research',
        "coingecko": 'CoinGecko: Checked whether major coins and smaller tokens have different market sizes.',
        "news": 'AP News: Read financial headlines involving economic uncertainty and market fluctuations.',
        "conclusion": 'Takeaway: Liquidity, market size and changing news can all influence investment risk.'
    },
    {
        "title": 'Stocks and Crypto Notes',
        "coingecko": 'CoinGecko: Reviewed Bitcoin and Ethereum as indicators of large crypto asset activity.',
        "news": 'AP News: Looked at coverage of US equity indexes and corporate earnings.',
        "conclusion": 'Takeaway: Equity returns depend on business performance, while crypto has different valuation drivers.'
    },
    {
        "title": 'Daily Research Summary',
        "coingecko": 'CoinGecko: Used rankings, daily percentage changes and volume as key reference fields.',
        "news": 'AP News: Focused on financial news about inflation, interest rates and stock markets.',
        "conclusion": 'Takeaway: Combine market data with credible news coverage before drafting a financial report.'
    },
]

# Record which option was selected so Part 2 continues the SAME document.
SESSION_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "research_notes_session.json")

# ============================================================
# TYPING FUNCTIONS
# ============================================================

def type_text(text):
    """
    Type a complete sentence/paragraph like a person.

    [FINALIST] Delegates to human_io.human_type: variable per-character
    delays, longer pauses at spaces/punctuation, occasional neighbouring-key
    typo + Backspace + correction, and slower typing for numbers / symbols.
    Research Notes Part 2 imports this same function.
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

def type_document(btc_price=None):
    """Stage 1: write the title and ONLY the CoinGecko information.

    [FINALIST] btc_price: the Bitcoin price copied from CoinGecko, passed
    in memory by the orchestrator (e.g. "67,412"). None = original text only.
    """

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

    for paragraph in [document["coingecko"]]:

        type_text(paragraph)

        # [FINALIST] One real value from the web, appended to the paragraph.
        if btc_price:
            type_text(
                f" Bitcoin was trading at around ${btc_price} at the time of writing."
            )

        pyautogui.press("enter")
        pyautogui.press("enter")

        human_io.human_pause(
            MIN_PARAGRAPH_PAUSE,
            MAX_PARAGRAPH_PAUSE
        )

    print(
        "CoinGecko notes completed."
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

    return f"{filename}.odt"
    
# ============================================================
# PART 1 — COINGECKO NOTES ONLY
# ============================================================

def run_research_notes_part1():
    print("=" * 60)
    print("RESEARCH NOTES — PART 1: COINGECKO")
    print("=" * 60)
    print(f"Starting in {START_DELAY} seconds...")
    time.sleep(START_DELAY)

    try:
        # 1. Open Writer (keep maximized — no split screen).
        open_openoffice_writer()

        # 2. Choose one of the 10 original note options at random.
        #    Type ONLY its title and CoinGecko paragraph.
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
