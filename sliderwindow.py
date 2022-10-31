import monitorcontrol
import PySimpleGUI as sg
from infrastructure import *


def get_slider_window():
    layout = [
        [
            sg.Push(),
            sg.Text("Set Monitor Brightness:"),
            sg.Push(),
        ],
        [sg.Slider(range=(0, 100), resolution=1, orientation="h", key="brightness_slider")],
        [sg.Checkbox(text="Hold at current value?", enable_events=True, key="hold_checkbox")],
    ]
    window = sg.Window("Settings", layout, finalize=True, no_titlebar=True)
    window.bind("<FocusOut>", "FOCUS OUT")
    window["brightness_slider"].bind("<ButtonRelease-1>", "_RELEASE")
    return window


def show_slider_window(window: sg.Window):
    position_window_on_tray(window)

    with monitorcontrol.get_monitors()[0] as monitor:
        slider = window["brightness_slider"]
        slider.Update(value=monitor.get_luminance())


def handle_slider_window_events(window: sg.Window, event, values):
    match event:
        case "FOCUS OUT":
            window.hide()
        case "brightness_slider_RELEASE":
            val = int(values["brightness_slider"])
            for monitor in monitorcontrol.get_monitors():
                with monitor:
                    monitor.set_luminance(val)
