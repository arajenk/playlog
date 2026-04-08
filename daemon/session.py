import httpx

def startSession(backend_url, game_id, device_id, token):
    start_session = httpx.post(f'{backend_url}/sessions/start', json={"game_id": game_id, "device_id": device_id}, headers={"Authorization":f"Bearer {token}"})
    return start_session.json()
def heartbeat(backend_url, session_id, token):
    heartbeat_call = httpx.post(f'{backend_url}/sessions/{session_id}/heartbeat', headers={"Authorization": f"Bearer {token}"})
def endSession(backend_url, session_id, token):
    end_session = httpx.post(f'{backend_url}/sessions/{session_id}/end', headers={"Authorization": f"Bearer {token}"})