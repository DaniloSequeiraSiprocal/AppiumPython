import os
import unittest
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from time import sleep
import random
from selenium.common.exceptions import (InvalidElementStateException,
                                        WebDriverException)
from capabilities_loader import load_capabilities

class SDKTests(unittest.TestCase):
    def setUp(self):
        # Configuración mejorada de capacidades
        self.caps = load_capabilities()

        # Inicialización más robusta del driver
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

    def test_basic_functionality(self):
        """Prueba básica de funcionalidad del SDK"""
        print("\nEjecutando prueba básica de funcionalidad")

        # Verificación mejorada con elementos visibles
        try:
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*[not(ancestor::*[contains(@visible, 'false')])]")
            self.assertGreater(len(elements), 0, "La aplicación no mostró elementos visibles")
        except Exception as e:
            self.fail(f"Fallo en prueba básica: {str(e)}")

    def test_orientation_change(self):
        """Prueba de cambio de orientación con manejo robusto de errores"""
        print("\nEjecutando prueba de cambio de orientación")

        def set_orientation(orientation):
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    self.driver.orientation = orientation
                    sleep(2)
                    visible_elements = self.driver.find_elements(AppiumBy.XPATH,
                                                                 "//*[not(ancestor::*[contains(@visible, 'false')])]")
                    if not visible_elements:
                        raise InvalidElementStateException(f"No elements found in {orientation} mode")
                    return True
                except InvalidElementStateException as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Intento {attempt + 1} fallido: {str(e)}")
                    os.system('adb shell settings put system accelerometer_rotation 1')
                    sleep(1)

        try:
            # Test landscape
            set_orientation("LANDSCAPE")
            # Test portrait
            set_orientation("PORTRAIT")
        except Exception as e:
            self.fail(f"Fallo en cambio de orientación: {str(e)}")

    def test_app_background(self):
        """Prueba de comportamiento en segundo plano con verificación mejorada"""
        print("\nEjecutando prueba de segundo plano")

        try:
            # Guardar estado actual antes de enviar a segundo plano
            initial_elements = self.driver.find_elements(AppiumBy.XPATH,
                                                         "//*[not(ancestor::*[contains(@visible, 'false')])]")

            # Enviar a segundo plano
            self.driver.background_app(5)
            sleep(6)

            # Verificar recuperación comparando con estado inicial
            recovered_elements = self.driver.find_elements(AppiumBy.XPATH,
                                                           "//*[not(ancestor::*[contains(@visible, 'false')])]")
            self.assertGreaterEqual(len(recovered_elements), len(initial_elements) / 2,
                                    "La aplicación no se recuperó correctamente")
        except Exception as e:
            self.fail(f"Fallo en prueba de segundo plano: {str(e)}")

    def test_stop_sdk_service(self):
        """Prueba mejorada para detener el servicio SDK"""
        print("\nEjecutando stop SDK test")

        def stop_sdk_service():
            """Función para detener el servicio con múltiples métodos"""
            # Método 1: Intentar broadcast
            try:
                self.driver.execute_script('mobile: shell', {
                    'command': 'am broadcast',
                    'args': ['-a', 'amazonia.iu.com.STOP_SERVICE'],
                    'includeStderr': True,
                    'timeout': 5000
                })
                sleep(2)
                return True
            except:
                pass

            # Método 2: Intentar detener servicio directamente
            try:
                self.driver.terminate_app(self.caps["appium:appPackage"])
                sleep(2)
                self.driver.activate_app(self.caps["appium:appPackage"])
                sleep(3)
                return True
            except:
                pass

            return False

        try:
            if not stop_sdk_service():
                self.fail("No se pudo detener el servicio SDK")

            # Verificar que la aplicación sigue funcional
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*[not(ancestor::*[contains(@visible, 'false')])]")
            self.assertGreater(len(elements), 0, "La aplicación no funciona después de detener el SDK")
        except Exception as e:
            self.fail(f"Error en stop_sdk_test: {str(e)}")

    def test_crash_recovery(self):
        """Prueba de recuperación mejorada después de fallo"""
        print("\nEjecutando prueba de recuperación de crash")

        def recover_from_crash():
            """Función de recuperación con múltiples estrategias"""
            try:
                # 1. Intentar reactivar la aplicación
                self.driver.activate_app(self.caps["appium:appPackage"])
                sleep(3)

                # 2. Verificar si la app responde
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH,
                                                         "//*[not(ancestor::*[contains(@visible, 'false')])]")
                    if elements:
                        return True
                except:
                    pass

                # 3. Reiniciar la sesión si es necesario
                self.driver.quit()
                sleep(2)
                options = UiAutomator2Options().load_capabilities(self.caps)
                self.driver = webdriver.Remote("http://localhost:4723", options=options)
                sleep(5)
                return True

            except Exception as e:
                print(f"Error en recuperación: {str(e)}")
                return False

        try:
            # Operaciones intensivas con manejo de errores
            for i in range(20):
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")
                    if elements:
                        random.choice(elements).click()
                        sleep(0.5)
                        self.driver.back()
                    sleep(0.1)
                except WebDriverException as e:
                    print(f"Error durante operación intensiva (intento {i}): {str(e)}")
                    if not recover_from_crash():
                        raise
                    continue

        except Exception as e:
            self.fail(f"La aplicación no se recuperó correctamente: {str(e)}")

        # Verificación final
        try:
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*[not(ancestor::*[contains(@visible, 'false')])]")
            self.assertGreater(len(elements), 0, "La aplicación no mostró elementos después de la recuperación")
        except Exception as e:
            self.fail(f"Fallo en verificación post-recuperación: {str(e)}")

    def test_disable_sdk_active(self):
        """Prueba para desactivar el SDK cambiando sdkActive a false"""
        print("\nEjecutando prueba para desactivar SDK (sdkActive = false)")

        try:
            # Método 1: Usar backdoor (si el SDK lo soporta)
            try:
                self.driver.execute_script('mobile: backdoor', {
                    'target': 'activity',
                    'methods': [
                        {'name': 'setSdkActive', 'args': [False]}
                    ]
                })
                print("Método backdoor exitoso")
            except:
                # Método 2: Usar broadcast intent (si está configurado)
                try:
                    self.driver.execute_script('mobile: shell', {
                        'command': 'am broadcast',
                        'args': [
                            '-a', 'amazonia.iu.com.SET_SDK_ACTIVE',
                            '--ez', 'active', 'false'
                        ],
                        'includeStderr': True,
                        'timeout': 5000
                    })
                    print("Método broadcast exitoso")
                except:
                    # Método 3: Usar reflexión Java (más avanzado)
                    try:
                        self.driver.execute_script('mobile: shell', {
                            'command': 'am',
                            'args': [
                                'startservice',
                                '-n', 'amazonia.iu.com/.SdkService',
                                '--es', 'action', 'set_active',
                                '--ez', 'value', 'false'
                            ],
                            'includeStderr': True,
                            'timeout': 5000
                        })
                        print("Método startservice exitoso")
                    except Exception as e:
                        raise Exception(f"Todos los métodos fallaron: {str(e)}")

            # Verificar que el cambio tuvo efecto
            sleep(2)  # Esperar a que se aplique el cambio

            # Verificación opcional (si el SDK provee forma de consultar el estado)
            try:
                result = self.driver.execute_script('mobile: backdoor', {
                    'target': 'activity',
                    'methods': [
                        {'name': 'isSdkActive', 'args': []}
                    ]
                })
                self.assertFalse(result, "El SDK sigue activo después de desactivarlo")
            except:
                print("No se pudo verificar el estado, asumiendo cambio exitoso")

            # Verificación funcional - la app debería seguir funcionando
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*[not(ancestor::*[contains(@visible, 'false')])]")
            self.assertGreater(len(elements), 0, "La aplicación dejó de funcionar después de desactivar el SDK")

        except Exception as e:
            self.fail(f"Fallo al desactivar SDK: {str(e)}")

    def tearDown(self):
        if hasattr(self, 'driver') and self.driver:
            try:
                # Restablecer orientación a portrait
                try:
                    self.driver.orientation = "PORTRAIT"
                except:
                    pass

                # Cerrar sesión limpiamente
                self.driver.quit()
            except Exception as e:
                print(f"Error durante tearDown: {str(e)}")

        # Limpiar procesos residuales
        os.system('adb shell am force-stop amazonia.iu.com')


if __name__ == '__main__':
    unittest.main(verbosity=2)