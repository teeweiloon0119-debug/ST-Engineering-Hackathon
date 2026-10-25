# Hardcoded-coordinate inventory

Scope: every place the agent depends on a screen position. Line numbers refer to the files in this folder (the versions you sent, with my `web_tasks.py` / `human_io.py` edits).

## Status (steps 1-4 done, mocked-tested, NOT yet run on the VM)

| Target | Status |
|---|---|
| 1 Name Box | **Done.** All 13 sites call `calc_nav.focus_name_box()` (new file `calc_nav.py`). Uses `Ctrl+Shift+T`, **unverified on your OpenOffice build**. If it fails, set `NAME_BOX_CLICK_XY = (37, 126)` in `calc_nav.py`. |
| 2 Title format | **Done.** `Ctrl+1` (Heading 1) after the title, `Ctrl+0` (Text Body) before the notes. Look changes from "Bold 18 pt" to the Heading 1 style. |
| 3 Click after title | **Done.** Removed (`End` already follows). |
| 5 Address bar | **Done.** Click removed; `Ctrl+L` kept. |
| 6 Close buttons | **Done.** `human_io.close_foreground_window()` (Alt+F4; sends `WM_CLOSE` instead if the expected window isn't in front). Renamed: `close_writer_with_mouse` -> `close_writer_window`, `close_calc_with_mouse` -> `close_calc`. `web_tasks.close_chrome_with_mouse` keeps its name because the orchestrator calls it, but no longer clicks. |
| 4 Desktop icon | **Open**, needs UI Automation (`spreadsheet_part1.py`, `SPREADSHEET_ICON`). |
| 7 Title-bar focus click | **Open**, fallback only (`orchestrator.ensure_foreground`, `financial_report.focus_window`); window-relative, low risk. |

## Summary

- **~30 click sites, but only 7 distinct UI targets** that need real work. Most sites are the same few elements repeated.
- **Nothing is wrong in the research-notes modules**: `research_notes_part1/2.py` are keyboard-only (no coordinates). `financial_report.py` positions windows with `SetWindowPos` + the work-area API, which is already resolution-independent.
- **Inconsistency found:** the Calc Name Box is `(17, 124)` in `spreadsheet_part1.py:19` but `(37, 126)` in parts 2, 3 and 4. They cannot both be right, which is itself evidence the numbers are fragile. Part 1 clicks 21 px further left, near the box's edge.

## The 7 targets

| # | UI element | Where (file:line) | Hardcoded value | Click sites |
|---|---|---|---|---|
| 1 | **Calc Name Box** | `spreadsheet_part1.py:19` (+ clicks at 103, 113, 160); `spreadsheet_part2.py:13` (57, 128); `spreadsheet_part3.py:13` (60); `spreadsheet_part4.py:13` (57, 119) | `(17,124)` in part 1, `(37,126)` in parts 2–4 | **~13** (every `go_to_sheet` / `go_to_cell`) |
| 2 | **Writer title formatting**: title paragraph, Bold button, Font-size box | `office_worker.py:177` (title 4-click), `189` + `237` (Bold), `200` + `248` (font size) | `(259,258)`, `(430,86)`, `(375,95)` | 5 |
| 3 | **Writer: click after title** | `office_worker.py:307` | `(500,140)` | 1 |
| 4 | **Desktop icon** "Profit and Loss Statement" | `spreadsheet_part1.py:16`, used at 67 and 75 | `(40,649)` | 2 (move + double-click) |
| 5 | **Chrome address bar** | `web_tasks.py:323-325` | `x = 30–44 % of width`, `y = 54` | 1 per URL |
| 6 | **Window Close button** (Writer ×2, Calc, Chrome) | `office_worker.py:453-461`, `financial_report.py:532-534`, `spreadsheet_part4.py:220-243`, `web_tasks.py:247-253` | `(right-15, top+15)` / `(screen_w-15, 12)` | 4 |
| 7 | **Title bar** (focus a window) | `orchestrator.py:250-254`, `financial_report.py:267-269` | `left+30..120, top+12` | 2 |

Not a problem: `web_tasks.py:371-373` (hover points inside the page) are *random positions to look at*, not click targets. They don't need replacing, only to land inside the page area.

## Why each one breaks

- **1, 2, 3** assume a specific Calc/Writer toolbar layout (sidebar open or closed, toolbar customised, window maximised, 100 % scaling). Any change moves the control and the click lands on something else, silently.
- **4** assumes the desktop icon sits at one grid position. Adding a file or changing resolution moves it.
- **5** assumes Chrome's toolbar height. A bookmarks bar, a different zoom/scaling or a different Chrome version shifts it. Note it is redundant: the code immediately presses `Ctrl+L`, which already focuses the address bar.
- **6** is relative to the window rect, so it survives resolution changes, but it assumes the caption buttons sit exactly 15 px in from the right. A maximised window's rect also extends a few pixels off-screen on Windows 10/11.
- **7** is window-relative and low risk; it only matters when `SetForegroundWindow` fails.

## Replacement options

There are two levels, and you can mix them. **Level A needs no new library**, so you can do it before the UI-automation package arrives.

### Level A: keyboard / window-API replacements (no new library)

| Target | Replacement | Confidence |
|---|---|---|
| 1 Name Box | One shared helper `focus_name_box()` used by all 13 sites. Try `Ctrl+Shift+T` (Calc's "go to Name Box" shortcut). If your OpenOffice build doesn't support it, `F5` opens the Navigator, which also jumps to a cell/sheet. | **Verify in the VM first.** I believe `Ctrl+Shift+T` works but I haven't confirmed it on your OpenOffice version. |
| 2 Title format | Replace the 5 clicks with a paragraph style: type the title, then `Ctrl+1` (Heading 1), `Enter`, `Ctrl+0` (Body Text). No toolbar involved. `Ctrl+B` for bold is already used in `financial_report.py`. | High. Heading 1 changes the font size/look from "Bold 18 pt", which should be fine for the story. |
| 3 Click after title | `End`, `Enter` (the code already does this right after the click, so the click can simply be removed). | High |
| 5 Address bar | Drop the click, keep `Ctrl+L` (already there). | High |
| 6 Close | `Alt+F4`, or `Ctrl+Q` for OpenOffice. One `close_window(hwnd)` helper for all four. | High |
| 4, 7 | No good keyboard equivalent. See Level B. | n/a |

Cost/benefit: Level A removes **~21 of ~30** click sites with a few small edits. The downside is fewer real mouse movements in the run. The judges' notes mention mouse paths, so I would keep some mouse use through Level B rather than remove all of it.

### Level B: UI Automation (`pywinauto` / `uiautomation`)

The best design keeps the human-looking mouse path and only removes the hardcoded pixels:

```
rect = find_control(window, name="Name Box").rectangle()
human_io.human_click(*random_point_inside(rect))   # same Bezier path, no magic numbers
```

| Target | UIA approach | Expected to work? |
|---|---|---|
| 6, 7 window caption buttons | Find the button named "Close" under the window's title bar. Caption buttons are native Windows, so UIA exposes them for **any** app, OpenOffice included. | Yes |
| 5 Chrome address bar | Edit control named "Address and search bar". Chrome's toolbar is native UI, so it is normally exposed. | Likely |
| 4 Desktop icon | Desktop icons appear as list items under "Program Manager". | Likely |
| 1, 2, 3 inside OpenOffice | **Weak.** OpenOffice draws its own controls and exposes only a thin accessibility tree to UIA, so the Name Box and toolbar buttons may be invisible to it. Treat as "try, fall back to Level A". | Uncertain |
| Clicking page content in Chrome (judges' "use web data") | Needs Chrome's web-content accessibility tree, which is **off by default**. | Needs setup, see below |

**Chrome accessibility, important constraint:** do not enable it with the `--force-renderer-accessibility` command-line flag. Judges read the `CommandLine` field in Sysmon Event ID 1, so an unusual flag there is a red flag. Instead turn on "Native accessibility API support" once in `chrome://accessibility` during VM setup (it persists in the profile), so Chrome starts with a normal command line.

## Suggested order

1. **Name Box helper** (target 1): ~13 sites collapse into one function, the biggest single win, and it also fixes the 17 vs 37 inconsistency.
2. **Writer title** (targets 2, 3): remove 6 pixel clicks via `Ctrl+1` / `Ctrl+0`.
3. **`close_window(hwnd)` helper** (target 6): one function replaces four copies.
4. **Address bar** (target 5): delete the redundant click.
5. **Desktop icon** (target 4) and **"click into web data"**: these need the UI-automation library.

Steps 1–4 do not depend on the library and can be done now.
