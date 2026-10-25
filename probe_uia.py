"""
probe_uia - DIAGNOSTIC ONLY, not part of the agent. Do not run during a demo.

Lists every control that Windows UI Automation can see in OpenOffice Writer,
OpenOffice Calc, Chrome and the desktop, with its type, name and rectangle.
The result decides, control by control, whether the agent can find it with UI
automation or needs a fallback.

Uses the `uiautomation` package (comtypes only), NOT pywinauto, because
pywinauto needs pywin32's win32ui DLL, which does not load on the VM.

Before running: open Writer (any document), Calc (Profit and Loss Statement.ods)
and Chrome (e.g. coingecko.com), all visible. Then:
    py probe_uia.py                 (all apps - slow, mostly Chrome)
    py probe_uia.py writer calc     (only the apps named: writer calc chrome desktop)
Output: uia_probe.txt (or uia_probe_<apps>.txt) next to this script. Wait for
"Done." before opening it - the file is incomplete while the probe is running.
"""

import os
import sys
import time

import uiautomation as auto

# (command-line key, label, fragment of the window title)
TARGETS = [
    ("writer", "Writer", "OpenOffice Writer"),
    ("calc", "Calc", "OpenOffice Calc"),
    ("chrome", "Chrome", "Google Chrome"),
    ("desktop", "Desktop icons", "Program Manager"),
]

MAX_DEPTH = 14      # how deep to walk each window's control tree
MAX_NODES = 2500    # per window; Chrome pages can be huge

HERE = os.path.dirname(os.path.abspath(__file__))


def describe(control):
    r = control.BoundingRectangle
    return (f"{control.ControlTypeName} | name={control.Name!r} | id={control.AutomationId!r}"
            f" | class={control.ClassName!r} | rect=({r.left},{r.top},{r.right},{r.bottom})")


def dump(control, depth, out, count):
    if depth > MAX_DEPTH or count[0] >= MAX_NODES:
        return
    try:
        out.write("  " * depth + describe(control) + "\n")
    except Exception as error:
        out.write("  " * depth + f"<unreadable: {error!r}>\n")
        return
    count[0] += 1
    if count[0] % 100 == 0:
        print(f"    ... {count[0]} controls", flush=True)
    try:
        children = control.GetChildren()
    except Exception:
        return
    for child in children:
        dump(child, depth + 1, out, count)


def main():
    wanted = [a.lower() for a in sys.argv[1:]]
    targets = [t for t in TARGETS if not wanted or t[0] in wanted]
    if wanted and not targets:
        sys.exit("Unknown app. Use any of: " + " ".join(t[0] for t in TARGETS))
    out_path = os.path.join(HERE, "uia_probe.txt" if not wanted
                            else f"uia_probe_{'_'.join(t[0] for t in targets)}.txt")

    windows = auto.GetRootControl().GetChildren()
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(f"UIA probe {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write("Top-level windows seen:\n")
        for w in windows:
            out.write("  " + describe(w) + "\n")

        for _, label, fragment in targets:
            matches = [w for w in windows if fragment.lower() in (w.Name or "").lower()]
            print(f"{label}: {len(matches)} window(s)", flush=True)
            out.write(f"\n{'=' * 70}\n{label}: {len(matches)} window(s) matching {fragment!r}\n{'=' * 70}\n")
            t0 = time.time()
            for w in matches[:1]:
                count = [0]
                dump(w, 0, out, count)
                if count[0] >= MAX_NODES:
                    out.write(f"... stopped at {MAX_NODES} controls\n")
                print(f"  {label}: {count[0]} controls in {time.time() - t0:.0f}s", flush=True)
            out.flush()   # a finished section is safe on disk even if a later one is slow
    print(f"Done. Wrote {out_path}")


if __name__ == "__main__":
    main()
