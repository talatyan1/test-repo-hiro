import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

PROFILE_PATH = r"C:\readdy_profile"

def capture_profiles():
    options = Options()
    options.add_argument(f"user-data-dir={PROFILE_PATH}")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://crowdworks.jp/dashboard")
        time.sleep(5)
        driver.save_screenshot("actual_profile_CrowdWorks.png")
        
        driver.get("https://www.lancers.jp/")
        time.sleep(5)
        driver.save_screenshot("actual_profile_Lancers.png")
        
        driver.get("https://coconala.com/")
        time.sleep(5)
        driver.save_screenshot("actual_profile_Coconala.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    capture_profiles()
