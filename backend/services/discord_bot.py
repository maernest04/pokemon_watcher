import os
from typing import Any

import requests


def send_embed(channel_id: str, *, title: str, description: str, fields: list[dict[str, Any]] | None = None) -> None:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not configured")
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    payload: dict[str, Any] = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "fields": fields or [],
            }
        ]
    }
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Discord send failed: {response.status_code} {response.text}")
