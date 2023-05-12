# SlymeGPT
## About
OpenAI GPT API replication with `selenium webdriver` and `undetectable chromedriver`.  
**NOTE:** Uses Chrome.  
Interacts with the official ChatGPT website and sends responses back to the caller, entirely free of charge (as opposed to the official API).  
Does **NOT** use any endpoints (`forefront`, `theb`, etc.)
## Setup
This section describes the setup process for `SlymeGPT`.
### Step 1. Download Chrome WebDriver
Open `Chrome -> Settings -> About Chrome`  
to find your Chrome version (update to latest if available).  
Then go to https://chromedriver.chromium.org/downloads and download the corresponding version.
Add the Chrome WebDriver to your system's PATH variable.
<details>
    <summary>HOW TO ADD TO PATH</summary>
  
    1. Move the downloaded Chrome WebDriver executable to a folder of your choice.
    2. Open your computer's "System Properties" settings.
    3. Click on the "Advanced" tab and then click on the "Environment Variables" button.
    4. Under "System Variables", find the "Path" variable and click "Edit".
    5. Click "New" and add the folder path where the Chrome WebDriver executable is located.
    6. Click "OK" on all open windows to save the changes.
</details>

### Step 2. Config Browser
Change directory to `SlymeGPT` and run `python open_browser.py`

## Functionalities

