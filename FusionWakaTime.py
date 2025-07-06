
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
ADDIN_VERSION = '6.0.1'
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

def get_wakatime_config_path(): 
    return os.path.join(str(Path.home()), '.wakatime.cfg')

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
    except Exception as e: 
        app.log(f"Could not read config file: {e}")
    app.log("----------------------------")

# --- Heartbeat Sending ---

def send_heartbeat(is_write=False):
    global last_heartbeat_time
    if not is_write and (time.time() - last_heartbeat_time < HEARTBEAT_INTERVAL): 
        return
    
    cli = CLI_PATH
    try:
        doc = app.activeDocument
        if not doc or not doc.isValid:
            app.log(f"{ADDIN_NAME}: No valid active document found.")
            return
    except RuntimeError as e:
        app.log(f"{ADDIN_NAME}: Error accessing active document: {str(e)}")
        return
    if not cli: 
        return

    project = "Fusion 360"  # Default project name
    entity = doc.name if doc else "Untitled"
    
    # Debug logging for project name resolution
    app.log("--- Debug: Project Name Resolution ---")
    app.log(f"Initial doc name: {entity}")
    
    try:
        if doc and doc.dataFile:
            app.log("Document has dataFile")
            entity = doc.dataFile.name
            app.log(f"Entity name set to: {entity}")
            
            if doc.dataFile.parentFolder:
                app.log("Document has parent folder")
                project = doc.dataFile.parentFolder.name
                app.log(f"Project name set to: {project}")
            else:
                app.log("No parent folder found")
                
            # Fallback to parent project
            if not project or project == "Fusion 360":
                if doc.dataFile.parentProject:
                    project = doc.dataFile.parentProject.name
                    app.log(f"Using parent project name: {project}")
        elif app.data.activeProject:
            project = app.data.activeProject.name
            app.log(f"Using active project name: {project}")
            
    except Exception as e:
        app.log(f"{ADDIN_NAME}: Project name resolution error: {str(e)}")
        app.log(traceback.format_exc())

    # Construct command with proper quoting for spaces
    command_list = [
        cli,
        '--entity', f'"{entity}"',  # Quote the entity name
        '--plugin', f'fusion-360-wakatime/{ADDIN_VERSION}',
        '--project', f'"{project}"',  # Quote the project name
        '--language', 'Fusion360',
        '--category', 'designing'
    ]
    
    if is_write:
        command_list.append('--write')
    elif not doc or not doc.dataFile:
        command_list.append('--is-unsaved-entity')

    app.log("--- Heartbeat Details ---")
    app.log(f"CLI Path: {cli}")
    app.log(f"Project: {project}")
    app.log(f"Entity: {entity}")
    app.log(f"Command: {' '.join(command_list)}")
    
    try:
        # Use shell=True to handle quoted arguments properly
        command_string = ' '.join(command_list)
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        
        process = subprocess.Popen(
            command_string,
            shell=True,
            creationflags=creationflags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Return strings instead of bytes
        )
        
        stdout, stderr = process.communicate()
        if stdout:
            app.log(f"Heartbeat stdout: {stdout}")
        if stderr:
            app.log(f"Heartbeat stderr: {stderr}")
            
        last_heartbeat_time = time.time()
        app.log("--> Heartbeat sent successfully.")
    except Exception as e:
        app.log(f'{ADDIN_NAME}: Error sending heartbeat: {str(e)}')
        app.log(traceback.format_exc())

# --- Event Handlers ---

class CommandStartingHandler(adsk.core.ApplicationCommandEventHandler):
    def __init__(self): 
        super().__init__()
    
    def notify(self, args: adsk.core.ApplicationCommandEventArgs):
        try: 
            send_heartbeat(is_write=False)
        except: 
            app.log(traceback.format_exc())

class SaveHandler(adsk.core.DocumentEventHandler):
    def __init__(self): 
        super().__init__()
    
    def notify(self, args: adsk.core.DocumentEventArgs):
        try: 
            send_heartbeat(is_write=True)
        except: 
            app.log(traceback.format_exc())

class DocumentOpenedHandler(adsk.core.DocumentEventHandler):
    def __init__(self): 
        super().__init__()
    
    def notify(self, args: adsk.core.DocumentEventArgs):
        try: 
            send_heartbeat(is_write=False)
        except: 
            app.log(traceback.format_exc())

handlers = []

def run(context):
    try:
        if not os.path.exists(get_wakatime_config_path()):
            ui.messageBox("WakaTime config file (~/.wakatime.cfg) not found.", f"{ADDIN_NAME} Error")
            return
        
        if not find_cli_path():
            return

        # Add event handlers
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
        for event, handler in handlers: 
            event.remove(handler)
        stop_event.set()
        app.log(f'{ADDIN_NAME} stopped.')
    except:
        app.log(traceback.format_exc())
