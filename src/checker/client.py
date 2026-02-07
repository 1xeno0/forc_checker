"""FORC task list checker: fetches URL and returns task lines."""
import time
from typing import List, Optional

import requests

from config import INTERVAL, URL


class CheckerClient:
    """Fetches task list from a URL and tracks changes by content."""

    def __init__(self, url: str = URL, interval: int = INTERVAL, forc_tasks: Optional[List[str]] = None):
        self.url = url
        self.interval = interval
        self.forc_tasks = forc_tasks or []
        self.running = False

    def session(self) -> List[str]:
        """Fetch current task list from URL (one task per line, last empty line stripped)."""
        html = requests.get(self.url, timeout=30).text
        lines = html.strip().split("\n")
        if lines and lines[-1] == "":
            lines = lines[:-1]
        return lines

    def run_loop(self, on_change=None):
        """Run forever; call on_change(new_tasks) only when task list content changes."""
        self.running = True
        while self.running:
            try:
                current = self.session()
                if current != self.forc_tasks:
                    if callable(on_change):
                        on_change(current)
                    self.forc_tasks = current
            except Exception:
                pass  # replace with logger when needed
            time.sleep(self.interval)

    def stop(self):
        self.running = False
