from platformdirs import user_config_path
import httpx
import os
import json
from getpass import getpass
from dotenv import load_dotenv
from platform import system, node
from poller import get_running_processes
import threading
import session as session_manager
from resolver import resolveProcess
from tray import run_tray


def _poll_loop(BACKEND_URL, IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, ANTHROPIC_API_KEY,
               config, config_file, games_json, stop_event: threading.Event):
    active_sessions = {}
    attempted_resolutions = set(config.get("attempted_resolutions", []))
    while not stop_event.is_set():
        running_games = set()
        for proc in get_running_processes():
            if proc["name"] in games_json and proc["name"] not in active_sessions:
                try:
                    session_id = session_manager.startSession(BACKEND_URL, games_json[proc['name']], config['device_id'], config['token'])
                    running_games.add(proc['name'])
                    active_sessions[proc['name']] = session_id
                except Exception as e:
                    print(f"Failed to start session for {proc['name']}: {e}")
            if proc["name"] in games_json and proc["name"] in active_sessions:
                try:
                    session_manager.heartbeat(BACKEND_URL, active_sessions[proc['name']], config['token'])
                except Exception as e:
                    print(f"Heartbeat failed for {proc['name']}: {e}")
                running_games.add(proc['name'])
            if proc["name"] not in games_json and proc["name"] not in attempted_resolutions:
                attempted_resolutions.add(proc["name"])
                try:
                    game_found = resolveProcess(proc["name"], proc["exe"], IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, ANTHROPIC_API_KEY)
                    if game_found is not None:
                        create_game = httpx.post(f'{BACKEND_URL}/games/create', json={"canonical_name": game_found['name']}, headers={"Authorization": f"Bearer {config['token']}"})
                        create_game.raise_for_status()
                        game_id = create_game.json()
                        games_json[proc['name']] = game_id
                        update_game = httpx.post(f'{BACKEND_URL}/games/{game_id}/update', json={"igdb_id": game_found['igdb_id'], "process_names": [proc['name']]}, headers={"Authorization": f"Bearer {config['token']}"})
                        update_game.raise_for_status()
                except Exception as e:
                    print(f"Resolution failed for {proc['name']}: {e}")
                    attempted_resolutions.discard(proc["name"])
        config["attempted_resolutions"] = list(attempted_resolutions)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f)
        stop_event.wait(30)  # interruptible sleep — exits promptly on Quit
        to_remove = []
        for session in active_sessions:
            if session not in running_games:
                try:
                    session_manager.endSession(BACKEND_URL, active_sessions[session], config['token'])
                except Exception as e:
                    print(f"Failed to end session for {session}: {e}")
                to_remove.append(session)
        for session in to_remove:
            del active_sessions[session]


def main():
    load_dotenv()
    config_dir = user_config_path("playlog", ensure_exists=True)
    config_file = config_dir / "config.json"
    BACKEND_URL = os.getenv("BACKEND_URL")
    IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
    IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)   
    except FileNotFoundError:
        config = {}

    if "token" not in config:
        email = input("Enter your email: ")
        password = getpass(prompt="Enter your password: ")
        login = httpx.post(f'{BACKEND_URL}/login', json={"email": email, "password" : password})
        login.raise_for_status()
        login_json = login.json()
        with open(config_file, 'w', encoding='utf-8') as f:
            config["token"] = login_json
            json.dump(config, f)
    if "device_id" not in config:
        device_name = node()
        os_map = {"Darwin": "macOS"}
        device_os = os_map.get(system(), system())
        device_register = httpx.post(f'{BACKEND_URL}/devices/register', json={"name": device_name, "os" : device_os}, headers={"Authorization": f"Bearer {config['token']}"})
        device_register.raise_for_status()
        device_json = device_register.json()
        with open (config_file, 'w', encoding='utf-8') as f:
            config["device_id"] = device_json
            json.dump(config, f)
    get_all_games = httpx.get(f'{BACKEND_URL}/games/getallgames', headers={"Authorization": f"Bearer {config['token']}"})
    get_all_games.raise_for_status()
    games_json = get_all_games.json()

    stop_event = threading.Event()
    poll_thread = threading.Thread(
        target=_poll_loop,
        args=(BACKEND_URL, IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, ANTHROPIC_API_KEY,
              config, config_file, games_json, stop_event),
        daemon=True,
    )
    poll_thread.start()
    run_tray(config_file, BACKEND_URL, stop_event)

if __name__ == "__main__":
    main()

    