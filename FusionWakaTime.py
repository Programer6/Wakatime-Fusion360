import adsk.core
import adsk.fusion
import traceback
import os
import sys
import time
import subprocess
import platform
import shlex
import configparser
from pathlib import Path

# --- Globals and Setup ---
app = adsk.core.Application.get()
ui = app.userInterface

# Configuration
ADDIN_NAME = 'FusionWakaTime'
ADDIN_VERSION = '2.6.0'
HEARTBEAT_INTERVAL = 120

# Global state
stop_event = threading.Event()
last_heartbeat_time = 0
CLI_PATH = None # Path to the wakatime-cli executable

# --- Helper Functions ---

def find_cli_path():
    """Finds the path to the wakatime-cli executable."""
    global CLI_PATH
    # NOTE: This function assumes the user has placed the wakatime-cli
    # executable inside the add-in's root folder.
    
    # Determine the correct filename based on OS and architecture
    os_name, arch_name = 'unknown', 'unknown'
    if sys.platform == 'win32':
        os_name = 'windows'
    elif sys.platform == 'darwin':
        os_name = 'darwin'
    else:
        app.log(f"{ADDIN_NAME}: Unsupported OS: {sys.platform}")
        return None

    machine = platform.machine().lower()
    if 'amd64' in machine or 'x86_64' in machine: arch_name = 'amd64'
    elif 'arm64' in machine or 'aarch64' in machine: arch_name = 'arm64'
    else:
        app.log(f"{ADDIN_NAME}: Unsupported Architecture: {machine}")
        return None

    cli_filename = f'wakatime-cli-{os_name}-{arch_name}'
    if os_name == 'windows':
        cli_filename += '.exe'
    
    # Check for the CLI in the add-in's directory
    potential_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cli_filename)
    if os.path.exists(potential_path):
        CLI_PATH = potential_path
        return CLI_PATH
    else:
        app.log(f"--- {ADDIN_NAME} ERROR ---")
        app.log(f"WakaTime CLI not found at: {potential_path}")
        app.log("Please download the correct wakatime-cli for your system and place it in the add-in folder.")
        app.log("--------------------------")
        return None

def get_wakatime_config_path(): return os.path.join(str(Path.home()), '.wakatime.cfg')

def log_current_config():
    """Reads the config file and logs the current settings securely."""
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

# --- Heartbeat Sending (THE FIX IS HERE) ---

def send_heartbeat(is_write=False):
    """Identifies the active file/project and sends a heartbeat via the CLI."""
    global last_heartbeat_time
    if not is_write and (time.time() - last_heartbeat_time < HEARTBEAT_INTERVAL): return
    
    # We check for the CLI path here. If it's not found, we do nothing.
    cli = CLI_PATH
    doc = app.activeDocument
    if not cli or not doc: return

    entity = doc.name; project = "Fusion 360"
    if doc.dataFile and doc.dataFile.parentFolder:
        project = doc.dataFile.parentFolder.name
        entity = doc.dataFile.name
    else:
        try:
            if app.data.activeProject: project = app.data.activeProject.name
        except: pass
    
    # --- THE FIX ---
    # Use --alternate-project because it is more robust for names with spaces.
    command_list = [cli, '--entity', entity, '--plugin', f'fusion-360-wakatime/{ADDIN_VERSION}', '--alternate-project', project]
    if is_write: command_list.append('--write')
    
    try:
        command_string = shlex.join(command_list)
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        subprocess.Popen(command_string, shell=True, creationflags=creationflags)
        last_heartbeat_time = time.time()
        app.log(f"Heartbeat sent for project: '{project}' (Write: {is_write})")
    except Exception as e:
        app.log(f'{ADDIN_NAME}: Error sending heartbeat with shlex: {e}')

# --- Event Handlers ---

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

# --- Main Add-in Functions: run() and stop() ---

def run(context):
    try:
        # Check if the user has a config file.
        if not os.path.exists(get_wakatime_config_path()):
            ui.messageBox("WakaTime config file not found. Please create ~/.wakatime.cfg with your API key.", f"{ADDIN_NAME} Error")
            return
        
        # Find the wakatime-cli path at startup.
        if not find_cli_path():
            # An error message is already logged by the function.
            return

        on_command_starting = CommandStartingHandler()
        ui.commandStarting.add(on_command_starting)
        handlers.append((ui.commandStarting, on_command_starting))

        on_save = SaveHandler()
        app.documentSaved.add(on_save)
        handlers.append((app.documentSaved, on_save))
        
        app.log(f'{ADDIN_NAME} v{ADDIN_VERSION} started successfully.')
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
