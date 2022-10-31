import json
import win32api
import PySimpleGUI as sg
from os.path import exists
from typing import Dict, List
from datetime import datetime

Settings = Dict[str, List | int]
SETTINGS_PATH = "settings.json"


def load_settings() -> Settings:
    if exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as jsonfile:
            settings = json.load(jsonfile)
    else:
        settings: Settings = {"TIMES": [], "UPDATE_FREQ": 10}
        save_settings()
    return settings


def save_settings(settings: Settings):
    seen = set()
    to_del = []
    for i, time in enumerate(settings["TIMES"]):
        time = time["TIME"]
        hrs, mins = time.split(":") if time else ("", "")
        if not hrs and not mins:
            to_del.append(i)
            continue
        elif not hrs:
            settings["TIMES"][i]["TIME"] = time = f"00:{mins}"
        elif not mins:
            settings["TIMES"][i]["TIME"] = time = f"{hrs}:00"

        if time in seen:
            to_del.append(i)
        seen.add(time)

    for i in sorted(to_del, reverse=True):
        del settings["TIMES"][i]

    sort_times(settings)
    with open(SETTINGS_PATH, "w") as jsonfile:
        json.dump(settings, jsonfile, indent=4)


def sort_times(settings: Settings):
    settings["TIMES"].sort(key=lambda x: datetime.strptime(x["TIME"], "%H:%M").time())


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
