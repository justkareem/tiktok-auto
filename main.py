import time
import os
import tempfile
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Proxy and authentication details (placeholder values)
proxy_ip = "proxy_ip:proxy_port"
proxy_user = "proxy_user"
proxy_pass = "proxy_pass"

# Create a temporary directory for the proxy extension
extension_dir = tempfile.mkdtemp()

# Proxy extension manifest
manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    }
}
"""

# Background script for proxy authentication
background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
      singleProxy: {{
        scheme: "http",
        host: "{proxy_ip.split(':')[0]}",
        port: parseInt("{proxy_ip.split(':')[1]}")
      }},
      bypassList: ["localhost"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

chrome.webRequest.onAuthRequired.addListener(
    function handler(details) {{
        return {{
            authCredentials: {{
                username: "{proxy_user}",
                password: "{proxy_pass}"
            }}
        }};
    }},
    {{urls: ["<all_urls>"]}},
    ["blocking"]
);
"""

# Write manifest and background.js files
with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
    f.write(manifest_json)
with open(os.path.join(extension_dir, "background.js"), "w") as f:
    f.write(background_js)

# Configure Chrome options
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
options.add_argument(f"--load-extension={extension_dir}")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(), options=options)

# Override navigator properties
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' });
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 1 });
    """
})


# Function to parse cookies from Netscape format file
def parse_cookies_from_netscape_file(cookie_file="cookies.txt"):
    cookies = []
    with open(cookie_file, "r") as f:
        for line in f:
            if not line.startswith("#") and line.strip():
                parts = line.strip().split("\t")
                if len(parts) >= 7:
                    cookies.append({
                        "domain": parts[0],
                        "path": parts[2],
                        "secure": parts[3].lower() == "true",
                        "expires": int(parts[4]) if parts[4].isdigit() else None,
                        "name": parts[5],
                        "value": parts[6]
                    })
    return cookies


# Load cookies into the browser
def load_cookies_from_netscape_file(driver, cookie_file="cookies.txt"):
    if not os.path.exists(cookie_file) or os.path.getsize(cookie_file) == 0:
        print("Cookies file is missing or empty.")
        return

    cookies = parse_cookies_from_netscape_file(cookie_file)
    for cookie in cookies:
        if 'sameSite' in cookie:
            del cookie['sameSite']
        driver.add_cookie(cookie)
    print("Cookies loaded successfully.")


# Save cookies to Netscape format file
def save_cookies_to_netscape_file(driver, cookie_file="cookies.txt"):
    cookies = driver.get_cookies()
    with open(cookie_file, "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in cookies:
            expires = int(cookie['expires']) if cookie.get('expires') else 0
            f.write(
                f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{str(cookie['secure']).upper()}\t{expires}\t{cookie['name']}\t{cookie['value']}\n")
    print("Cookies saved successfully.")


# Function to post a video to TikTok
def post_to_tiktok(video_path, description):
    driver.get("https://www.tiktok.com/")
    load_cookies_from_netscape_file(driver)
    driver.refresh()
    time.sleep(3)

    # Navigate to upload page
    driver.get("https://www.tiktok.com/tiktokstudio/upload?from=upload")
    time.sleep(5)

    # Upload video
    upload_input = driver.find_element(By.XPATH, "//input[@type='file']")
    upload_input.send_keys(video_path)
    time.sleep(5)

    # Enter description
    description_box = WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
    )
    description_box.click()
    ActionChains(driver).move_to_element(description_box).click().key_down(Keys.CONTROL).send_keys("a").key_up(
        Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
    words = description.split(" ")
    for word in words:
        if word[0] == "#":
            description_box.send_keys(word)
            description_box.send_keys(' ' + Keys.BACKSPACE)
            time.sleep(5)
            description_box.send_keys(Keys.ENTER)
    time.sleep(1)

    # Post video
    post_button = WebDriverWait(driver, 100).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[@class='TUXButton TUXButton--default TUXButton--large TUXButton--primary']"))
    )
    post_button.click()
    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, "//div[@title='Your video has been uploaded']"))
    )
    print("Video posted successfully.")


# Example usage
try:
    post_to_tiktok(video_path="path_to_video.mp4", description="#example #tag")
except Exception as e:
    print("An error occurred:", e)
finally:
    driver.quit()

# Cleanup temporary files
try:
    os.remove(f"{extension_dir}/manifest.json")
    os.remove(f"{extension_dir}/background.js")
    os.rmdir(extension_dir)
except Exception as cleanup_error:
    print("Cleanup error:", cleanup_error)
