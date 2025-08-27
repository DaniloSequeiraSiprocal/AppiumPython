import os
import unittest
import time  # Importación esencial
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import (InvalidElementStateException,
                                        WebDriverException,
                                        NoSuchElementException)


class SDKTests(unittest.TestCase):
    def setUp(self):
        # Configuración de capacidades
        self.caps = {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "appium:platformVersion": "12",
            "appium:deviceName": "Pixel_4",
            "appium:appPackage": "amazonia.iu.com",
            "appium:appActivity": "amazonia.iu.com.MainActivity",
            "appium:noReset": False,
            "appium:autoGrantPermissions": True,
            "appium:uiautomator2ServerLaunchTimeout": 60000,
            "appium:uiautomator2ServerInstallTimeout": 60000,
            "appium:adbExecTimeout": 60000
        }

        # Inicialización del driver
        self.driver = None
        try:
            options = UiAutomator2Options().load_capabilities(self.caps)
            self.driver = webdriver.Remote(
                command_executor="http://localhost:4723",
                options=options
            )
            self.driver.implicitly_wait(10)
        except Exception as e:
            self.fail(f"Error al inicializar el driver: {str(e)}")

    def get_sdk_status(self):
        """Consulta el estado del SDK usando el método GET_STATUS"""
        print("\nConsultando estado del SDK...")

        try:
            # 1. Preparar el intent para consultar el estado
            status = self.driver.execute_script('mobile: shell', {
                'command': 'am broadcast',
                'args': [
                    '-a', 'amazonia.iu.com.GET_STATUS',
                    '--es', 'reply_pkg', 'amazonia.iu.com'  # Paquete que recibirá la respuesta
                ],
                'includeStderr': True,
                'timeout': 10000  # 10 segundos de timeout
            })

            # 2. Analizar la respuesta
            if 'Broadcast completed' in status.get('stdout', ''):
                print("Solicitud de estado enviada correctamente")

                # 3. Verificar el estado mediante diferentes métodos
                return self._verify_sdk_status_response()
            else:
                print("Error al enviar solicitud de estado")
                return None

        except Exception as e:
            print(f"Error al consultar estado del SDK: {str(e)}")
            return None

    def _verify_sdk_status_response(self):
        """Verifica la respuesta del estado del SDK usando múltiples métodos"""
        # Método 1: Verificar logs de la aplicación
        status_from_logs = self._get_status_from_logs()
        if status_from_logs is not None:
            return status_from_logs

        # Método 2: Verificar cambios en la UI
        status_from_ui = self._get_status_from_ui()
        if status_from_ui is not None:
            return status_from_ui

        # Método 3: Verificar comportamiento específico
        return self._get_status_from_behavior()

    def _get_status_from_logs(self):
        """Intenta obtener el estado del SDK desde los logs"""
        try:
            logs = self.driver.get_log('logcat')
            for entry in reversed(logs[-50:]):  # Revisar los últimos 50 logs
                if 'SDK Status:' in entry['message']:
                    return 'active' in entry['message'].lower()
            return None
        except:
            return None

    def _get_status_from_ui(self):
        """Intenta determinar el estado del SDK mediante elementos UI"""
        try:
            # Buscar indicadores visuales del estado del SDK
            active_indicators = [
                "//*[contains(@resource-id, 'sdk_active')]",
                "//*[contains(@text, 'SDK: ON')]"
            ]

            inactive_indicators = [
                "//*[contains(@resource-id, 'sdk_inactive')]",
                "//*[contains(@text, 'SDK: OFF')]"
            ]

            for indicator in active_indicators:
                if self.driver.find_elements(AppiumBy.XPATH, indicator):
                    return True

            for indicator in inactive_indicators:
                if self.driver.find_elements(AppiumBy.XPATH, indicator):
                    return False

            return None
        except:
            return None

    def _get_status_from_behavior(self):
        """Determina el estado del SDK mediante su comportamiento"""
        try:
            # Intentar operación que solo funciona con SDK activo
            self.driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'Status')]").click()
            time.sleep(1)
            return True
        except:
            return False

    def test_sdk_lifecycle(self):
        """Prueba mejorada del ciclo de vida del SDK"""
        print("\n=== Prueba de ciclo de vida del SDK ===")

        try:
            # 1. Detección inicial del estado del SDK
            initial_state = self._detect_sdk_state()
            print(f"Estado inicial detectado: {'ACTIVO' if initial_state else 'INACTIVO'}")

            # 2. Cambio de estado mediante interacciones seguras
            if initial_state:
                print("Intentando desactivar SDK...")
                self._safe_change_sdk_state(activate=False)
                self.assertFalse(self._wait_for_sdk_state(False, 15),
                                 "El SDK no se desactivó correctamente")

            # 3. Activación manual con verificación
            print("Intentando activar SDK...")
            self._safe_change_sdk_state(activate=True)
            self.assertTrue(self._wait_for_sdk_state(True, 30),
                            "El SDK no se activó en el tiempo esperado")

            print("¡Prueba completada con éxito!")

        except Exception as e:
            self.fail(f"Fallo en la prueba: {str(e)}")

    def _detect_sdk_state(self):
        """Detección robusta del estado del SDK"""
        # Método 1: Buscar elementos UI específicos con múltiples intentos
        sdk_indicators = [
            "//*[contains(@resource-id, 'sdk')]",
            "//*[contains(@text, 'SDK')]",
            "//*[contains(@content-desc, 'sdk')]"
        ]

        for _ in range(3):  # 3 intentos
            for indicator in sdk_indicators:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, indicator)
                    if elements and elements[0].is_displayed():
                        return True
                except:
                    continue
            time.sleep(2)

        # Método 2: Verificar comportamiento específico
        try:
            # Ejemplo: Intentar una acción que solo funciona con SDK activo
            self.driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'Inicio')]").click()
            time.sleep(1)
            return True
        except:
            return False

    def _safe_change_sdk_state(self, activate=True):
        """Cambia el estado del SDK de manera segura"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Navegación genérica a configuración
                menu_buttons = self.driver.find_elements(AppiumBy.XPATH,
                                                         "//*[contains(@content-desc, 'Menú') or contains(@text, 'Menú')]")
                if menu_buttons:
                    menu_buttons[0].click()
                    time.sleep(2)

                    # Buscar opción de configuración
                    settings = self.driver.find_elements(AppiumBy.XPATH,
                                                         "//*[contains(@text, 'Configuración') or contains(@content-desc, 'Configuración')]")
                    if settings:
                        settings[0].click()
                        time.sleep(2)

                        # Buscar toggle del SDK
                        sdk_toggles = self.driver.find_elements(AppiumBy.XPATH,
                                                                "//*[contains(@text, 'SDK')]/following-sibling::*[1]//Switch")
                        if sdk_toggles:
                            current_state = 'ON' in sdk_toggles[0].text
                            if (activate and not current_state) or (not activate and current_state):
                                sdk_toggles[0].click()
                                time.sleep(3)
                                return
                # Si no se encontraron elementos, intentar método alternativo
                self._alternative_sdk_state_change(activate)
                return
            except Exception as e:
                print(f"Intento {attempt + 1} fallido: {str(e)}")
                if attempt == max_attempts - 1:
                    raise Exception(f"No se pudo cambiar el estado del SDK después de {max_attempts} intentos")
                time.sleep(2)

    def _alternative_sdk_state_change(self, activate):
        """Método alternativo para cambiar el estado del SDK"""
        # Intenta navegar directamente a la pantalla de SDK
        self.driver.press_keycode(4)  # KEYCODE_BACK
        time.sleep(1)

        # Intenta abrir el menú de SDK con combinación de teclas (si está disponible)
        self.driver.press_keycode(82)  # KEYCODE_MENU
        time.sleep(1)

        # Busca elementos alternativos
        try:
            sdk_options = self.driver.find_elements(AppiumBy.XPATH, "//*[contains(@text, 'SDK')]")
            if sdk_options:
                sdk_options[0].click()
                time.sleep(2)

                toggle = self.driver.find_element(AppiumBy.XPATH, "//Switch")
                if (activate and 'OFF' in toggle.text) or (not activate and 'ON' in toggle.text):
                    toggle.click()
                    time.sleep(3)
        except:
            pass

    def _wait_for_sdk_state(self, desired_state, timeout):
        """Espera hasta que el SDK alcance el estado deseado"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_state = self._detect_sdk_state()
            if current_state == desired_state:
                return True
            print(f"Esperando... Estado actual: {'ACTIVO' if current_state else 'INACTIVO'}")
            time.sleep(3)
        return False


if __name__ == '__main__':
    unittest.main(verbosity=2)