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
from resolver import resolveProcess

def main():
    load_dotenv()
    config_dir = user_config_path("playlog", ensure_exists=True)
    config_file = config_dir / "config.json"
    print(config_file)
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

    active_sessions = {}
    attempted_resolutions = set(config.get("attempted_resolutions", []))
    while True:
        print('starting poll cycle')
        running_games = set()
        for proc in get_running_processes():
            if proc["name"] in games_json and proc["name"] not in active_sessions:
                session_id = session_manager.startSession(BACKEND_URL, games_json[proc['name']], config['device_id'], config['token'])
                running_games.add(proc['name'])
                active_sessions[proc['name']] = session_id
            if proc["name"] in games_json and proc["name"] in active_sessions:
                session_manager.heartbeat(BACKEND_URL, active_sessions[proc['name']], config['token'])
                running_games.add(proc['name'])
            if proc["name"] not in games_json and proc["name"] not in attempted_resolutions:
                attempted_resolutions.add(proc["name"])
                game_found = resolveProcess(proc["name"], proc["exe"], IGDB_CLIENT_ID, IGDB_CLIENT_SECRET, ANTHROPIC_API_KEY)
                if game_found is not None:
                    create_game = httpx.post(f'{BACKEND_URL}/games/create', json={"canonical_name": game_found['name']}, headers={"Authorization": f"Bearer {config['token']}"})
                    create_game.raise_for_status()
                    game_id = create_game.json()
                    games_json[proc['name']] = game_id
                    print(f"Created game with id: {game_id}")
                    update_game = httpx.post(f'{BACKEND_URL}/games/{game_id}/update', json={"igdb_id": game_found['igdb_id'], "process_names": [proc['name']]}, headers={"Authorization": f"Bearer {config['token']}"})
                    update_game.raise_for_status()
                    print(f"Update response: {update_game.status_code} {update_game.json()}")
        # after the for loop, before time.sleep
        config["attempted_resolutions"] = list(attempted_resolutions)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f)
        time.sleep(5)
        print("sleep done, checking sessions")
        to_remove = []
        for session in active_sessions:
            if session not in running_games:
                session_manager.endSession(BACKEND_URL, active_sessions[session], config['token'])
                to_remove.append(session)
        for session in to_remove:
            del active_sessions[session]

if __name__ == "__main__":
    main()

    