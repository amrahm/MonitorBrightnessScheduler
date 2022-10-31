import time, threading
from datetime import datetime, date
import monitorcontrol
from infrastructure import *


class TimeVal:
    def __init__(self, time: str, value: int):
        self.time = datetime.strptime(time, "%H:%M").time()
        self.value = value

    def __repr__(self) -> str:
        return f"{self.time} --> {self.value}"


class TimeLoop(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.settingsUpdatedEvent = threading.Event()
        self.settings = load_settings()
        self.time_vals = [TimeVal(row["TIME"], row["VALUE"]) for row in self.settings["TIMES"]]

    def handle_settings_updated_event(self):
        if self.settingsUpdatedEvent.is_set():
            self.settings = load_settings()
            self.time_vals = [TimeVal(row["TIME"], row["VALUE"]) for row in self.settings["TIMES"]]
            self.settingsUpdatedEvent.clear()

    def run(self):
        while True:
            self.handle_settings_updated_event()
            while not self.time_vals:
                self.settingsUpdatedEvent.wait()
                self.handle_settings_updated_event()
            curr_time = datetime.now()
            prev_time_val = self.time_vals[-1]
            for next_time_val in self.time_vals:
                if next_time_val.time > curr_time.time():
                    break
                prev_time_val = next_time_val

            next_time = datetime.combine(date.today(), next_time_val.time)
            prev_time = datetime.combine(date.today(), prev_time_val.time)
            ratio = (curr_time - prev_time) / (next_time - prev_time)
            new_brightness = int(next_time_val.value * ratio + prev_time_val.value * (1 - ratio))

            for monitor in monitorcontrol.get_monitors():
                with monitor:
                    monitor.set_luminance(new_brightness)

            time.sleep(self.settings["UPDATE_FREQ"])
