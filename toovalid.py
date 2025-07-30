import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import random
import os
import tkinter as tk
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor
import queue
import logging

OUTPUT_DIR = "results"
BATCH_SIZE = 50
MAX_WORKERS = 3
MIN_DELAY = 0.3
MAX_DELAY = 0.8
WAIT_TIMEOUT = 8

AUTH_URL = (
    'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=4765445b-32c6-49b0-83e6-1d93765276ca'
    '&redirect_uri=https%3A%2F%2Fwww.office.com%2Flandingv2'
    '&response_type=code%20id_token'
    '&scope=openid%20profile%20https%3A%2F%2Fwww.office.com%2Fv2%2FOfficeHome.All'
    '&response_mode=form_post'
    '&nonce=638881404491827874.NzUzMzMwMGQtZWJhNi00MjYxLWJmYTYtMGZkMzdmMDVkODViZDEzYzdkNTUtZjFiZi00Zjg2LWEwOTAtZmQxMDE3YmNiODRi'
    '&ui_locales=en-US&mkt=en-US'
    '&client-request-id=aef0c282-9b1f-42c6-8a29-36bfdc4cbe5d'
    '&state=random_state_string'
    '&x-client-SKU=ID_NET8_0&x-client-ver=8.5.0.0&sso_reload=true'
)

def start_driver():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--window-size=1200,800")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument("--blink-settings=imagesEnabled=false")
    return uc.Chrome(options=options)

def timestamped_filename():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, f"valid_{ts}.txt")

def select_email_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    root.destroy()
    if not file_path:
        print("No file selected. Exiting.")
        exit(1)
    return file_path

def validate_emails(emails, valid_file):
    valid_count, invalid_count, unknown_count, error_count = 0, 0, 0, 0
    email_queue = queue.Queue()
    for email in emails:
        email_queue.put(email)

    print(f"🚀 Starting Microsoft email validator — {len(emails)} emails to scan.")
    print(f"📦 Browser restarts every {BATCH_SIZE} emails.")
    print(f"🕒 Delay between checks: {MIN_DELAY}-{MAX_DELAY} sec\n")

    def worker():
        nonlocal valid_count, invalid_count, unknown_count, error_count
        driver = start_driver()
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        batch_count = 0

        while not email_queue.empty():
            try:
                email = email_queue.get_nowait()
                driver.get(AUTH_URL)
                email_input = wait.until(EC.presence_of_element_located((By.ID, "i0116")))
                email_input.clear()
                email_input.send_keys(email)
                next_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
                next_btn.click()

                wait.until(lambda d: d.current_url != AUTH_URL or "We couldn't find an account" in d.page_source)

                current_url = driver.current_url
                page_source = driver.page_source
                log = ""

                if current_url != AUTH_URL:
                    log = f"[VALID/REDIRECT] → {current_url}"
                    with open(valid_file, "a", encoding='utf-8') as vf:
                        vf.write(email + "\n")
                    valid_count += 1
                    print(f"✅ {email}: {log}")
                elif "Enter password" in page_source or "Forgot my password" in page_source:
                    log = "[VALID/PASSWORD] Password prompt visible"
                    with open(valid_file, "a", encoding='utf-8') as vf:
                        vf.write(email + "\n")
                    valid_count += 1
                    print(f"✅ {email}: {log}")
                elif "account doesn't exist" in page_source or "We couldn't find an account" in page_source:
                    log = "[INVALID] Account not found"
                    print(f"❌ {email}: {log}")
                    invalid_count += 1
                else:
                    log = f"[UNKNOWN] URL: {current_url}"
                    print(f"❓ {email}: {log}")
                    unknown_count += 1

                batch_count += 1
                if batch_count >= BATCH_SIZE:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = start_driver()
                    wait = WebDriverWait(driver, WAIT_TIMEOUT)
                    batch_count = 0

                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

            except queue.Empty:
                break
            except Exception as e:
                error_count += 1
                print(f"💥 [ERROR] {email}: {str(e)}")

        try:
            driver.quit()
        except:
            pass

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(worker) for _ in range(MAX_WORKERS)]
        for future in futures:
            future.result()

    print("\n🎯 Scan Complete!")
    print(f"✅ Valid: {valid_count}")
    print(f"❌ Invalid: {invalid_count}")
    print(f"❓ Unknown: {unknown_count}")
    print(f"💥 Errors: {error_count}")
    print(f"\n📁 Valid emails saved in: {valid_file}")

if __name__ == "__main__":
    logging.basicConfig(
        filename=f'validator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    file_path = select_email_file()
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            raw_emails = [line.strip() for line in f if line.strip()]
        unique_emails = list(set(raw_emails))
        validate_emails(unique_emails, timestamped_filename())
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        exit(1)
