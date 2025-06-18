# Installation Guide

## Prerequisites

- Fusion 360
- Python
- Windows 10/11

## Download

1. Clone the repository:
   ```bash
   git clone 
   https://github.com/LiveWaffle/Hackatime-Fusion360.git

2. Open Fusion 360 > Utilities > Addins > Create New

3. *Optional* Check Run on startup


   ![Guide Part 1](./guidepart1.png)
   ![Guide Image 2](./guideimage2.png)



# If Fusion 360 instantly crashes, follow these steps:

Navigate to the Python folder inside Fusion’s installation path:
C:\Users\YOURUSER\AppData\Local\Autodesk\webdeploy\production 
There should be 2 folders - Check for one with all the files in it including python and then at the address bar type ```cmd```

Locate the folder that contains python.exe

Open a Command Prompt in that directory and run:
```
python -m pip install requests
```
