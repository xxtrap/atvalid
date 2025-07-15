import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

EMAIL_FILE = "emails.txt"
VALID_FILE = "valid.txt"
BATCH_SIZE = 100        # Emails before restarting browser
MAX_BATCH_SECONDS = 10 # Max seconds before restarting browser
MIN_DELAY = 1
MAX_DELAY = 2

AUTH_URL = (
    'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=4765445b-32c6-49b0-83e6-1d93765276ca'
    '&redirect_uri=https%3A%2F%2Fwww.office.com%2Flandingv2'
    '&response_type=code%20id_token'
    '&scope=openid%20profile%20https%3A%2F%2Fwww.office.com%2Fv2%2FOfficeHome.All'
    '&response_mode=form_post'
    '&nonce=638881404491827874.NzUzMzMwMGQtZWJhNi00MjYxLWJmYTYtMGZkMzdmMDVkODViZDEzYzdkNTUtZjFiZi00Zjg2LWEwOTAtZmQxMDE3YmNiODRi'
    '&ui_locales=en-US&mkt=en-US'
    '&client-request-id=aef0c282-9b1f-42c6-8a29-36bfdc4cbe5d'
    '&state=g5Gi4I_vYfyrZgCE1RNSXAlqggl6-x0mq-HIbq7V39JEVlJabY366DIPyZRmxTVwfZSHoPCkFjEOIOXkVlr5VK4XOausi0M58kY1P1d-pXjmkKj4KvbsjjkouERbQBj5PZ7AARgSSwt2OUOxZ-Qkakal2tEE0aBwJOVbTh6-KhG-aTwUvYzN217gZ3NCUNcb3zCxpEVUU1qrkepVZenYLBcvZREly5Ra0vnld_qaIrXI-EjmchtxHvtXt2nrNiTsQuMe040dFhMsQU9EsCDu_gH7bBHd_z-_2Gskz_DWxKk'
    '&x-client-SKU=ID_NET8_0&x-client-ver=8.5.0.0&sso_reload=true'
)

def start_driver():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--window-size=1200,800")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # You can try comment out headless if you want to debug visually
    driver = uc.Chrome(options=options)
    return driver

def validate_emails(emails):
    valid_count = 0
    total = len(emails)
    print("Starting Microsoft email validator.")
    print(f"Restarting browser every {BATCH_SIZE} emails or {MAX_BATCH_SECONDS} seconds.")
    print(f"Per-email delay randomized between {MIN_DELAY}–{MAX_DELAY} sec.\n")
    batch_start_time = time.time()
    driver = start_driver()
    wait = WebDriverWait(driver, 15)
    for idx, email in enumerate(emails, 1):
        try:
            driver.get(AUTH_URL)
            email_input = wait.until(EC.presence_of_element_located((By.ID, "i0116")))
            email_input.clear()
            email_input.send_keys(email)
            next_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
            next_btn.click()

            # Wait for either URL change or error message
            try:
                wait.until(lambda d: d.current_url != AUTH_URL or "We couldn't find an account" in d.page_source)
            except:
                pass

            current_url = driver.current_url
            page_source = driver.page_source

            # Result detection
            if "login.live.com" in current_url:
                result = "[VALID/REDIRECT] Redirected to login.live.com (MSA att.net)"
                print(f"{email}: {result}")
                with open(VALID_FILE, "a") as vf:
                    vf.write(email + "\n")
                valid_count += 1
            elif "Enter password" in page_source or "Forgot my password" in page_source:
                result = "[VALID/PASSWORD] Password prompt detected (AAD/Office365)"
                print(f"{email}: {result}")
                with open(VALID_FILE, "a") as vf:
                    vf.write(email + "\n")
                valid_count += 1
            elif "account doesn't exist" in page_source or "We couldn't find an account" in page_source:
                result = "[INVALID] Not found."
                print(f"{email}: {result}")
            else:
                result = "[UNKNOWN] URL after Next: " + current_url
                print(f"{email}: {result}")

        except Exception as e:
            print(f"[ERROR] {email}: {str(e)}")

        # Wait a randomized delay between each check
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)

        # Restart browser every BATCH_SIZE emails or MAX_BATCH_SECONDS seconds
        if idx % BATCH_SIZE == 0 or (time.time() - batch_start_time > MAX_BATCH_SECONDS):
            try:
                driver.quit()
            except Exception:
                pass
            time.sleep(1)
            driver = start_driver()
            wait = WebDriverWait(driver, 15)
            batch_start_time = time.time()

    try:
        driver.quit()
    except Exception:
        pass

    print(f"\nDone. {valid_count} valid emails saved to {VALID_FILE}")

if __name__ == "__main__":
    # Load emails from file
    with open(EMAIL_FILE, "r") as f:
        emails = [line.strip() for line in f if line.strip()]
    validate_emails(emails)
