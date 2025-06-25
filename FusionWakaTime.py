import adsk.core
import adsk.fusion

import traceback
import hashlib
import os
import sys
import time
import subprocess
import ctypes
import configparser
from subprocess import Popen, PIPE, STDOUT
from subprocess import CREATE_NO_WINDOW
from . import commands
from .lib import fusionAddInUtils as futil
import threading
def checkInstall():
    pypath = os.path.dirname(sys.executable)
    exists = os.path.exists(pypath + "/Lib/site-packages/requests")
    if exists == False:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "chardet"])
        app.log("Dependencies Installed...!")
    if exists == True:
        app.log("Dependencies already installed...!")

checkInstall()
import requests
import platform
import chardet


app = adsk.core.Application.get()


ui = app.userInterface










lastActive = time.time()
heartbeat_interval = 30
inactive_threshold = 30

def getActiveDocument():
    try:
        folder = None
        design = None

        design= app.activeDocument
        if design:
            if design.dataFile:
                folder = design.dataFile.parentFolder
                if folder is None:
                    folder = design
            else:
                folder = design
    except Exception as e:
        app.log(f"Could not get Active Document: {e}")
    return [folder,design]

def update_activity():
    global lastActive
    lastActive = time.time()

stopEvent = threading.Event()

def run(context):
    try:
        Contents()  # or move all its contents here directly
    except Exception as e:
        app.log(f"Run failed: {str(e)}")



def Contents():
    app.log("part -1")
    try:
        def DetectEncode():
         configPath = os.path.join(os.environ['USERPROFILE'], '.wakatime.cfg')
         with open(configPath, "rb") as file:
                data = file.read()
                encoded = chardet.detect(data)
                encoding = encoded["encoding"]
                if encoding is None:
                    return "UTF-8"
                else:
                    return encoding
        DetectEncode()

        app.log(DetectEncode())
        app.log("part 1")
        parse=configparser.ConfigParser()
        parsePath = os.path.join(os.environ['USERPROFILE'], '.wakatime.cfg')
        parse.read(parsePath, encoding=DetectEncode())

        if os.path.exists(parsePath):
            APIKEY = parse.get('settings','api_key')
            APIURL = parse.get('settings','api_url')
            print("Key: "+APIKEY + " Url: "+ APIURL)
        else:
            ErrorMessage = ctypes.windll.user32.MessageBoxW(0, u"Please use the script to download the hackatime files! https://hackatime.hackclub.com/", u"Invalid File", 0)

        arch = platform.machine()
        app.log(platform.machine())

        app.log("part 2")
        if arch == "AMD64":
            WakaTimePath = os.path.join(os.path.dirname(__file__), "WakaTimeCli.exe")
        elif arch in ("ARM64", "aarch64"):
            WakaTimePath = os.path.join(os.path.dirname(__file__), "WakaTimeCliARM64.exe")
        elif arch in ("i386", "x86"):
            WakaTimePath = os.path.join(os.path.dirname(__file__), "WakaTimeCli386.exe")
        else:
            app.log("Unsupported CPU platform ")


        timeout = 30
        start_time = time.time()
        design = None


        data = getActiveDocument()

        app.log("FusionDocument type: " + str(design))

        url = "https://hackatime.hackclub.com/api/v1/my/heartbeats"

        app.log(url)

        
        lastKnownProjectName = "Untitled"
        lastKnownDesignName = "Untitled"

        def sendHeartBeat():
            getActiveDocument()
            global lastKnownProjectName
            global lastKnownDesignName
            folder, design = getActiveDocument()
            if folder:
                lastKnownProjectName = folder.name
            folderName = lastKnownProjectName
            
            if design:
                lastKnownDesignName = design.name
            designName = lastKnownDesignName
                
            timestamp = int(time.time())
            if time.time() - lastActive < inactive_threshold: 
                    CliCommand = [
                    WakaTimePath,
                    '--key', APIKEY,
                    '--entity', folderName,
                    '--time', str(timestamp),
                    '--write',
                    '--plugin', 'fusion360-wakatime/0.0.1',
                    '--alternate-project', designName,
                    '--category', "designing",
                    '--language', 'Fusion360',
                    '--is-unsaved-entity',
                    ]
                    try:
                        app.log("Running CLI: " + ' '.join(CliCommand))
                        result = subprocess.run(CliCommand, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                        app.log(f"Heartbeat Sent under project: {folderName}")
                    except Exception as e:
                        app.log("error!!")
                        app.log("Error sending heartbeat: " + str(e))

            else:
                app.log("User Inactive")


        def handleUserInteractions(args):
            update_activity()


        def onCommandUse(args: adsk.core.ApplicationCommandEventArgs):
            update_activity()
            cmdID = args.commandId
            app.log(f'Command starting: {cmdID}')
        futil.add_handler(ui.commandStarting, onCommandUse)

        def looping():
            while not stopEvent.is_set():
                sendHeartBeat()
                time.sleep(heartbeat_interval)
        threading.Thread(target=looping,daemon=True).start()
    except Exception as e:
        app.log("Error when running!!!")
        app.log(e)
        

def stop():
    app.log("Shutting Fusion WakaTime down")
    futil.clear_handlers()
    stopEvent.set()

