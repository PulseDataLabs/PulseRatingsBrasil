import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_page():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Opening page...")
        driver.get("http://localhost:8081/consulta.html")
        time.sleep(3) # Wait for page load and table init
        
        print("\n--- Console Logs ---")
        for entry in driver.get_log('browser'):
            print(f"[{entry['level']}] {entry['message']}")
            
        print("\nChecking element states:")
        try:
            # Check toggle view checkbox state
            toggle = driver.find_element("id", "toggle-view")
            print(f"Toggle-view checkbox found. Checked: {toggle.is_selected()}")
        except Exception as e:
            print(f"Toggle-view checkbox not found: {e}")
            
        try:
            updates = driver.find_element("id", "updates-content-list")
            print(f"updates-content-list found. InnerHTML length: {len(updates.get_attribute('innerHTML').strip())}")
            print(f"Content: {updates.text}")
        except Exception as e:
            print(f"updates-content-list not found: {e}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    test_page()
