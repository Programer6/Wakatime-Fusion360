# Hackatime-Fusion360
Log the time you spend designing in Autodesk Fusion 360 automatically with [WakaTime](https://wakatime.com) or if you're a [Hackclubber](https://hackclub.com) with [Hakatime](https://hackatime.hackclub.com).

This add-in works seamlessly in the background on both **Windows** and **macOS**.

## Features:
**Automatic Time Tracking:** The add-in detects your activity automatically every 2 Minutes.
-   **Cross-Platform:** Works identically on Windows and macOS.
-   **Intelligent CLI Handling:** Automatically downloads and manages the correct WakaTime command-line tool for your system.
-   **Project Detection:** Automatically detects the active file and uses its **parent folder** as the project name in WakaTime.
-   **Startup-Ready:** Set it to run on startup and never think about it again.


## Prerequisites

-   Autodesk Fusion 360
-   A free [WakaTime Account](https://wakatime.com/signup)


## Installation Guide

Follow these steps to install the add-in. This process works for both Windows and macOS.

#### 1. Download the Add-in
-   Go to the [main page of this repository](https://github.com/LiveWaffle/Hackatime-Fusion360).
-   Click the green `<> Code` button, then click **Download ZIP**.
-   Unzip the downloaded file. You will get a folder named something like `Hackatime-Fusion360-main`.
<img width="309" alt="Screenshot 2025-07-05 at 11 36 13 AM" src="https://github.com/user-attachments/assets/881233cb-ea98-448f-8b6e-5f43c6b5b87d" />

<br>

<img width="397" alt="Screenshot 2025-07-05 at 11 34 58 AM" src="https://github.com/user-attachments/assets/d77d50e4-7da3-4f80-9139-c754ee72b6e0" />


#### 2. Rename the Folder
-   Rename the unzipped folder from `Hackatime-Fusion360-main` to exactly:
    **`FusionWakaTime`**
    *(This step is very important!)*

#### 3. Add to Fusion 360
-   Open Fusion 360.
-   Go to the **UTILITIES** tab and click the **Scripts and Add-Ins** icon.
-   In the new window, select the **Add-Ins** tab.
-   Click the green **+** icon next to "My Add-Ins".
-   ![guideimage2](https://github.com/LiveWaffle/Hackatime-Fusion360/assets/175021115/285c57b7-5a04-4054-9549-14a01c40f283)

-   In the file dialog, navigate to and select the `FusionWakaTime` folder you renamed in Step 2.

#### 4. Run the Add-in
-   The `FusionWakaTime` add-in will now appear in your list.
-   Select it and click **Run**.
-   **IMPORTANT:** Check the **Run on startup** box so it runs automatically every time you open Fusion 360.

The first time you run it, the add-in will automatically download the necessary command-line tool in the background.

---

## First-Time Configuration (API Key)

For the add-in to log your time, you need to tell it your secret WakaTime API key.

1.  Find your **Secret API Key** on your [WakaTime Settings page](https://wakatime.com/settings/api-key).

2.  Create a configuration file in your user home directory. The file must be named `.wakatime.cfg`.
    -   **Windows:** `C:\Users\YOUR_USERNAME\.wakatime.cfg`
    -   **macOS:** `/Users/YOUR_USERNAME/.wakatime.cfg`

3.  Open the file in a text editor and add the following lines, pasting your key where indicated:

    ```ini
    [settings]
    api_key = YOUR_SECRET_API_KEY_HERE
    ```

4.  Save the file. Restart Fusion 360, and your time will start logging automatically!

## Credits

-   Credits to **@its-kronos** for hotfixing and contributions.
