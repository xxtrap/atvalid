from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# CONFIG
EMAIL_FILE = 'emails.txt'
AUTH_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=4765445b-32c6-49b0-83e6-1d93765276ca&redirect_uri=https%3A%2F%2Fwww.office.com%2Flandingv2&response_type=code%20id_token&scope=openid%20profile%20https%3A%2F%2Fwww.office.com%2Fv2%2FOfficeHome.All&response_mode=form_post&nonce=638881404491827874.NzUzMzMwMGQtZWJhNi00MjYxLWJmYTYtMGZkMzdmMDVkODViZDEzYzdkNTUtZjFiZi00Zjg2LWEwOTAtZmQxMDE3YmNiODRi&ui_locales=en-US&mkt=en-US&client-request-id=aef0c282-9b1f-42c6-8a29-36bfdc4cbe5d&state=g5Gi4I_vYfyrZgCE1RNSXAlqggl6-x0mq-HIbq7V39JEVlJabY366DIPyZRmxTVwfZSHoPCkFjEOIOXkVlr5VK4XOausi0M58kY1P1d-pXjmkKj4KvbsjjkouERbQBj5PZ7AARgSSwt2OUOxZ-Qkakal2tEE0aBwJOVbTh6-KhG-aTwUvYzN217gZ3NCUNcb3zCxpEVUU1qrkepVZenYLBcvZREly5Ra0vnld_qaIrXI-EjmchtxHvtXt2nrNiTsQuMe040dFhMsQU9EsCDu_gH7bBHd_z-_2Gskz_DWxKk&x-client-SKU=ID_NET8_0&x-client-ver=8.5.0.0&sso_reload=true'

# Read emails from file
with open(EMAIL_FILE, 'r') as f:
    emails = [line.strip() for line in f if line.strip()]

# Chrome options for headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1200,800")
chrome_options.add_argument("--log-level=3")  # Suppress warnings

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)

for email in emails:
    driver.get(AUTH_URL)

    # Wait for the email field and enter email
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "i0116")))
        email_input.clear()
        email_input.send_keys(email)
    except Exception as e:
        print(f"[ERROR] {email}: Email input not found.")
        continue

    # Click Next
    try:
        next_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
        next_btn.click()
    except Exception as e:
        print(f"[ERROR] {email}: Next button not found.")
        continue

    # Wait for redirect or result
    try:
        wait.until(lambda d: d.current_url != AUTH_URL)
    except:
        print(f"[TIMEOUT] {email}: No redirect.")
        continue

    # Detect outcome
    current_url = driver.current_url
    page_source = driver.page_source

    if "login.live.com" in current_url:
        print(f"[VALID/REDIRECT] {email}: Redirected to login.live.com (MSA att.net)")
    elif "Enter password" in page_source or "Forgot my password" in page_source:
        print(f"[VALID/PASSWORD] {email}: Password prompt detected (AAD/Office365)")
    elif "account doesn't exist" in page_source or "We couldn't find an account" in page_source:
        print(f"[INVALID] {email}: Not found.")
    else:
        print(f"[UNKNOWN] {email}: URL after Next: {current_url}")

driver.quit()

