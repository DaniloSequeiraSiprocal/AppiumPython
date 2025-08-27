import unittest
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import (NoSuchElementException)
from selenium.webdriver.common.by import By

from capabilities_loader import load_capabilities


class SDKTests(unittest.TestCase):
    def setUp(self):
        self.caps = load_capabilities()

        try:
            options = UiAutomator2Options().load_capabilities(self.caps)
            self.driver = webdriver.Remote(
                command_executor="http://localhost:4723",
                options=options
            )
            self.driver.implicitly_wait(10)
        except Exception as e:
            self.fail(f"Error al inicializar el driver: {str(e)}")

    def tearDown(self):
        if self.driver:
            self.driver.quit()


    def test_text_extract(self):
        max_retries = 5
        retry_delay = 2  # segundos

        try:
            for attempt in range(max_retries):
                time.sleep(10)
                self.driver.find_element(By.ID, "amazonia.iu.com:id/button10").click()
                time.sleep(retry_delay)

                # Verificar el texto
                text_view_element = self.driver.find_element(By.ID, "amazonia.iu.com:id/textView")
                text = text_view_element.text.strip()

               # Extraer Client Id
                client_id_element = self.driver.find_element(By.ID, "amazonia.iu.com:id/deviceIdValue")
                client_id_text = client_id_element.text.strip()
                print(f"[Intento {attempt + 1}] Status del SDK: {text}, Client Id: {client_id_text}")


                if text == "REGISTERED" and client_id_text:
                    print("✔ Estado válido detectado y Client Id encontrado")
                    break
            else:
                self.fail("❌ No se obtuvo un estado válido o información de SDK después de varios intentos.")
        except NoSuchElementException:
            self.fail("No se encontró el elemento requerido.")


if __name__ == '__main__':
    unittest.main()
