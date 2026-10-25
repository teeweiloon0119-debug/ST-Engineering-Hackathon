"""Diagnostic v5: can the AGENT's own lookups reach OpenOffice's controls?

No clicking. Uses the exact code path the agent uses (ui_find.find_office and
calc_nav's cell hit-test), and also dumps what UI Automation sees in each
window's toolbars (the document / cell grid is skipped), so a miss shows the
real names and control types to match on.

Have BOTH open: Writer (any document) and Calc (Profit and Loss Statement.ods).
Run it the way the agent runs:
    "C:\\...\\pythonw.exe" diag_uia.py
Then read the result:
    type uia_diag.txt

Web page check (Chrome open on e.g. an AP News story; no clicks):
    py diag_uia.py web

If OpenOffice shows only its title bar / caption buttons, run once with
    "C:\\...\\pythonw.exe" diag_uia.py --enable
then close ALL OpenOffice windows (incl. the Quickstarter tray icon), reopen
Writer + Calc and run diag_uia.py again.
"""
import builtins
import os
import sys
import traceback

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uia_diag.txt")
_out = open(LOG, "w", encoding="utf-8")


def w(*parts):
    _out.write(" ".join(str(p) for p in parts) + "\n")
    _out.flush()


builtins.print = w     # ui_find / calc_nav trace lines ("[uia] ...") land in the file too
w(f"exe: {sys.executable}")


def dump(ctl, depth, budget, skip):
    """Toolbar-level tree: type | name | rect, not descending into `skip` types."""
    if budget[0] <= 0 or depth > 12:
        return
    budget[0] -= 1
    try:
        ctype = ctl.ControlTypeName
        w("  " * depth + f"{ctype} | {ctl.Name!r} | {ui_find.rect_of(ctl)}")
        if depth > 0 and ctype in skip:
            w("  " * (depth + 1) + "(contents skipped)")
            return
        child = ctl.GetFirstChildControl()
        n = 0
        while child is not None and n < 200:
            dump(child, depth + 1, budget, skip)
            child = child.GetNextSiblingControl()
            n += 1
    except Exception as error:
        w("  " * depth + f"<unreadable: {error!r}>")


def describe(ctl):
    if ctl is None:
        return "None"
    try:
        return f"{ctl.ControlTypeName} | {ctl.Name!r} | {ui_find.rect_of(ctl)}"
    except Exception as error:
        return f"<unreadable: {error!r}>"


def probe_cells(hwnd):
    """What Calc's grid answers: hit-tests, its first children, Grid pattern."""
    grid = ui_find.find_office(hwnd, control_types=calc_nav._GRID_TYPES,
                               skip_into=calc_nav._GRID_TYPES, timeout=2.0, label="sheet grid")
    if grid is None:
        return
    gl, gt, gr, gb = ui_find.rect_of(grid)
    w("\n--- cell probe ---")
    for x, y in ((gl + 4, gt + 4), (gl + 40, gt + 30), ((gl + gr) // 2, (gt + gb) // 2)):
        ctl = ui_find.control_at(x, y)
        w(f"hit-test ({x},{y}): {describe(ctl)}")
        try:
            for extra in ("AutomationId", "ClassName", "LocalizedControlType"):
                w(f"    {extra}: {getattr(ctl, extra, None)!r}")
            value = ctl.GetLegacyIAccessiblePattern()
            w(f"    legacy name={value.Name!r} value={value.Value!r} role={value.Role!r} "
              f"childId={value.ChildId!r}")
            parent = ctl.GetParentControl()
            for _ in range(3):
                w(f"    parent: {describe(parent)}")
                parent = parent.GetParentControl() if parent is not None else None
        except Exception as error:
            w(f"    (details failed: {error!r})")
    w("grid children (first 6):")
    try:
        child, n = grid.GetFirstChildControl(), 0
        while child is not None and n < 6:
            w(f"    {describe(child)}")
            child, n = child.GetNextSiblingControl(), n + 1
        if n == 0:
            w("    (none)")
    except Exception as error:
        w(f"    (failed: {error!r})")
    try:
        pattern = grid.GetGridPattern()
        w(f"grid pattern: rows={pattern.RowCount} cols={pattern.ColumnCount}")
        for r, c in ((0, 0), (3, 4), (18, 5)):
            w(f"    GetItem({r},{c}): {describe(pattern.GetItem(r, c))}")
    except Exception as error:
        w(f"grid pattern: unavailable ({error!r})")
    try:
        legacy = grid.GetLegacyIAccessiblePattern()
        w(f"grid legacy: role={legacy.Role!r} name={legacy.Name!r}")
    except Exception as error:
        w(f"grid legacy: failed ({error!r})")


try:
    import ui_find
    import calc_nav
    w(f"ui_find imported; uiautomation available: {ui_find.available()}")
    if "--enable" in sys.argv:
        ui_find.set_screen_reader_flag(True)   # stays on until logoff
        w("screen-reader flag switched ON. Now CLOSE every OpenOffice window (and the "
          "Quickstarter tray icon), reopen Writer + Calc, and run diag_uia.py again.")
    w(f"screen-reader flag: {'ON' if ui_find.screen_reader_flag() else 'OFF'}"
      " (OpenOffice must be STARTED while it is ON to expose its controls)")
except Exception:
    ui_find = None
    w("import FAILED:\n" + traceback.format_exc())

def probe_web():
    """What the agent sees on the Chrome page that is open now (no clicks)."""
    import web_tasks
    w("\n" + "=" * 60 + "\nChrome page\n" + "=" * 60)
    hwnd = web_tasks.get_chrome_hwnd()
    w(f"chrome hwnd={hwnd} title={web_tasks.get_window_title(hwnd)!r}")
    if not hwnd:
        w("Chrome is not open - open the page (e.g. an AP News story) and retry.")
        return
    ui_find.ensure_foreground(hwnd)
    import time as _t
    t0 = _t.time()
    asked = web_tasks.enable_web_accessibility(hwnd)
    w(f"asked {asked} Chrome page window(s) to turn accessibility on")
    doc = web_tasks.page_document()
    w(f"page document: {describe(doc)}  content={doc is not None and web_tasks._has_web_content(doc)}"
      f" after {_t.time() - t0:.1f}s")
    if doc is None:
        return
    w("\n--- visible controls of ANY type (first 80) ---")
    every = ["TextControl", "GroupControl", "CustomControl", "PaneControl", "HyperlinkControl",
             "ListItemControl", "DataItemControl", "HeaderControl", "ImageControl", "ButtonControl",
             "ListControl", "TableControl", "EditControl", "DocumentControl"]
    for c in ui_find.visible_controls(doc, every, limit=80, max_nodes=4000, timeout=8.0):
        leaf = "leaf" if web_tasks._is_leaf(c) else "    "
        w(f"  {leaf} {c.ControlTypeName:16} {ui_find.text_of(c)[:70]!r} {ui_find.rect_of(c)}")
    blocks = web_tasks.text_blocks()
    w(f"\nreading blocks (read_with_mouse uses these): {len(blocks)}")
    paras = [b for b in web_tasks.text_blocks(min_width=250, min_height=30, max_height=320)
             if b[0].ControlTypeName != "HyperlinkControl"]
    w(f"paragraph candidates (highlight + copy uses these): {len(paras)}")
    for c, r in paras[:10]:
        w(f"    {c.ControlTypeName:16} {r} link-at-start={web_tasks._is_link_at(r[0] + 2, r[1] + 8)}"
          f" name={ui_find.text_of(c)[:50]!r}")
    w(f"headline links (>= 25 chars): {len(web_tasks.visible_links(min_len=25))}")
    priced, pool, view = web_tasks.page_data_links()
    w(f"\nApple/Amazon click candidates (click_into_page_data picks from these): "
      f"{len(pool)} in content, {len(priced)} price-like, page area={view}")
    for c in (priced or pool)[:15]:
        w(f"    {c.ControlTypeName:16} {ui_find.text_of(c)[:60]!r} {ui_find.rect_of(c)}")


if ui_find is not None and ui_find.available() and "web" in sys.argv:
    try:
        probe_web()
    except Exception:
        w("web probe FAILED:\n" + traceback.format_exc())
elif ui_find is not None and ui_find.available():
    for title, checks in [
        ("OpenOffice Writer", [(["Bold"], ["ButtonControl", "CheckBoxControl"]),
                               (["Font Size"], ["ComboBoxControl", "EditControl"])]),
        ("OpenOffice Calc", [(["Name Box"], ["ComboBoxControl", "EditControl"]),
                             (["Summary"], ["TabItemControl"]),
                             (["Salary"], ["TabItemControl"])]),
    ]:
        w("\n" + "=" * 60 + f"\n{title}\n" + "=" * 60)
        try:
            hwnd = ui_find.window_by_title(title)
            w(f"window_by_title -> hwnd={hwnd} {ui_find._title(hwnd)!r}")
            if not hwnd:
                w("window not found - open it and retry.")
                continue
            w(f"ensure_foreground: {ui_find.ensure_foreground(hwnd)}")
            for names, types in checks:
                skip = calc_nav._GRID_TYPES if "TabItemControl" in types else ui_find.OFFICE_SKIP_INTO
                c = ui_find.find_office(hwnd, names=names, control_types=types, skip_into=skip)
                if c is not None and "ComboBoxControl" in types:
                    w(f"    text field to click: {ui_find.text_field_rect(c)}")
            if "Writer" in title:
                doc = ui_find.find_office(hwnd, control_types=["DocumentControl"], timeout=2.0,
                                          label="Writer document")
                if doc is not None:
                    ui_find.text_block_rect(doc, "")       # topmost paragraph = title
                    w("--- document children (first 15) ---")
                    dump(doc, 0, [15], ())
            if "Calc" in title:
                for addr in ("A1", "E4", "F19"):
                    calc_nav._visible_cell_rect(hwnd, addr)
                probe_cells(hwnd)
            w("\n--- tree (document / grid contents skipped) ---")
            dump(ui_find._window_control(hwnd), 0, [1500], ui_find.OFFICE_SKIP_INTO)
        except Exception:
            w("FAILED:\n" + traceback.format_exc())

w("\ndone.")
_out.close()
