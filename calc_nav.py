"""
calc_nav - the ONE place that knows how to reach Calc's Name Box, sheet tabs
and cells.

Primary path uses Windows UI Automation (ui_find): the agent clicks the REAL
"Name Box" control, the REAL sheet tab and the REAL cell (read from the grid's
accessible object by index), with the human mouse. No pixel positions. If UIA is unavailable or
a control is not found, it falls back to the Name Box and finally to a
configurable pixel click, so the spreadsheet steps still run.
"""

import re

import pyautogui

import human_io
import ui_find

# Last-resort pixel click for the Name Box, used only if UIA cannot find it.
# The Name Box sits at the top-left of the formula bar, which stays in roughly
# the same place across resolutions (toolbars are top/left-anchored), so this is
# a reasonable fallback. Set to None to disable.
NAME_BOX_CLICK_XY = (37, 126)

CALC_TITLE = "OpenOffice Calc"

# Calc's grid: the accessible spreadsheet table (walk stops AT it, never inside).
_GRID_TYPES = ["TableControl", "DataGridControl"]
_ADDRESS = re.compile(r"^([A-Z]{1,3})([0-9]{1,7})$")


def _calc_hwnd():
    """Locate the Calc window by title and bring it to the front (OpenOffice only
    exposes its controls to UI Automation while in front). Falls back to the
    window currently in front."""
    hwnd = ui_find.window_by_title(CALC_TITLE) if ui_find.available() else 0
    if hwnd:
        ui_find.ensure_foreground(hwnd)
        return hwnd
    return ui_find.foreground_hwnd()


def focus_name_box():
    """Put the cursor in Calc's Name Box with its text selected, so the next
    thing typed (a sheet name or cell address) replaces it."""
    hwnd = _calc_hwnd()
    clicked = False

    if ui_find.available():
        # OpenOffice exposes the Name Box as a COMBO box named "Name Box" on the
        # Formula tool bar; click its text field, not the drop-down arrow.
        box = ui_find.find_office(hwnd, names=["Name Box"],
                                  control_types=["ComboBoxControl", "EditControl"])
        clicked = ui_find.click_text_field(box)

    if not clicked and NAME_BOX_CLICK_XY:
        human_io.human_click(*NAME_BOX_CLICK_XY)
        clicked = True

    human_io.human_pause(0.3, 0.9)
    pyautogui.hotkey("ctrl", "a")      # select the current reference
    human_io.human_pause(0.2, 0.6)


def go_to_sheet(sheet_name):
    """Switch to a sheet. Preferred: click its tab (what a person does, and it
    reads as 'clicking into data'). Fallback: type the name into the Name Box."""
    hwnd = _calc_hwnd()

    if ui_find.available():
        # The tab bar is narrow: with the last sheets in view, the first tab
        # (Summary) is scrolled out of it. Click the tab bar's real "Move Left"
        # arrow until the tab is fully in view, like a person would.
        for attempt in range(5):
            tab, direction = _visible_tab(hwnd, sheet_name)
            if tab is not None:
                if ui_find.click_rect(tab):
                    human_io.human_pause(0.6, 1.4)
                    return
                break
            if attempt == 4 or not _scroll_tabs(hwnd, direction):
                break

    # Fallback: Name Box accepts a sheet name and jumps to it.
    focus_name_box()
    human_io.human_type(str(sheet_name), typo_rate=0)
    human_io.human_pause(0.4, 0.9)
    pyautogui.press("enter")
    human_io.human_pause(0.8, 1.6)


def _visible_tab(hwnd, sheet_name):
    """(rect, None) if the sheet's tab is fully inside the tab bar; otherwise
    (None, 'Move Left' / 'Move Right'), the arrow that brings it into view
    (a tab that is not listed at all is assumed scrolled off to the left).
    The tab bar sits beside the grid inside the document view, so only the
    grid itself is skipped by the lookup."""
    tab = ui_find.find_office(hwnd, names=[sheet_name], control_types=["TabItemControl"],
                              skip_into=_GRID_TYPES, timeout=2.0, label=f"sheet tab {sheet_name!r}")
    rect = ui_find.rect_of(tab) if tab is not None else None
    if rect is None:
        return None, "Move Left"
    try:
        bar = ui_find.rect_of(tab.GetParentControl())
    except Exception:
        bar = None
    if bar and rect[0] < bar[0] - 2:
        print(f"[uia] sheet tab {sheet_name!r} {rect} is cut off on the left of the tab bar {bar}")
        return None, "Move Left"
    if bar and rect[2] > bar[2] + 2:
        print(f"[uia] sheet tab {sheet_name!r} {rect} is cut off on the right of the tab bar {bar}")
        return None, "Move Right"
    return rect, None


def _scroll_tabs(hwnd, arrow_name):
    """Click the tab bar's real 'Move Left' / 'Move Right' arrow once.
    Returns True if clicked."""
    arrow = ui_find.find_office(hwnd, names=[arrow_name], control_types=["ButtonControl"],
                                skip_into=_GRID_TYPES, timeout=2.0, label=f"tab bar {arrow_name}")
    if arrow is None or not ui_find.click(arrow):
        return False
    human_io.human_pause(0.4, 0.9)
    return True


# =====================================================================
# CELLS
# =====================================================================

def _parse_address(address):
    """'F19' -> (6, 19); None if it is not a plain cell address."""
    m = _ADDRESS.match(str(address).strip().upper().replace("$", ""))
    if not m:
        return None
    col = 0
    for ch in m.group(1):
        col = col * 26 + (ord(ch) - 64)
    return col, int(m.group(2))


def _address_in(name):
    """(col, row) of the cell address in an accessible name ('E4' / 'Cell E4')."""
    for token in re.split(r"[^A-Z0-9$]+", (name or "").upper()):
        pos = _parse_address(token)
        if pos:
            return pos
    return None


# Calc numbers its cells as the grid's children row by row across the WHOLE
# sheet: index = (row-1) * columns + (col-1). Apache OpenOffice 4 has 1024
# columns; the others are tried once and the one that works is remembered.
_SHEET_WIDTHS = [1024, 256, 16384]


def _cell_by_index(grid, target):
    """(name, rect) of a cell, fetched straight from the grid's accessible
    object by index, or None. The name is checked against the target, so a
    wrong index guess can never click the wrong cell."""
    try:
        grid_acc = grid.GetLegacyIAccessiblePattern().pattern.GetIAccessible()
        try:
            from comtypes.gen.Accessibility import IAccessible
        except ImportError:
            import comtypes.client
            IAccessible = comtypes.client.GetModule("oleacc.dll").IAccessible
    except Exception as error:
        print(f"[uia] grid IAccessible unavailable ({error!r})")
        return None
    col, row = target
    for width in list(_SHEET_WIDTHS):
        index = (row - 1) * width + (col - 1)
        for child_id in (index + 1, index):     # MSAA child ids are usually 1-based
            try:
                try:                            # cell as its own object ...
                    cell, cid = grid_acc.accChild(child_id).QueryInterface(IAccessible), 0
                except Exception:               # ... or as a simple child of the grid
                    cell, cid = grid_acc, child_id
                name = cell.accName(cid)
                if _address_in(name) != target:
                    continue
                left, top, width_px, height_px = cell.accLocation(cid)
            except Exception:
                continue
            _SHEET_WIDTHS.remove(width)
            _SHEET_WIDTHS.insert(0, width)      # remember the layout that worked
            return name, (left, top, left + width_px, top + height_px)
    return None


def _visible_cell_rect(hwnd, address):
    """On-screen rect of a cell (clipped to the visible grid), or None if it is
    scrolled out of view or cannot be read."""
    target = _parse_address(address)
    grid = ui_find.find_office(hwnd, control_types=_GRID_TYPES, skip_into=_GRID_TYPES,
                               timeout=2.0, label="sheet grid") if target else None
    grid_rect = ui_find.rect_of(grid) if grid is not None else None
    if not grid_rect:
        return None
    found = _cell_by_index(grid, target)
    if found is None:
        print(f"[uia] cell {address}: not readable from the grid")
        return None
    name, rect = found
    gl, gt, gr, gb = grid_rect
    r = (max(rect[0], gl), max(rect[1], gt), min(rect[2], gr), min(rect[3], gb))
    if r[2] - r[0] >= 6 and r[3] - r[1] >= 6:
        print(f"[uia] cell {address}: {name!r} on screen at {r}")
        return r
    print(f"[uia] cell {address}: scrolled out of view (rect {rect})")
    return None


def go_to_cell(address):
    """Select a cell the way a person does: click it when it is on screen
    (located through Calc's accessibility tree, no pixel positions). Otherwise type
    the address into the Name Box. The address applies to the active sheet."""
    hwnd = _calc_hwnd()

    if ui_find.available():
        rect = _visible_cell_rect(hwnd, address)
        if rect and ui_find.click_rect(rect):
            human_io.human_pause(0.4, 1.0)
            return

    focus_name_box()
    human_io.human_type(str(address), typo_rate=0)
    human_io.human_pause(0.3, 0.9)
    pyautogui.press("enter")
    human_io.human_pause(0.5, 1.3)
