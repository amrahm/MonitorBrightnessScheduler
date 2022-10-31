from operator import le
import PySimpleGUI as sg
from infrastructure import *


class SettingsView:
    def __init__(self):
        self.settings = load_settings()
        self.row_inc = 0
        self.row_map = {}
        self.window = None

    def get_time_row(self, row, row_ind=None):
        time, value = row["TIME"], row["VALUE"]
        hrs, mins = time.split(":") if time else ("", "")
        i = self.row_inc
        self.row_map[i] = row_ind if row_ind is not None else len(self.settings["TIMES"]) - 1
        self.row_inc += 1
        return [
            sg.In(
                key=f"INPUT_HOURS_{i}",
                enable_events=True,
                size=(4, 1),
                change_submits=True,
                do_not_clear=True,
                default_text=hrs,
            ),
            sg.T(":", pad=(0, 0)),
            sg.In(
                key=f"INPUT_MINUTES_{i}",
                enable_events=True,
                size=(4, 1),
                change_submits=True,
                do_not_clear=True,
                default_text=mins,
            ),
            sg.Slider(
                range=(0, 100),
                resolution=1,
                orientation="h",
                key=f"INPUT_BRIGHTNESS_{i}",
                default_value=value,
                enable_events=True,
            ),
            sg.Button(image_filename="delete.png", key=f"TIME_ROW_DELETE_{i}"),
        ]

    def get_settings_window(self):
        if self.window:
            self.window.bring_to_front()
            return

        self.settings = load_settings()
        time_rows = [self.get_time_row(row, i) for i, row in enumerate(self.settings["TIMES"])]
        layout = [
            [sg.Column(time_rows, key="TIME_COLUMN")],
            [sg.Push(), sg.B("Add Time"), sg.Push()],
            [
                sg.Text("Update Frequency: "),
                sg.In(
                    key="INPUT_UPDATE_FREQ",
                    enable_events=True,
                    size=(4, 1),
                    change_submits=True,
                    do_not_clear=True,
                    default_text=self.settings["UPDATE_FREQ"],
                ),
                sg.Text(" Seconds"),
            ],
            [
                sg.Button("Exit Program", button_color="white on red"),
                sg.Push(),
                sg.B("Ok"),
                sg.Button("Cancel"),
            ],
        ]

        self.window = sg.Window(
            "Monitor Brightness Scheduler Settings",
            layout,
            finalize=True,
            enable_close_attempted_event=True,
            no_titlebar=True,
            keep_on_top=True,
        )
        position_window_on_tray(self.window)

    def handle_settings_window_events(self, window: sg.Window, event, values):
        """returns True when the OK button is pressed (indicating that settings have changed)"""
        match event:
            case "Cancel" | sg.WIN_CLOSE_ATTEMPTED_EVENT:
                self.close_window()
            case "Ok":
                save_settings(self.settings)
                self.close_window()
                return True
            case "Add Time":
                self.settings["TIMES"].append({"TIME": ":", "VALUE": 50})
                window.extend_layout(
                    window["TIME_COLUMN"],
                    [self.get_time_row(self.settings["TIMES"][-1])],
                )
                self.window.refresh()
                position_window_on_tray(self.window, keep_x=True)
            case "INPUT_UPDATE_FREQ":
                if not values[event].isnumeric():
                    values[event] = values[event][:-1]
                    window[event].update(values[event])
                self.settings["UPDATE_FREQ"] = int(values[event])
            case _:
                if "INPUT_HOURS_" in event:
                    i = int(str(event).split("_")[-1])
                    if not values[event].isnumeric() or int(values[event]) > 23:
                        values[event] = values[event][:-1]
                        window[event].update(values[event])
                    hrtxt = values[event]
                    if len(hrtxt) == 2 or len(hrtxt) == 1 and not hrtxt in ["0", "1", "2"]:
                        window[f"INPUT_MINUTES_{i}"].SetFocus()

                    curr_mins = window[f"INPUT_MINUTES_{i}"].get()
                    self.settings["TIMES"][self.row_map[i]]["TIME"] = f"{values[event]}:{curr_mins}"
                elif "INPUT_MINUTES_" in event:
                    i = int(str(event).split("_")[-1])
                    if len(values[event]) == 0:
                        window[f"INPUT_HOURS_{i}"].SetFocus()
                    elif not values[event].isnumeric() or int(values[event]) > 59:
                        values[event] = values[event][:-1]
                        window[event].update(values[event])

                    curr_hrs = window[f"INPUT_HOURS_{i}"].get()
                    self.settings["TIMES"][self.row_map[i]]["TIME"] = f"{curr_hrs}:{values[event]}"
                elif "INPUT_BRIGHTNESS_" in event:
                    i = int(str(event).split("_")[-1])
                    self.settings["TIMES"][self.row_map[i]]["VALUE"] = int(values[event])
                elif "TIME_ROW_DELETE_" in event:
                    i = int(str(event).split("_")[-1])
                    window[event].hide_row()
                    del self.settings["TIMES"][self.row_map[i]]
                    self.row_map[i] = -1
                    for j in range(i + 1, self.row_inc):
                        self.row_map[j] -= 1
                    self.window.refresh()
                    position_window_on_tray(self.window, keep_x=True)

        return False

    def close_window(self):
        self.window.close()
        self.window = None
        self.row_inc = 0
