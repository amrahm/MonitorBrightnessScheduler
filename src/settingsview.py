import copy
import os
import PySimpleGUI as sg

from src.infrastructure import (
    EXIT_PROGRAM,
    TIME,
    TIMES,
    UPDATE_FREQ,
    VALUE,
    WORKING_DIR,
    SettingsSingleton,
    position_window_on_tray,
)

CANCEL = "Cancel"
OK = "Ok"
INPUT_UPDATE_FREQ = "INPUT_UPDATE_FREQ"
TIME_COLUMN = "TIME_COLUMN"
ADD_TIME = "Add Time"
INPUT_HOURS = "INPUT_HOURS_"
INPUT_MINUTES = "INPUT_MINUTES_"
INPUT_BRIGHTNESS = "INPUT_BRIGHTNESS_"
TIME_ROW_DELETE = "TIME_ROW_DELETE_"


class SettingsView:
    def __init__(self):
        with SettingsSingleton().settings() as settings:
            self.new_settings = copy.deepcopy(settings)
        self.row_inc = 0
        self.row_map = {}
        self.window = None

    def get_time_row(self, row, row_ind=None):
        time, value = row[TIME], row[VALUE]
        hrs, mins = time.split(":") if time else ("", "")
        i = self.row_inc
        self.row_map[i] = (
            row_ind if row_ind is not None else len(self.new_settings[TIMES]) - 1
        )
        self.row_inc += 1
        return [
            sg.Input(
                key=f"{INPUT_HOURS}{i}",
                enable_events=True,
                size=(4, 1),
                do_not_clear=True,
                default_text=hrs,
            ),
            sg.T(":", pad=(0, 0)),
            sg.Input(
                key=f"{INPUT_MINUTES}{i}",
                enable_events=True,
                size=(4, 1),
                do_not_clear=True,
                default_text=mins,
            ),
            sg.Slider(
                range=(0, 100),
                resolution=1,
                orientation="h",
                key=f"{INPUT_BRIGHTNESS}{i}",
                default_value=value,
                enable_events=True,
            ),
            sg.Button(
                image_filename=os.path.join(WORKING_DIR, "delete.png"),
                key=f"{TIME_ROW_DELETE}{i}",
            ),
        ]

    def get_settings_window(self):
        if self.window:
            self.window.bring_to_front()
            return

        with SettingsSingleton().settings() as settings:
            self.new_settings = copy.deepcopy(settings)
        time_rows = [
            self.get_time_row(row, i) for i, row in enumerate(self.new_settings[TIMES])
        ]
        layout = [
            [sg.Column(time_rows, key=TIME_COLUMN)],
            [sg.Push(), sg.B(ADD_TIME), sg.Push()],
            [
                sg.Text("Update Frequency: "),
                sg.In(
                    key=INPUT_UPDATE_FREQ,
                    enable_events=True,
                    size=(4, 1),
                    change_submits=True,
                    do_not_clear=True,
                    default_text=self.new_settings[UPDATE_FREQ],
                ),
                sg.Text(" Seconds"),
            ],
            [
                sg.Button(EXIT_PROGRAM, button_color="white on red"),
                sg.Push(),
                sg.Button(OK),
                sg.Button(CANCEL),
            ],
        ]

        self.window = sg.Window(
            "Monitor Brightness Scheduler Settings",
            layout,
            finalize=True,
            no_titlebar=True,
            keep_on_top=True,
            modal=True,
        )
        position_window_on_tray(self.window)

    def handle_settings_window_events(self, window: sg.Window, event, values):
        """returns True when the OK button is pressed (indicating that settings have changed)"""
        if event == CANCEL:
            self.close_window()
        elif event == OK:
            SettingsSingleton().save_settings(self.new_settings)
            self.close_window()
        elif event == ADD_TIME:
            self.new_settings[TIMES].append({TIME: ":", VALUE: 50})
            window.extend_layout(
                window[TIME_COLUMN],
                [self.get_time_row(self.new_settings[TIMES][-1])],
            )
            window.refresh()
            position_window_on_tray(window, keep_x=True)
        elif event == INPUT_UPDATE_FREQ:
            if not values[event].isnumeric():
                values[event] = values[event][:-1]
                window[event].update(values[event])
            self.new_settings[UPDATE_FREQ] = int(values[event])
        elif INPUT_HOURS in event:
            self.handle_input_hours(event, values, window)
        elif INPUT_MINUTES in event:
            self.handle_input_minutes(window, event, values)
        elif INPUT_BRIGHTNESS in event:
            i = int(str(event).split("_")[-1])
            self.new_settings[TIMES][self.row_map[i]][VALUE] = int(values[event])
        elif TIME_ROW_DELETE in event:
            self.handle_delete(event, window)

    def handle_input_hours(self, event, values, window):
        i = int(str(event).split("_")[-1])
        if not values[event].isnumeric() or int(values[event]) > 23:
            values[event] = values[event][:-1]
            window[event].update(values[event])
        hrtxt = values[event]
        if len(hrtxt) == 2 or len(hrtxt) == 1 and hrtxt not in ["0", "1", "2"]:
            window[f"{INPUT_MINUTES}{i}"].SetFocus()

        curr_mins = window[f"{INPUT_MINUTES}{i}"].get()
        self.new_settings[TIMES][self.row_map[i]][TIME] = f"{values[event]}:{curr_mins}"

    def handle_input_minutes(self, window, event, values):
        i = int(str(event).split("_")[-1])
        if len(values[event]) == 0:
            window[f"{INPUT_HOURS}{i}"].SetFocus()
        elif not values[event].isnumeric() or int(values[event]) > 59:
            values[event] = values[event][:-1]
            window[event].update(values[event])

        curr_hrs = window[f"{INPUT_HOURS}{i}"].get()
        self.new_settings[TIMES][self.row_map[i]][TIME] = f"{curr_hrs}:{values[event]}"

    def handle_delete(self, event, window):
        i = int(str(event).split("_")[-1])
        window[event].hide_row()
        del self.new_settings[TIMES][self.row_map[i]]
        self.row_map[i] = -1
        for j in range(i + 1, self.row_inc):
            self.row_map[j] -= 1
        self.window.refresh()
        position_window_on_tray(self.window, keep_x=True)

    def close_window(self):
        self.window.close()
        self.window = None
        self.row_inc = 0
