from platformdirs import user_config_path
import httpx
import os
import json
from getpass import getpass
from dotenv import load_dotenv
from platform import system, node
from poller import get_running_processes
import time
import session as session_manager

def main():
    load_dotenv()
    config_dir = user_config_path("playlog", ensure_exists=True)
    config_file = config_dir / "config.json"
    print(config_file)
    BACKEND_URL = os.getenv("BACKEND_URL")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)   
    except FileNotFoundError:
        config = {}

    if "token" not in config:
        email = input("Enter your email: ")
        password = getpass(prompt="Enter your password: ")
        login = httpx.post(f'{BACKEND_URL}/login', json={"email": email, "password" : password})
        login_json = login.json()
        with open(config_file, 'w', encoding='utf-8') as f:
            config["token"] = login_json
            json.dump(config, f)
    if "device_id" not in config:
        device_name = node()
        os_map = {"Darwin": "macOS"}
        device_os = os_map.get(system(), system())
        device_register = httpx.post(f'{BACKEND_URL}/devices/register', json={"name": device_name, "os" : device_os}, headers={"Authorization": f"Bearer {config['token']}"})
        device_json = device_register.json()
        with open (config_file, 'w', encoding='utf-8') as f:
            config["device_id"] = device_json
            json.dump(config, f)
    get_all_games = httpx.get(f'{BACKEND_URL}/games/getallgames', headers={"Authorization": f"Bearer {config['token']}"})
    games_json = get_all_games.json()

    active_sessions = {}
    while True:
        running_games = set()
        for proc in get_running_processes():
            if proc["name"] in games_json and proc["name"] not in active_sessions:
                session_id = session_manager.startSession(BACKEND_URL, games_json[proc['name']], config['device_id'], config['token'])
                running_games.add(proc['name'])
                active_sessions[proc['name']] = session_id
            if proc["name"] in games_json and proc["name"] in active_sessions:
                session_manager.heartbeat(BACKEND_URL, active_sessions[proc['name']], config['token'])
                running_games.add(proc['name'])
        time.sleep(30)
        to_remove = []
        for session in active_sessions:
            if session not in running_games:
                session_manager.endSession(BACKEND_URL, active_sessions[session], config['token'])
                to_remove.append(session)
        for session in to_remove:
            del active_sessions[session]
            

if __name__ == "__main__":
    main()

    