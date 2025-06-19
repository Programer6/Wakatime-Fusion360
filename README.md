# Installation Guide
### Credits
credits to @its-kronos for hotfixing while i was asleep 


## Prerequisites

- Fusion 360
- Python
- Windows 10/11

## Download

1. Clone the repository:
   ```bash
   git clone https://github.com/LiveWaffle/Hackatime-Fusion360.git

2. Rename the cloned folder to "FusionWakaTime"

3. Open Fusion 360 > Utilities > Addins > Create New

4. *Optional* Check Run on startup


   ![Guide Part 1](./guidepart1.png)
   ![Guide Image 2](./guideimage2.png)



# If Fusion 360 instantly crashes, or the program doesn't work follow these steps:

Navigate to the Python folder inside Fusion’s installation path:
C:\Users\YOURUSER\AppData\Local\Autodesk\webdeploy\production 
There should be 2 folders - Check for one with all the files in it including python.exe and then at the address bar type ```cmd``` (or navigate there using command prompt)

and then run
```
./python.exe -m pip install requests
```
