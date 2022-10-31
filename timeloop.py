import time, threading
from datetime import datetime, date, timedelta
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
        self.update_freq = 0  # immediate update on program open

    def run(self):
        while True:
            time.sleep(self.update_freq)
            with SettingsSingleton().settings() as settings:
                self.update_freq = settings[UPDATE_FREQ]
                if not settings[TIMES]:
                    continue

                curr_time = datetime.now()

                if settings[SHOULD_HOLD]:
                    hold_start = datetime.fromisoformat(settings[HOLD_START_TIME])
                    held = (curr_time - hold_start).seconds // 60
                    if held < settings[HOLD_TIME]:
                        continue
                    settings[SHOULD_HOLD] = False
                    SettingsSingleton().update_single_setting_with_lock(SHOULD_HOLD, False)

                self.time_vals = [TimeVal(row[TIME], row[VALUE]) for row in settings[TIMES]]
                prev_time_val = self.time_vals[-1]
                for next_time_val in self.time_vals:
                    if next_time_val.time > curr_time.time():
                        break
                    prev_time_val = next_time_val

                next_time = datetime.combine(date.today(), next_time_val.time)
                prev_time = datetime.combine(date.today(), prev_time_val.time)

                if next_time_val == prev_time_val:
                    next_time_val = self.time_vals[0]
                    next_time = datetime.combine(date.today() + timedelta(days=1), next_time_val.time)

                ratio = 1 if next_time == prev_time else (curr_time - prev_time) / (next_time - prev_time)
                new_brightness = int(next_time_val.value * ratio + prev_time_val.value * (1 - ratio))

                # print(prev_time_val, curr_time.time(), next_time_val, f"{ratio:0.5}", new_brightness)

                set_monitor_brightness(new_brightness)
