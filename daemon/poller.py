import psutil
def get_running_processes():
    processes = []
    for proc in psutil.process_iter(['name']):
        try:
            exe = proc.exe()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
        processes.append({"name" : proc.info['name'], "exe":exe})
    return processes
