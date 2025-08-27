from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.by import By
import time

caps = {
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:platformVersion": "13",
  "appium:deviceName": "M2012K10C",
  "appium:javaHome": "C:\\Program Files\\Microsoft\\jdk-11.0.27.6-hotspot",
  "appium:appPackage": "com.miui.calculator",
  "appium:appActivity": "com.miui.calculator.cal.CalculatorActivity"
}

options = UiAutomator2Options().load_capabilities(caps)
driver = webdriver.Remote('http://localhost:4723', options=options)

#procedimiento de suma
driver.find_element(By.XPATH, "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout").click()
time.sleep(1)
driver.find_element(By.ID, "com.miui.calculator:id/btn_8_s").click()
driver.find_element(By.ID, "com.miui.calculator:id/btn_plus_s").click()
driver.find_element(By.ID, "com.miui.calculator:id/btn_5_s").click()
driver.find_element(By.ID, "com.miui.calculator:id/btn_equal_s").click()