import monitorcontrol
import PySimpleGUI as sg
from infrastructure import *

BRIGHTNESS_SLIDER = "BRIGHTNESS_SLIDER"
CHECKBOX_HOLD = "CHECKBOX_HOLD"
INPUT_HOLD = "INPUT_HOLD"
FOCUS_OUT = "FOCUS_OUT"


def get_slider_window():
    with SettingsSingleton().settings() as settings:
        layout = [
            [
                sg.Push(),
                sg.Text("Set Monitor Brightness:"),
                sg.Push(),
            ],
            [sg.Slider(range=(0, 100), resolution=1, orientation="h", key=BRIGHTNESS_SLIDER)],
            [
                sg.Checkbox(text="Hold?", enable_events=True, key=CHECKBOX_HOLD, default=settings[SHOULD_HOLD]),
                sg.Text("for"),
                sg.Input(
                    key=INPUT_HOLD,
                    enable_events=True,
                    size=(4, 1),
                    do_not_clear=True,
                    default_text=settings[HOLD_TIME],
                ),
                sg.Text("minutes"),
            ],
        ]
    window = sg.Window("Brightness Slider", layout, finalize=True, no_titlebar=True)
    _init_slider_value(window)
    window.bind("<FocusOut>", FOCUS_OUT)
    window[BRIGHTNESS_SLIDER].bind("<ButtonRelease-1>", "_RELEASE")
    return window


def show_slider_window(window: sg.Window):
    position_window_on_tray(window)
    _init_slider_value(window)
    with SettingsSingleton().settings() as settings:
        window[CHECKBOX_HOLD].update(value=settings[SHOULD_HOLD])
        window[INPUT_HOLD].update(value=settings[HOLD_TIME])


def _init_slider_value(window: sg.Window):
    with monitorcontrol.get_monitors()[0] as monitor:
        slider = window[BRIGHTNESS_SLIDER]
        slider.Update(value=monitor.get_luminance())


def handle_slider_window_events(window: sg.Window, event, values):
    if event == FOCUS_OUT:
        window.hide()
    elif event == f"{BRIGHTNESS_SLIDER}_RELEASE":
        val = int(values[BRIGHTNESS_SLIDER])
        for monitor in monitorcontrol.get_monitors():
            with monitor:
                monitor.set_luminance(val)

        window[CHECKBOX_HOLD].update(value=True)
        SettingsSingleton().update_single_setting(HOLD_START_TIME, datetime.now().isoformat())
        SettingsSingleton().update_single_setting(SHOULD_HOLD, True)
    elif event == CHECKBOX_HOLD:
        SettingsSingleton().update_single_setting(HOLD_START_TIME, datetime.now().isoformat())
        SettingsSingleton().update_single_setting(SHOULD_HOLD, values[event])
    elif event == INPUT_HOLD:
        if not values[event]:
            return
        if not values[event].isnumeric():
            values[event] = values[event][:-1]
            window[event].update(values[event])
        SettingsSingleton().update_single_setting(HOLD_TIME, int(values[event]))
