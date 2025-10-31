import subprocess
import time
import os

# path to chrome.exe
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# folder to store session data (cookies, login info)
profile_path = r"C:\chrome_profile"

# make folder if not exists
os.makedirs(profile_path, exist_ok=True)

# Temu URL
temu_url = "https://www.temu.com/pk-en/home-decor-products-o3-751.html?opt_level=2&title=Home%20Decor%20Products&_x_enter_scene_type=cate_tab&leaf_type=bro&show_search_type=3&opt1_id=-13"

# full Chrome command
command = f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{profile_path}" "{temu_url}"'

# run Chrome process
print("Launching Chrome with remote debugging...")
subprocess.Popen(command, shell=True)

# give browser some time to open
time.sleep(5)
print("✅ Chrome opened. You can now log in manually if Temu asks.")
