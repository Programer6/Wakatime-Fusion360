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

<p align="center">
<img width="309" center alt="Screenshot 2025-07-05 at 11 36 13 AM" src="https://github.com/user-attachments/assets/881233cb-ea98-448f-8b6e-5f43c6b5b87d" />

<br>

<img width="397" alt="Screenshot 2025-07-05 at 11 34 58 AM" src="https://github.com/user-attachments/assets/d77d50e4-7da3-4f80-9139-c754ee72b6e0" />
  
</p>

#### 2. Rename the Folder
-   Rename the unzipped folder from `Hackatime-Fusion360-main` to exactly:
    **`FusionWakaTime`**
    *(This step is very important!)*
<img width="173" alt="Screenshot 2025-07-05 at 11 40 42 AM" src="https://github.com/user-attachments/assets/7b1a4d75-fba6-454a-aa7c-1781b04aea50" />

#### 3. Add to Fusion 360
-   Open Fusion 360.
-   Go to the **UTILITIES** tab and click the **Scripts and Add-Ins** icon.
-   In the new window, select the **Add-Ins** tab.
-   Click the green **+** icon next to "My Add-Ins".
-   In the file dialog, navigate to and select the `FusionWakaTime` folder you renamed in Step 2.
![My-add-in](https://github.com/user-attachments/assets/8eede38a-9a08-4618-9fb3-20b0fc1543e9)
![FusionWakaTime](https://github.com/user-attachments/assets/29a37634-eb1c-4bf2-b728-bc83e3078db6)



#### 4. Run the Add-in
-   The `FusionWakaTime` add-in will now appear in your list.
-   Select it and click **Run**.
-   **IMPORTANT:** Check the **Run on startup** box so it runs automatically every time you open Fusion 360.

The first time you run it, the add-in will automatically download the necessary command-line tool in the background.

---

### First-Time Configuration (API Key)

For the add-in to log your time, you need to tell it your secret WakaTime API key.

1.  Find your **Secret API Key** on your settings page:
    *   **WakaTime:** [wakatime.com/settings/api-key](https://wakatime.com/settings/api-key)
    *   **HackaTime:** [hackatime.hackclub.com/my/settings](https://hackatime.hackclub.com/my/settings)

2.  Create a configuration file in your user home directory. The file must be named `.wakatime.cfg`.
    *   **Windows:** `C:\Users\YOUR_USERNAME\.wakatime.cfg`
    *   **macOS:** `/Users/YOUR_USERNAME/.wakatime.cfg`

3.  Open the file in a text editor and add the correct configuration based on which service you use.

    <br>

    **For Hack Club / HackaTime Users:**
    Your file must include both the `api_key` and the custom `api_url`.

    ```ini
    [settings]
    api_key = YOUR_HACKATIME_API_KEY_HERE
    api_url = https://hackatime.hackclub.com/api/hackatime/v1
    heartbeat_rate_limit_seconds = 30
    ```

    **For Standard WakaTime.com Users:**
    Your file only needs the `api_key`. The `api_url` will default to WakaTime.com.

    ```ini
    [settings]
    api_key = YOUR_WAKATIME_API_KEY_HERE
    ```

    *Note: You can add other advanced configurations to this file if needed. See the [official documentation](https://github.com/wakatime/wakatime-cli/blob/develop/USAGE.md#ini-config-file) for all available options.*

4.  Save the file. Restart Fusion 360, and your time will start logging automatically!

---

## Troubleshooting

-   **My time isn't appearing on my dashboard:**
    1.  Double-check that your API key and `api_url` (if needed) are correct in your `.wakatime.cfg` file.
    2.  In Fusion 360, go to **UTILITIES -> Text Commands** (or use `Ctrl+Alt+C`). This opens a console that will show any error messages from the add-in.

## Credits

-   Credits to **@its-kronos** for hotfixing and contributions.
