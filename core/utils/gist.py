import os
import json
import requests
from core.logging_module import get_log

_log = get_log(__name__)
_last_gist_content = None


async def create_gist_from_traceback(traceback_text: str) -> str:
    global _last_gist_content

    # Avoid duplicate Gist creation
    if traceback_text == _last_gist_content:
        _log.info("Skipping duplicate Gist creation.")
        return "Duplicate error - Gist already created."

    _last_gist_content = traceback_text

    try:
        GITHUB_API = "https://api.github.com/gists"
        API_TOKEN = os.getenv("GITHUB")
        if not API_TOKEN:
            raise EnvironmentError("Missing GITHUB token in environment.")

        headers = {"Authorization": f"token {API_TOKEN}"}
        payload = {
            "description": "PortalBot Traceback",
            "public": True,
            "files": {"error.txt": {"content": traceback_text}},
        }

        response = requests.post(GITHUB_API, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        gist_id = response.json()["id"]
        gist_url = f"https://gist.github.com/{gist_id}"
        _log.info(f"Gist created: {gist_url}")
        return gist_url

    except Exception as e:
        _log.error(f"Failed to create Gist: {e}")
        return "Unable to create Gist"
