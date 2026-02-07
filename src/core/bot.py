from src.data.config import URL, INTERVAL
import time
import requests


class Bot:
    def __init__(self, url: str = URL, interval: int = INTERVAL, forc_tasks: list = []):
        self.url = url
        self.interval = interval
        self.running = False
        self.forc_tasks = forc_tasks

    def start_bot(self):
        self.running = True
        self.run_loop()

    def run_loop(self):
        while True:
            try:
                forc_tasks_changed = self.session()
                if len(forc_tasks_changed) != len(self.forc_tasks):
                    self.tg_bot_msg(forc_tasks_changed)
                self.forc_tasks = forc_tasks_changed
            except Exception:
                print("Error")  # можно заменить на error_log

            time.sleep(self.interval)

    def session(self) -> list:
        html = requests.get(self.url).text
        forc_tasks = html.split('\n')
        del forc_tasks[-1]
        return forc_tasks

    def tg_bot_msg(self, forc_tasks: list):
        pass

    def stop_bot(self):
        self.running = False
        exit(0)
