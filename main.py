from appium import webdriver
from appium.options.android import UiAutomator2Options

caps = {
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:platformVersion": "12",
  "appium:deviceName": "Pixel_4",
  "appium:javaHome": "C:\\Program Files\\Microsoft\\jdk-11.0.27.6-hotspot",
  "appium:appPackage": "com.google.android.calculator",
  "appium:appActivity": "com.android.calculator2.Calculator"
}

options = UiAutomator2Options().load_capabilities(caps)

driver = webdriver.Remote('http://localhost:4723', options=options)

