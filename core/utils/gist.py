import os
import json
import requests
from core.logging_module import get_log

_log = get_log(__name__)
_last_gist_state = {"last_content": None}


async def create_gist_from_traceback(traceback_text: str) -> str:
    # Avoid duplicate Gist creation
    if traceback_text == _last_gist_state["last_content"]:
        _log.info("⚠️ Skipping duplicate Gist creation.")
        return "Duplicate error - Gist already created."

    _last_gist_state["last_content"] = traceback_text

    try:
        API_TOKEN = os.getenv("github_gist")
        if not API_TOKEN:
            _log.error("❌ Missing GitHub Gist API token in environment.")
            return "GitHub token not found."

        GITHUB_API = "https://api.github.com/gists"
        headers = {
            "Authorization": f"token {API_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "description": "PortalBot Traceback",
            "public": True,
            "files": {"error.txt": {"content": traceback_text}},
        }

        response = requests.post(GITHUB_API, headers=headers, json=payload)
        response.raise_for_status()

        gist_data = response.json()
        gist_url = (
            gist_data.get("html_url")
            or f"https://gist.github.com/{gist_data.get('id')}"
        )
        _log.info(f"✅ Gist created: {gist_url}")
        return gist_url

    except requests.HTTPError as http_err:
        _log.error(
            f"HTTP error while creating Gist: {http_err.response.text}", exc_info=True
        )
        return "Unable to create Gist due to API error."

    except Exception as e:
        _log.error(f"Unexpected error while creating Gist: {e}", exc_info=True)
        return "Unable to create Gist."
