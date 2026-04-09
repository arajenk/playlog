import httpx
import anthropic
import time

_igdb_token: str | None = None
_igdb_token_expires_at: float = 0.0

def accessIGDB(client_id, client_secret):
    global _igdb_token, _igdb_token_expires_at
    if _igdb_token and time.time() < _igdb_token_expires_at - 60:
        return _igdb_token
    token_request = httpx.post('https://id.twitch.tv/oauth2/token', params={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"})
    token_request.raise_for_status()
    data = token_request.json()
    _igdb_token = data["access_token"]
    _igdb_token_expires_at = time.time() + data["expires_in"]
    return _igdb_token

def searchIGDB(game_name, client_id, access_token):
    response = httpx.post(
        'https://api.igdb.com/v4/games',
        headers={
            'Client-ID': client_id,
            'Authorization': f'Bearer {access_token}'
        },
        content=f'search "{game_name}"; fields name; limit 5;'
    )
    return response.json()

def aiLookup(anthropic_api_key, igdb_results, process, exe_path):
    client = anthropic.Anthropic(api_key=anthropic_api_key)

    message = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=100,
        messages=[{"role": "user", "content": f'Given the process name {process}, and the path {exe_path}, which of these IGDB games is the most likely match? Return ONLY a number or ONLY the word null. No other text, no explanation. Games: {igdb_results}'}]
)
    return message.content[0].text

def resolveProcess(process_name, exe_path, client_id, client_secret, anthropic_api_key):
    token = accessIGDB(client_id, client_secret)
    igdb_result = searchIGDB(process_name, client_id, token)
    if igdb_result:
        anthropic_result = aiLookup(anthropic_api_key, igdb_result, process_name, exe_path)
    else:
        return None
    cleaned = anthropic_result.strip()
    if cleaned == "null":
        return None
    if not cleaned.lstrip("-").isdigit():
        print(f"Unexpected AI response: {cleaned!r}")
        return None
    target_id = int(cleaned)
    for game in igdb_result:
        if game["id"] == target_id:
            return {"igdb_id": game["id"], "name": game["name"]}
    return None
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    client_id = os.getenv("IGDB_CLIENT_ID")
    client_secret = os.getenv("IGDB_CLIENT_SECRET")
    anthropic_api_key= os.getenv("ANTHROPIC_API_KEY")
    token = accessIGDB(client_id, client_secret)
    result = searchIGDB("Elden Ring", client_id, token)
    claude_result = resolveProcess("Elden Ring", "/Applications/EldenRing.app/Contents/MacOS/EldenRing", client_id, client_secret, anthropic_api_key)
    print(claude_result)