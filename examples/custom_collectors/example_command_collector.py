#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

from community_memory.custom_collectors import write_collector_window
from community_memory.utils import from_iso, to_iso, utc_now


def main() -> None:
    base_path = Path(os.environ["PRISM_BASE_PATH"])
    collector_key = os.environ["PRISM_COLLECTOR_KEY"]
    options = json.loads(os.environ.get("PRISM_COLLECTOR_OPTIONS", "{}") or "{}")

    bucket = os.environ.get("EXAMPLE_COLLECTOR_BUCKET", options.get("bucket", "custom"))
    channel_name = options.get("channel_name", "example-feed")
    now = (
        from_iso(os.environ["PRISM_NOW"])
        if os.environ.get("PRISM_NOW")
        else utc_now()
    )
    since = now - timedelta(hours=1)
    until = now

    messages = [
        {
            "id": "example-1",
            "author": {
                "id": "example-source",
                "username": "example-source",
                "display_name": "Example Source",
            },
            "content": "This is a sample custom collector message.",
            "created_at": to_iso(since + timedelta(minutes=15)),
            "jump_url": "https://example.com/custom-collector",
            "attachments": [],
            "embeds": [],
        }
    ]

    outputs = write_collector_window(
        base_path=base_path,
        collector_key=collector_key,
        bucket=bucket,
        since_iso=to_iso(since),
        until_iso=to_iso(until),
        messages=messages,
        channel_name=channel_name,
        channel_id=channel_name,
        channel_topic="Example custom collector output",
        force=os.environ.get("PRISM_FORCE") == "1",
    )

    result = {
        "status": "ok",
        "outputs": [outputs["md"]] if outputs else [],
        "windows_processed": 1,
        "collector_state": {
            "last_until": to_iso(until),
            "window_minutes": 60,
        },
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
