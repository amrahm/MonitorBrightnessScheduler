import os
import PySimpleGUI as sg
from psgtray import SystemTray
from infrastructure import *
from settingsview import *
from sliderwindow import *
from timeloop import *


def main():
    sg.theme("Dark Grey 2")

    slider_window = get_slider_window()
    slider_window.hide()
    settings_view = SettingsView()

    tray = get_tray(slider_window)

    time_loop = TimeLoop()
    time_loop.start()

    while True:
        window, event, values = sg.read_all_windows()

        # Set event to value from tray if it's a tray event
        if event == tray.key:
            event = values[event]

        if event in (EXIT_PROGRAM, sg.WIN_CLOSED):
            break
        elif event in (OPEN_SETTINGS, sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED):
            settings_view.get_settings_window()
        elif event == sg.EVENT_SYSTEM_TRAY_ICON_ACTIVATED:
            show_slider_window(slider_window)
        elif window == slider_window:
            handle_slider_window_events(window, event, values)
        elif window == settings_view.window:
            settings_view.handle_settings_window_events(window, event, values)

    tray.close()
    slider_window.close()


def get_tray(settings_window):
    tooltip = "Click to open Brightness Slider, double click to open settings"
    menu = ["", [OPEN_SETTINGS, EXIT_PROGRAM]]
    return SystemTray(
        menu,
        single_click_events=True,
        window=settings_window,
        tooltip=tooltip,
        icon=os.path.join(WORKING_DIR, "favicon.ico"),
    )


if __name__ == "__main__":
    main()
