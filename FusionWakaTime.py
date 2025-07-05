# FusionWakaTime.py - v6.0.0 - Definitive User-Managed Version

import adsk.core
import adsk.fusion
import traceback
import os
import sys
import time
import subprocess
import platform
import configparser
import threading
from pathlib import Path

# --- Globals and Setup ---
app = adsk.core.Application.get()
ui = app.userInterface

# Configuration
ADDIN_NAME = 'FusionWakaTime'
ADDIN_VERSION = '6.0.0'
HEARTBEAT_INTERVAL = 120

# Global state
stop_event = threading.Event()
last_heartbeat_time = 0
CLI_PATH = None

# --- Helper Functions ---

def find_cli_path():
    """Looks for the wakatime-cli executable in standard user locations."""
    global CLI_PATH
    
    # Determine OS and Architecture
    os_name = 'unknown'
    if sys.platform.startswith('linux'): os_name = 'linux'
    elif sys.platform == 'darwin': os_name = 'darwin'
    elif sys.platform == 'win32': os_name = 'windows'
    else: return None

    machine = platform.machine().lower()
    if 'arm64' in machine or 'aarch64' in machine: arch_name = 'arm64'
    elif 'amd64' in machine or 'x86_64' in machine: arch_name = 'amd64'
    else: return None

    cli_filename = f'wakatime-cli-{os_name}-{arch_name}'
    if os_name == 'windows': cli_filename += '.exe'

    # Check in two standard locations: ~/.wakatime/ and ~/
    home_dir = str(Path.home())
    locations_to_check = [
        os.path.join(home_dir, '.wakatime', cli_filename),
        os.path.join(home_dir, cli_filename)
    ]

    for path in locations_to_check:
        if os.path.exists(path):
            if os_name in ('linux', 'darwin') and not os.access(path, os.X_OK):
                app.log(f"--- {ADDIN_NAME} PERMISSION ERROR ---")
                app.log(f"CLI found at {path}, but it is not executable. Please run 'chmod +x \"{path}\"'")
                continue
            CLI_PATH = path
            return CLI_PATH

    app.log(f"--- {ADDIN_NAME} ERROR: WakaTime CLI not found in standard locations. ---")
    app.log("Please download the CLI and place it in your home directory (~) or in ~/.wakatime/")
    return None

def get_wakatime_config_path(): return os.path.join(str(Path.home()), '.wakatime.cfg')

def log_current_config():
    config_file = get_wakatime_config_path()
    app.log("--- WakaTime Configuration ---")
    try:
        parser = configparser.ConfigParser()
        parser.read(config_file)
        api_key = parser.get('settings', 'api_key', fallback="Not found")
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "Set, but too short."
        app.log(f"API Key: {masked_key}")
        api_url = parser.get('settings', 'api_url', fallback="Default (WakaTime.com)")
        app.log(f"API URL: {api_url}")
    except Exception as e: app.log(f"Could not read config file: {e}")
    app.log("----------------------------")

# --- Heartbeat Sending (Using the Direct, Reliable Method) ---

def send_heartbeat(is_write=False):
    global last_heartbeat_time
    if not is_write and (time.time() - last_heartbeat_time < HEARTBEAT_INTERVAL): return
    
    cli = CLI_PATH
    doc = app.activeDocument
    if not cli or not doc: return

    project = "Fusion 360"
    entity = doc.name
    try:
        if doc.dataFile:
            entity = doc.dataFile.name
            if doc.dataFile.parentFolder:
                project = doc.dataFile.parentFolder.name
        elif app.data.activeProject:
            project = app.data.activeProject.name
    except Exception as e:
        app.log(f"{ADDIN_NAME}: Could not determine project name, using default. Error: {e}")

    # --- THE DIRECT METHOD ---
    command_list = [
        cli,
        '--entity', entity,
        '--plugin', f'fusion-360-wakatime/{ADDIN_VERSION}',
        '--alternate-project', project,
        '--language', 'Fusion360',
        '--category', 'designing'
    ]
    if is_write:
        command_list.append('--write')
    elif not doc.dataFile:
        command_list.append('--is-unsaved-entity')

    app.log("--- Preparing Heartbeat ---")
    app.log(f"  - Project: {project}")
    app.log(f"  - Entity: {entity}")
    app.log(f"  - Write: {is_write}")
    app.log("---------------------------")
    
    try:
        # Pass the list directly. DO NOT use shell=True. This is the most reliable way.
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        subprocess.Popen(command_list, creationflags=creationflags)
        
        last_heartbeat_time = time.time()
        app.log("--> Heartbeat command sent successfully.")
    except Exception as e:
        app.log(f'{ADDIN_NAME}: Error sending heartbeat: {e}')

# --- Event Handlers and Main Functions ---

class CommandStartingHandler(adsk.core.ApplicationCommandEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args: adsk.core.ApplicationCommandEventArgs):
        try: send_heartbeat(is_write=False)
        except: app.log(traceback.format_exc())

class SaveHandler(adsk.core.DocumentEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args: adsk.core.DocumentEventArgs):
        try: send_heartbeat(is_write=True)
        except: app.log(traceback.format_exc())

handlers = []

def run(context):
    try:
        if not os.path.exists(get_wakatime_config_path()):
            ui.messageBox("WakaTime config file (~/.wakatime.cfg) not found.", f"{ADDIN_NAME} Error")
            return
        
        if not find_cli_path():
            return

        on_command_starting = CommandStartingHandler()
        ui.commandStarting.add(on_command_starting)
        handlers.append((ui.commandStarting, on_command_starting))

        on_save = SaveHandler()
        app.documentSaved.add(on_save)
        handlers.append((app.documentSaved, on_save))
        
        app.log(f'{ADDIN_NAME} v{ADDIN_VERSION} started successfully.')
        app.log(f"Using CLI from: {CLI_PATH}")
        log_current_config()
    except:
        app.log(traceback.format_exc())

def stop(context):
    try:
        for event, handler in handlers: event.remove(handler)
        stop_event.set()
        app.log(f'{ADDIN_NAME} stopped.')
    except:
        app.log(traceback.format_exc())
