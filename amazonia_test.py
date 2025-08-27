import unittest
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from time import sleep


class SystemEventsSDKTests(unittest.TestCase):
    def setUp(self):
        # Configuración de las capacidades
        self.caps = {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "appium:platformVersion": "12",
            "appium:deviceName": "Pixel_4",
            "appium:appPackage": "amazonia.iu.com",
            "appium:appActivity": "amazonia.iu.com.MainActivity",
            "appium:noReset": False,
            "appium:autoGrantPermissions": True
        }

        # Convertir las capacidades a Opciones de UiAutomator2
        options = UiAutomator2Options().load_capabilities(self.caps)

        # Inicializar el driver de Appium con las opciones
        self.driver = webdriver.Remote(command_executor="http://localhost:4723",options=options)
        self.driver.implicitly_wait(10)

    def test_orientation_change(self):
        """Test para validar el cambio de orientación del dispositivo"""
        print("\nEjecutando prueba de cambio de orientación")

        # Obtener orientación actual
        current_orientation = self.driver.orientation
        print(f"Orientación actual: {current_orientation}")

        # Cambiar a landscape si no lo está
        if current_orientation != "LANDSCAPE":
            self.driver.orientation = "LANDSCAPE"
            sleep(2)  # Esperar a que la aplicación se adapte
            print("Cambiado a modo landscape")

            # Verificar que la aplicación sigue funcionando
            self.assertTrue(self.driver.find_elements(AppiumBy.XPATH, "//*"),
                            "La aplicación no muestra elementos en landscape")

        # Volver a portrait
        self.driver.orientation = "PORTRAIT"
        sleep(2)
        print("Vuelto a modo portrait")

        # Verificar que la aplicación sigue funcionando
        self.assertTrue(self.driver.find_elements(AppiumBy.XPATH, "//*"),
                        "La aplicación no muestra elementos en portrait")

    def test_app_background_foreground(self):
        """Test para validar el comportamiento cuando la app va a segundo plano y vuelve"""
        print("\nEjecutando prueba de background/foreground")

        # Ir a home (background)
        self.driver.press_keycode(3)  # Código para botón home
        sleep(3)
        print("Aplicación enviada a segundo plano")

        # Volver a la aplicación
        self.driver.activate_app("amazonia.iu.com")
        sleep(2)
        print("Aplicación traída a primer plano")

        # Verificar que la aplicación sigue funcionando
        self.assertTrue(self.driver.find_elements(AppiumBy.XPATH, "//*"),
                        "La aplicación no se recuperó correctamente")

    def test_notification_interruption(self):
        """Test para validar el comportamiento con notificaciones"""
        print("\nEjecutando prueba de interrupción por notificación")

        # Abrir el panel de notificaciones
        self.driver.open_notifications()
        sleep(2)
        print("Panel de notificaciones abierto")

        # Cerrar el panel de notificaciones
        self.driver.press_keycode(4)  # Código para botón back
        sleep(2)
        print("Panel de notificaciones cerrado")

        # Verificar que la aplicación sigue funcionando
        self.assertTrue(self.driver.find_elements(AppiumBy.XPATH, "//*"),
                        "La aplicación no se recuperó después de notificaciones")

    def test_permissions_handling(self):
        """Test para verificar el autoGrantPermissions"""
        print("\nEjecutando prueba de manejo de permisos")

        # Verificar que la aplicación tiene permisos necesarios
        # (autoGrantPermissions=True debería haber concedido los permisos)
        from appium.webdriver.common.appiumby import AppiumBy
        try:
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*")
            self.assertTrue(len(elements) > 0,
                            "La aplicación no muestra contenido después de conceder permisos")
            print("Manejo de permisos verificado correctamente")
        except Exception as e:
            self.fail(f"Fallo en verificación de permisos: {str(e)}")

    def tearDown(self):
        # Restaurar configuración y cerrar la aplicación
        if hasattr(self, 'driver'):
            self.driver.orientation = "PORTRAIT"
            self.driver.quit()


if __name__ == '__main__':
    unittest.main(verbosity=2)