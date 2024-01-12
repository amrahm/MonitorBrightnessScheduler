import time, threading

from src.infrastructure import (
    TIMES,
    UPDATE_FREQ,
    SettingsSingleton,
    update_brightness_based_on_time,
)


class TimeLoop(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.update_freq = 0  # immediate update on program open

    def run(self):
        while True:
            time.sleep(self.update_freq)
            with SettingsSingleton().settings() as settings:
                self.update_freq = settings[UPDATE_FREQ]
                if not settings[TIMES]:
                    continue

            update_brightness_based_on_time()
