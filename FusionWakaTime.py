

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

# --- Add the bundled 'lib' folder to Python's path ---
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

import chardet

# --- Globals and Setup ---
app = adsk.core.Application.get()
ui = app.userInterface
ADDIN_NAME = 'FusionWakaTime'
ADDIN_VERSION = '6.0.7'
HEARTBEAT_INTERVAL = 120
stop_event = threading.Event()
last_heartbeat_time = 0
CLI_PATH = None

# --- Helper Functions ---
def find_cli_path():
    global CLI_PATH
    os_name = 'windows' if sys.platform == 'win32' else ('darwin' if sys.platform == 'darwin' else 'linux')
    machine = platform.machine().lower()
    arch_name = 'arm64' if 'arm64' in machine or 'aarch64' in machine else 'amd64'
    cli_filename = f'wakatime-cli-{os_name}-{arch_name}'
    if os_name == 'windows': cli_filename += '.exe'
    home_dir = str(Path.home())
    locations_to_check = [os.path.join(home_dir, '.wakatime', cli_filename), os.path.join(home_dir, cli_filename)]
    for path in locations_to_check:
        if os.path.exists(path):
            CLI_PATH = path
            return CLI_PATH
    return None

def get_wakatime_config_path(): 
    return os.path.join(str(Path.home()), '.wakatime.cfg')

def get_config_encoding(config_path):
    try:
        with open(config_path, 'rb') as f: raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'] if result['encoding'] else 'utf-8'
    except Exception as e:
        app.log(f"Config encoding detection failed: {e}")
        return 'utf-8'

def log_current_config():
    config_file = get_wakatime_config_path()
    app.log("--- WakaTime Configuration ---")
    try:
        parser = configparser.ConfigParser()
        parser.read(config_file, encoding=get_config_encoding(config_file))
        api_key = parser.get('settings', 'api_key', fallback="Not found")
        app.log(f"API Key: {f'{api_key[:4]}...{api_key[-4:]}' if len(api_key) > 8 else 'Set, but too short.'}")
        app.log(f"API URL: {parser.get('settings', 'api_url', fallback='Default (WakaTime.com)')}")
    except Exception as e: app.log(f"Could not read config file: {e}")
    app.log("----------------------------")

# --- Heartbeat Sending ---
def send_heartbeat(is_write=False):
    global last_heartbeat_time
    if not is_write and (time.time() - last_heartbeat_time < HEARTBEAT_INTERVAL): return
    cli = CLI_PATH
    try:
        doc = app.activeDocument
        if not doc or not doc.isValid: return
    except RuntimeError: return
    if not cli: return

    app.log("--- Heartbeat Resolution Start ---")
    project = "Fusion 360"
    entity = doc.name if doc else "Untitled"
    try:
        if doc and doc.dataFile:
            app.log("Document has a dataFile. Entity set to dataFile.name.")
            entity = doc.dataFile.name
            app.log("Checking for parentFolder...")
            if doc.dataFile.parentFolder:
                project = doc.dataFile.parentFolder.name
                app.log(f"SUCCESS: Project set from parentFolder: {project}")
            else:
                app.log("parentFolder is None. Checking for activeProject.")
                active_proj = app.data.activeProject
                if active_proj:
                    project = active_proj.name
                    app.log(f"SUCCESS: Project set from activeProject: {project}")
                else:
                    app.log("WARNING: activeProject is also None. Using default project name.")
        elif app.data.activeProject:
            app.log("Document is unsaved. Checking for activeProject.")
            active_proj = app.data.activeProject
            if active_proj:
                project = active_proj.name
                app.log(f"SUCCESS: Project for unsaved file set from activeProject: {project}")
            else:
                app.log("WARNING: activeProject is None for unsaved file.")
        else:
            app.log("No dataFile and no activeProject. Using default names.")
    except Exception as e:
        app.log(f"CRITICAL ERROR during project/entity resolution: {e}")
        app.log(traceback.format_exc())

    app.log(f"--- Final Values: Project='{project}', Entity='{entity}' ---")
    
    command_list = [
        cli, '--entity', entity, '--plugin', f'fusion-360-wakatime/{ADDIN_VERSION}',
        '--project', project, '--language', 'Fusion360', '--category', 'designing'
    ]
    if is_write: command_list.append('--write')
    elif not doc or not doc.dataFile: command_list.append('--is-unsaved-entity')
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        process = subprocess.Popen(
            command_list, creationflags=creationflags,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate(timeout=15)
        if stderr: app.log(f"Heartbeat CLI stderr: {stderr.strip()}")
        last_heartbeat_time = time.time()
        app.log("--> Heartbeat command executed.")
    except Exception as e:
        app.log(f'Error executing heartbeat command: {e}')

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
class DocumentOpenedHandler(adsk.core.DocumentEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args: adsk.core.DocumentEventArgs):
        try: send_heartbeat(is_write=False)
        except: app.log(traceback.format_exc())
handlers = []

# --- Add-in Main Functions ---
def run(context):
    try:
        if not os.path.exists(get_wakatime_config_path()):
            ui.messageBox(f"{ADDIN_NAME} Error: WakaTime config file (~/.wakatime.cfg) not found.")
            return
        if not find_cli_path():
            ui.messageBox(f"{ADDIN_NAME} Error: WakaTime command-line tool not found.")
            return
        on_command_starting = CommandStartingHandler()
        ui.commandStarting.add(on_command_starting)
        handlers.append((ui.commandStarting, on_command_starting))
        on_save = SaveHandler()
        app.documentSaved.add(on_save)
        handlers.append((app.documentSaved, on_save))
        on_document_opened = DocumentOpenedHandler()
        app.documentOpened.add(on_document_opened)
        handlers.append((app.documentOpened, on_document_opened))
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
