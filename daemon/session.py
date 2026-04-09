import httpx

def startSession(backend_url, game_id, device_id, token):
    start_session = httpx.post(f'{backend_url}/sessions/start', json={"game_id": game_id, "device_id": device_id}, headers={"Authorization":f"Bearer {token}"})
    start_session.raise_for_status()
    return start_session.json()
def heartbeat(backend_url, session_id, token):
    heartbeat_call = httpx.post(f'{backend_url}/sessions/{session_id}/heartbeat', headers={"Authorization": f"Bearer {token}"})
    heartbeat_call.raise_for_status()
def endSession(backend_url, session_id, token):
    end_session = httpx.post(f'{backend_url}/sessions/{session_id}/end', headers={"Authorization": f"Bearer {token}"})
    end_session.raise_for_status()