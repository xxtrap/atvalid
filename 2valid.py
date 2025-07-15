import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# === CONFIG ===
EMAIL_FILE = 'emails.txt'
RESULT_FILE = 'results.txt'
AUTH_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=4765445b-32c6-49b0-83e6-1d93765276ca&redirect_uri=https%3A%2F%2Fwww.office.com%2Flandingv2&response_type=code%20id_token&scope=openid%20profile%20https%3A%2F%2Fwww.office.com%2Fv2%2FOfficeHome.All&response_mode=form_post&nonce=638881404491827874.NzUzMzMwMGQtZWJhNi00MjYxLWJmYTYtMGZkMzdmMDVkODViZDEzYzdkNTUtZjFiZi00Zjg2LWEwOTAtZmQxMDE3YmNiODRi&ui_locales=en-US&mkt=en-US&client-request-id=aef0c282-9b1f-42c6-8a29-36bfdc4cbe5d&state=g5Gi4I_vYfyrZgCE1RNSXAlqggl6-x0mq-HIbq7V39JEVlJabY366DIPyZRmxTVwfZSHoPCkFjEOIOXkVlr5VK4XOausi0M58kY1P1d-pXjmkKj4KvbsjjkouERbQBj5PZ7AARgSSwt2OUOxZ-Qkakal2tEE0aBwJOVbTh6-KhG-aTwUvYzN217gZ3NCUNcb3zCxpEVUU1qrkepVZenYLBcvZREly5Ra0vnld_qaIrXI-EjmchtxHvtXt2nrNiTsQuMe040dFhMsQU9EsCDu_gH7bBHd_z-_2Gskz_DWxKk&x-client-SKU=ID_NET8_0&x-client-ver=8.5.0.0&sso_reload=true'

# Restart controls
RESTART_EVERY_SECONDS = 100      # Restart browser after this many seconds
RESTART_EVERY_EMAILS = 10       # Restart browser after this many emails
EMAIL_DELAY_RANGE = (1, 2)      # Delay per email (seconds, randomized between min/max)

def launch_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1200,800")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def save_result(email, result):
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(f"{email}: {result}\n")
    print(f"{email}: {result}")

def is_funky_state(driver):
    # Funky states are when something is wrong, e.g., CAPTCHA, error page, etc.
    page_source = driver.page_source.lower()
    if "enter the characters you see" in page_source or "verify your identity" in page_source:
        return "CAPTCHA or verification detected"
    if "unusual activity" in page_source or "help us protect your account" in page_source:
        return "Unusual activity / protection page"
    return None

def validate_emails():
    with open(EMAIL_FILE, "r", encoding="utf-8") as f:
        emails = [line.strip() for line in f if line.strip()]
    done = set()
    # Avoid duplicates in results file
    try:
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    done.add(line.split(":")[0].strip())
    except FileNotFoundError:
        pass

    total = len(emails)
    idx = 0
    while idx < total:
        driver = launch_browser()
        wait = WebDriverWait(driver, 15)
        session_start = time.time()
        emails_checked = 0

        while idx < total:
            email = emails[idx]
            idx += 1
            if email in done:
                continue

            # Time-based restart
            elapsed = time.time() - session_start
            if elapsed > RESTART_EVERY_SECONDS or emails_checked >= RESTART_EVERY_EMAILS:
                driver.quit()
                print("Restarting browser after", emails_checked, "emails or", int(elapsed), "seconds.")
                break

            try:
                driver.get(AUTH_URL)
                # Detect funky session states right away
                funky = is_funky_state(driver)
                if funky:
                    save_result(email, f"[ERROR] {funky} (browser restart)")
                    driver.quit()
                    print("Restarting browser due to:", funky)
                    break

                # Wait for email field and enter email
                email_input = wait.until(EC.presence_of_element_located((By.ID, "i0116")))
                email_input.clear()
                email_input.send_keys(email)
                # Click Next
                next_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
                next_btn.click()
            except Exception as e:
                save_result(email, f"[ERROR] {str(e)}")
                continue

            # Wait for redirect/result or funky state
            try:
                wait.until(lambda d: d.current_url != AUTH_URL or is_funky_state(d))
            except:
                save_result(email, "[TIMEOUT] No redirect/result.")
                continue

            current_url = driver.current_url
            page_source = driver.page_source

            funky = is_funky_state(driver)
            if funky:
                save_result(email, f"[ERROR] {funky} (browser restart)")
                driver.quit()
                print("Restarting browser due to:", funky)
                break

            if "login.live.com" in current_url:
                save_result(email, "[VALID/REDIRECT] Redirected to login.live.com (MSA att.net)")
            elif "Enter password" in page_source or "Forgot my password" in page_source:
                save_result(email, "[VALID/PASSWORD] Password prompt detected (AAD/Office365)")
            elif "account doesn't exist" in page_source or "We couldn't find an account" in page_source:
                save_result(email, "[INVALID] Not found.")
            else:
                save_result(email, f"[UNKNOWN] URL after Next: {current_url}")

            emails_checked += 1
            time.sleep(random.uniform(*EMAIL_DELAY_RANGE))

        driver.quit()

if __name__ == "__main__":
    print("Starting Microsoft email validator.")
    print(f"Restarting browser every {RESTART_EVERY_EMAILS} emails or {RESTART_EVERY_SECONDS} seconds.")
    print(f"Per-email delay randomized between {EMAIL_DELAY_RANGE[0]}–{EMAIL_DELAY_RANGE[1]} sec.")
    validate_emails()
    print("Done. All results saved to results.txt.")
