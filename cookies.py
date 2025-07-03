from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://ebook.yourcloudlibrary.com/library/deBib/featured")

input("Log handmatig in en druk op Enter...")

cookies = driver.get_cookies()
for cookie in cookies:
    if cookie["name"] == "__config_PROD":
        print("__config_PROD =", cookie["value"])

driver.quit()
