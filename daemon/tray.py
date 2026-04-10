import subprocess
import threading
from AppKit import (
    NSApplication,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSMenu,
    NSMenuItem,
    NSImage,
    NSBezierPath,
    NSColor,
    NSMakeSize,
    NSMakePoint,
)
from Foundation import NSObject


def _make_icon() -> NSImage:
    """Draw a triangular play-button icon using Bezier paths (no image file needed)."""
    img = NSImage.alloc().initWithSize_(NSMakeSize(18, 18))
    img.lockFocus()
    path = NSBezierPath.bezierPath()
    path.moveToPoint_(NSMakePoint(3, 2))
    path.lineToPoint_(NSMakePoint(3, 16))
    path.lineToPoint_(NSMakePoint(15, 9))
    path.closePath()
    NSColor.blackColor().setFill()
    path.fill()
    img.unlockFocus()
    img.setTemplate_(True)  # adapts automatically to dark / light menu bar
    return img


class _MenuDelegate(NSObject):
    def openDashboard_(self, sender):
        subprocess.Popen(["open", self._dashboard_url])

    def openConfig_(self, sender):
        subprocess.Popen(["open", str(self._config_path)])

    def quit_(self, sender):
        self._stop_event.set()
        NSApplication.sharedApplication().terminate_(None)


def run_tray(config_path, dashboard_url, stop_event: threading.Event) -> None:
    """Build the status bar item and run the AppKit event loop. Blocks until quit."""
    app = NSApplication.sharedApplication()
    # Accessory policy: no Dock icon, no menu bar takeover
    app.setActivationPolicy_(1)

    delegate = _MenuDelegate.alloc().init()
    delegate._config_path = config_path
    delegate._dashboard_url = dashboard_url
    delegate._stop_event = stop_event

    status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
        NSVariableStatusItemLength
    )
    status_item.button().setImage_(_make_icon())

    menu = NSMenu.alloc().init()
    for title, sel in [
        ("Open Dashboard", "openDashboard:"),
        ("Open Config", "openConfig:"),
    ]:
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, sel, "")
        item.setTarget_(delegate)
        menu.addItem_(item)

    menu.addItem_(NSMenuItem.separatorItem())

    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Quit", "quit:", ""
    )
    quit_item.setTarget_(delegate)
    menu.addItem_(quit_item)

    status_item.setMenu_(menu)
    app.run()
