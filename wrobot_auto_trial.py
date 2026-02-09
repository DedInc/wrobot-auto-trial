import subprocess
import os
import time
import threading

import psutil
import win32gui
import pywinauto
from pywinauto.application import Application

WROBOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WRobot.exe")

# Background thread to auto-dismiss "Trial version" popups
def trial_popup_monitor():
    """Continuously monitors for and dismisses 'Trial version' popups without stealing focus."""
    while True:
        try:
            windows_found = pywinauto.findwindows.find_windows(title="Trial version")
            for hwnd in windows_found:
                try:
                    window_title = win32gui.GetWindowText(hwnd)
                    print(f"Found Trial version popup: '{window_title}' (HWND: {hwnd})")
                    # Send WM_CLOSE without stealing focus
                    win32gui.PostMessage(hwnd, 0x0010, 0, 0)  # WM_CLOSE
                    print("Dismissed Trial version popup (no focus steal)!")
                except Exception as e:
                    print(f"Error handling Trial version popup {hwnd}: {e}")
        except Exception:
            pass  # Silently continue if no windows found
        time.sleep(1)  # Check every second

def find_process_by_name(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc
    return None

def main():
    # Start background thread to monitor and dismiss trial popups
    trial_monitor_thread = threading.Thread(target=trial_popup_monitor, daemon=True)
    trial_monitor_thread.start()
    print("Started Trial version popup monitor thread.")

    process_name = "WRobot.exe"
    while True:
        wrobot_process = find_process_by_name(process_name)

        if not wrobot_process:
            print(f"Process '{process_name}' not found. Starting it from: {WROBOT_PATH}")
            try:
                subprocess.Popen([WROBOT_PATH])
                time.sleep(5)
                wrobot_process = find_process_by_name(process_name)
                if not wrobot_process:
                    print(f"Failed to start '{process_name}'. Retrying in 10 seconds...")
                    time.sleep(10)
                    continue
            except FileNotFoundError:
                print(f"Error: '{WROBOT_PATH}' not found. Please check the path.")
                time.sleep(10)
                continue
            except Exception as e:
                print(f"An error occurred while starting '{process_name}': {e}")
                time.sleep(10)
                continue

            print(f"Found {process_name} with PID: {wrobot_process.pid}")

            try:
                app = Application(backend="uia").connect(process=wrobot_process.pid)
                main_window = app.top_window()
                print("Successfully connected to the main window.")

                def click_button_by_id(automation_id):
                    try:
                        button = main_window.child_window(auto_id=automation_id, control_type="Button")
                        button.wait('visible', timeout=10)
                        button.click()
                        print(f"Button with auto_id '{automation_id}' clicked successfully.")
                    except Exception as e:
                        print(f"Could not find or click button with auto_id '{automation_id}'. Error: {e}")

                print("Waiting for server connection to be established...")
                try:
                    start_time = time.time()
                    timeout = 120
                    check_interval = 1.0
                    def check_launch_bot_ready():
                        try:
                            button = main_window.child_window(auto_id="buttonLaunchBot", control_type="Button")
                            if button.exists(): return button.is_enabled()
                            return False
                        except Exception: return False
                    button_ready = False
                    while time.time() - start_time < timeout:
                        if check_launch_bot_ready():
                            button_ready = True
                            break
                        time.sleep(check_interval)
                    if button_ready:
                        print("Server connection established! Button is now enabled.")
                        click_button_by_id("buttonLaunchBot")
                    else:
                        print("Timeout waiting for server connection to be established.")
                        continue
                except Exception as e:
                    print(f"An error occurred while waiting for server connection. Error: {e}")
                    continue

                try:
                    print("Waiting for 'License Keys Management' window...")
                    license_window = app.window(title="License Keys Management")
                    license_window.wait('visible', timeout=30)
                    print("Found 'License Keys Management' window.")
                    login_button = license_window.child_window(auto_id="buttonLogin", control_type="Button")
                    login_button.wait('visible', timeout=10)
                    threading.Thread(target=lambda: login_button.click()).start()
                    print("Click on 'buttonLogin' (LOGIN) initiated in a separate thread.")

                    try:
                        print("Waiting for captcha window to appear...")
                        time.sleep(1)
                        windows_found = pywinauto.findwindows.find_windows(title_re=".*MessageBox.*")
                        if windows_found:
                            print(f"Found {len(windows_found)} MessageBox windows")
                            for hwnd in windows_found:
                                try:
                                    window_title = win32gui.GetWindowText(hwnd)
                                    print(f"Closing window: '{window_title}' (HWND: {hwnd})")
                                    win32gui.PostMessage(hwnd, 0x0010, 0, 0)
                                    print("Sent WM_CLOSE message to captcha window!")
                                except Exception as e: print(f"Error closing window {hwnd}: {e}")
                        else: print("No MessageBox windows found to close")
                        print("Captcha window handling complete!")
                    except Exception as e: print(f"An error occurred while handling the captcha window. Error: {e}")
                    
                    try:
                        print("Waiting for final WRobot window to appear...")
                        time.sleep(3)

                        print("Looking for final window...")

                        final_window = None
                        for window in app.windows():
                            try:
                                win_text = window.window_text()
                                if "License" not in win_text and window.is_visible():
                                    final_window = window
                                    break
                            except Exception:
                                continue

                        if not final_window:
                            print("Could not find a new window by iterating, trying app.top_window()...")
                            final_window = app.top_window()

                        if final_window:
                            print(f"Found final window: '{final_window.window_text()}'")
                            final_window.set_focus()
                            
                            print("Sending key combination 'Alt+C'...")
                            
                            final_window.type_keys("%c") 
                            
                            print("Key combination 'Alt+C' sent successfully!")
                        else:
                            print("All methods to find the final window have failed.")

                    except Exception as e:
                        print(f"An error occurred while finding the window or sending keys. Error: {e}")

                except Exception as e:
                    print(f"An error occurred while handling the license window. Error: {e}")

            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print(f"'{process_name}' is running. Checking again in 5 seconds.")

        time.sleep(5)

if __name__ == "__main__":
    main()
