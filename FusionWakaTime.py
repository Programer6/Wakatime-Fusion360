import adsk.core
import adsk.fusion
import traceback
import os
import sys
import time
import subprocess
import platform
import urllib.request
import zipfile
import stat
import threading
import json
from pathlib import Path

# --- Globals and Setup ---
app = adsk.core.Application.get()
ui = app.userInterface

# Configuration
ADDIN_NAME = 'FusionWakaTime'
ADDIN_VERSION = '2.0.0' 
HEARTBEAT_INTERVAL = 120  

stop_event = threading.Event()
last_heartbeat_time = 0


RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wakatime-cli-data')
CLI_PATH = None

def get_os_and_arch():
    """Determines the OS and architecture for the WakaTime CLI."""
    os_name = 'unknown'
    arch_name = 'unknown'

    if sys.platform == 'win32':
        os_name = 'windows'
    elif sys.platform == 'darwin': 
        os_name = 'darwin'
    else: 
        return None, None

    machine = platform.machine().lower()
    if 'amd64' in machine or 'x86_64' in machine:
        arch_name = 'amd64'
    elif 'arm64' in machine or 'aarch64' in machine:
        arch_name = 'arm64'
    elif 'i386' in machine or 'x86' in machine:
        arch_name = '386'
    else:
        return None, None
        
    return os_name, arch_name

def get_cli_path():
    """Gets the path to the wakatime-cli executable, downloading it if necessary."""
    global CLI_PATH
    if CLI_PATH and os.path.exists(CLI_PATH):
        return CLI_PATH

    os_name, arch_name = get_os_and_arch()
    if not os_name or not arch_name:
        app.log(f'{ADDIN_NAME}: Unsupported OS or architecture.')
        return None
    
    cli_filename = f'wakatime-cli-{os_name}-{arch_name}'
    if os_name == 'windows':
        cli_filename += '.exe'

    final_cli_path = os.path.join(RESOURCES_DIR, cli_filename)

    if os.path.exists(final_cli_path):
        CLI_PATH = final_cli_path
        return CLI_PATH

    app.log(f'{ADDIN_NAME}: wakatime-cli not found. Downloading...')
    if not os.path.exists(RESOURCES_DIR):
        os.makedirs(RESOURCES_DIR)

    try:
        latest_release_url = "https://api.github.com/repos/wakatime/wakatime-cli/releases/latest"
        with urllib.request.urlopen(latest_release_url) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            app.log(f'{ADDIN_NAME}: Latest CLI version is {latest_version}.')
    except Exception as e:
        app.log(f"{ADDIN_NAME}: Could not fetch latest version tag, using fallback. Error: {e}")
        latest_version = "v1.89.1" 

    download_url = f'https://github.com/wakatime/wakatime-cli/releases/download/{latest_version}/wakatime-cli-{os_name}-{arch_name}.zip'
    zip_path = os.path.join(RESOURCES_DIR, 'wakatime-cli.zip')

    try:
        app.log(f'{ADDIN_NAME}: Downloading from {download_url}')
        urllib.request.urlretrieve(download_url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(RESOURCES_DIR)
        
        os.remove(zip_path)

        if os_name != 'windows' and os.path.exists(final_cli_path):
            os.chmod(final_cli_path, os.stat(final_cli_path).st_mode | stat.S_IEXEC)

        app.log(f'{ADDIN_NAME}: CLI downloaded and unpacked successfully.')
        CLI_PATH = final_cli_path
        return CLI_PATH

    except Exception as e:
        ui.messageBox(f'Error downloading WakaTime CLI: {e}')
        app.log(f'{ADDIN_NAME}: Error downloading or extracting wakatime-cli: {e}')
        return None

def get_wakatime_config_path():
    """Returns the cross-platform path to the .wakatime.cfg file."""
    return os.path.join(str(Path.home()), '.wakatime.cfg')

def send_heartbeat(is_write=False):
    """Constructs the command and sends a heartbeat to the WakaTime API."""
    cli = get_cli_path()
    if not cli:
        app.log(f'{ADDIN_NAME}: Cannot send heartbeat, wakatime-cli path is not configured.')
        return

    doc = app.activeDocument
    if not doc: return

    entity = doc.name
    project = "Unsaved Project"
    if doc.dataFile:
        entity = doc.dataFile.name
        if doc.dataFile.parentFolder:
            project = doc.dataFile.parentFolder.name
    
    command = [ cli, '--entity', entity, '--plugin', f'fusion-360-wakatime/{ADDIN_VERSION}', '--project', project ]
    if is_write:
        command.append('--write')
    
    creationflags = 0
    if sys.platform == 'win32':
        creationflags = subprocess.CREATE_NO_WINDOW

    app.log(f'{ADDIN_NAME}: Sending heartbeat: {" ".join(command)}')
    try:
        subprocess.Popen(command, creationflags=creationflags)
        global last_heartbeat_time
        last_heartbeat_time = time.time()
    except Exception as e:
        app.log(f'{ADDIN_NAME}: Error sending heartbeat: {e}')


class ActivityHandler(adsk.core.DocumentEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: adsk.core.DocumentEventArgs):
        try:
            # Any tracked event means the user is active. Send a heartbeat if enough time has passed.
            if time.time() - last_heartbeat_time > HEARTBEAT_INTERVAL:
                is_write = isinstance(args, adsk.core.DocumentSavingEventArgs)
                send_heartbeat(is_write=is_write)
        except:
            app.log(traceback.format_exc())

handlers = []

def run(context):
    try:
        if not os.path.exists(get_wakatime_config_path()):
            ui.messageBox(f"WakaTime API Key not found.\nPlease create the file:\n{get_wakatime_config_path()}\n\nand add your API key before restarting Fusion 360.", f"{ADDIN_NAME} Setup")
            return
        
        get_cli_path() 

        on_activity = ActivityHandler()
        doc_events = [app.documentActivated, app.documentSaved]
        
        for event in doc_events:
            event.add(on_activity)
            handlers.append((event, on_activity))

        app.log(f'{ADDIN_NAME} v{ADDIN_VERSION} started successfully.')
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
