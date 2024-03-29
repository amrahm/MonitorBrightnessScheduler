import sys
from datetime import datetime, date, timedelta
import time, threading
import json
import win32api
import PySimpleGUI as sg
from os.path import exists
from typing import Dict, List
import monitorcontrol
from datetime import datetime
import contextlib

Settings = Dict[str, List | int]
SETTINGS_PATH = "settings.json"
WORKING_DIR = sys._MEIPASS if getattr(sys, "frozen", False) else "src"

EXIT_PROGRAM = "Exit Program"
OPEN_SETTINGS = "Open Settings"
TIMES = "TIMES"
TIME = "TIME"
VALUE = "VALUE"
UPDATE_FREQ = "UPDATE_FREQ"
SHOULD_HOLD = "SHOULD_HOLD"
HOLD_TIME = "HOLD_TIME"
HOLD_START_TIME = "HOLD_START_TIME"


class SettingsSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                # could have been created while waiting for lock, so double check
                if not cls._instance:
                    cls._instance = super(SettingsSingleton, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r") as jsonfile:
                self._settings: Settings = json.load(jsonfile)
        else:
            self._settings: Settings = {
                TIMES: [],
                UPDATE_FREQ: 10,
                SHOULD_HOLD: False,
                HOLD_TIME: 60,
            }
            with open(SETTINGS_PATH, "w") as jsonfile:
                json.dump(self._settings, jsonfile, indent=4)

    @contextlib.contextmanager
    def settings(self):
        with SettingsSingleton._lock:
            yield self._settings

    def save_settings(self, new_settings: Settings):
        seen = set()
        to_del = []
        for i, time in enumerate(new_settings[TIMES]):
            time = time[TIME]
            hrs, mins = time.split(":") if time else ("", "")
            if not hrs and not mins:
                to_del.append(i)
                continue
            elif not hrs:
                new_settings[TIMES][i][TIME] = time = f"00:{mins}"
            elif not mins:
                new_settings[TIMES][i][TIME] = time = f"{hrs}:00"

            if time in seen:
                to_del.append(i)
            seen.add(time)

        for i in sorted(to_del, reverse=True):
            del new_settings[TIMES][i]

        _sort_times(new_settings)

        with SettingsSingleton._lock:
            self._settings.update(new_settings)
            with open(SETTINGS_PATH, "w") as jsonfile:
                json.dump(self._settings, jsonfile, indent=4)

    def update_single_setting_with_lock(self, setting, value):
        self._settings[setting] = value
        with open(SETTINGS_PATH, "w") as jsonfile:
            json.dump(self._settings, jsonfile, indent=4)

    def update_single_setting(self, setting, value):
        with SettingsSingleton._lock:
            self.update_single_setting_with_lock(setting, value)


def _sort_times(settings):
    settings[TIMES].sort(key=lambda x: datetime.strptime(x[TIME], "%H:%M").time())


def position_window_on_tray(window: sg.Window, keep_x=False):
    window.hide()
    mouse_pos = win32api.GetCursorPos()
    monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint(mouse_pos))
    _, _, monitor_width, monitor_height = monitor_info.get("Work")
    win_width, win_height = window.size
    x_pos = (
        window.current_location()[0]
        if keep_x
        else min(max(mouse_pos[0] - win_width // 2, 0), monitor_width - win_width)
    )
    y_pos = max(monitor_height - win_height, 0)
    window.move(x_pos, y_pos)
    window.un_hide()
    window.bring_to_front()
    window.TKroot.focus_force()


def set_monitor_brightness(new_brightness):
    for _ in range(3):
        try:
            for monitor in monitorcontrol.get_monitors():
                with monitor:
                    old = monitor.get_luminance()
                    if old == new_brightness:
                        continue
                    monitor.set_luminance(new_brightness)
            break
        except (ValueError, monitorcontrol.VCPError) as e:
            print(e)
            time.sleep(0.2)


def get_monitor_brightness():
    with monitorcontrol.get_monitors()[0] as monitor:
        return monitor.get_luminance()


class TimeVal:
    def __init__(self, time: str, value: int):
        self.time = datetime.strptime(time, "%H:%M").time()
        self.value = value

    def __repr__(self) -> str:
        return f"{self.time} --> {self.value}"


def update_brightness_based_on_time():
    with SettingsSingleton().settings() as settings:
        if not settings[TIMES]:
            return
        curr_time = datetime.now()

        if settings[SHOULD_HOLD]:
            hold_start = datetime.fromisoformat(settings[HOLD_START_TIME])
            held = (curr_time - hold_start).seconds // 60
            if held < settings[HOLD_TIME]:
                return False
            settings[SHOULD_HOLD] = False
            SettingsSingleton().update_single_setting_with_lock(SHOULD_HOLD, False)

        time_vals = [TimeVal(row[TIME], row[VALUE]) for row in settings[TIMES]]
        prev_time_val = time_vals[-1]
        for next_time_val in time_vals:
            if next_time_val.time > curr_time.time():
                break
            prev_time_val = next_time_val

        next_time = datetime.combine(date.today(), next_time_val.time)
        prev_time = datetime.combine(date.today(), prev_time_val.time)

        if next_time_val == prev_time_val:
            next_time_val = time_vals[0]
            next_time = datetime.combine(
                date.today() + timedelta(days=1), next_time_val.time
            )

        ratio = (
            1
            if next_time == prev_time
            else (curr_time - prev_time) / (next_time - prev_time)
        )
        new_brightness = int(
            next_time_val.value * ratio + prev_time_val.value * (1 - ratio)
        )

        # print(prev_time_val, curr_time.time(), next_time_val, f"{ratio:0.5}", new_brightness)

        set_monitor_brightness(new_brightness)
