import psutil
from AppKit import NSWorkspace

def get_running_processes():
    processes = []
    apps = NSWorkspace.sharedWorkspace().runningApplications()
    for app in apps:
        name = app.localizedName()
        exe = app.executableURL().path() if app.executableURL() else None
        if name and exe:
            processes.append({"name": name, "exe": exe})
    return processes