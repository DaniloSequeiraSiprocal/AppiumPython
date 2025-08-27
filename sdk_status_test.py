import unittest
import time  # Importación esencial
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from capabilities_loader import load_capabilities


class SDKTests(unittest.TestCase):
    def setUp(self):
        # Configuración de capacidades
        self.caps = load_capabilities()

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
        """
        Consulta el estado del SDK cuando el BroadcastReceiver tiene exported=true.
        Permite enviar broadcasts directamente sin necesidad de root.
        """
        print("\nConsultando estado del SDK (broadcast directo)...")

        try:
            # Enviar el broadcast para obtener el estado
            response = self.driver.execute_script('mobile: shell', {
                'command': 'am',
                'args': [
                    'broadcast',
                    '-n', 'amazonia.iu.com/.receivers.CommandReceiver',  # receptor explícito
                    '-a', 'com.iu.diagnostics.request',                 # acción correcta
                    '--es', 'reply_pkg', 'amazonia.iu.com'
                ],
                'includeStderr': True,
                'timeout': 10000
            })


            stdout = response.get('stdout', '')
            stderr = response.get('stderr', '')

            if 'Broadcast completed' in stdout:
                print("Broadcast enviado correctamente.")

                # Aquí analizas la respuesta según la implementación del SDK
                logs = self.driver.get_log('logcat')
                for entry in reversed(logs[-50:]):  # Últimos 50 logs
                    if 'SDK Status:' in entry['message']:
                        detected = 'active' in entry['message'].lower()
                        print(f"Estado detectado: {'ACTIVO' if detected else 'INACTIVO'}")
                        return detected

                # Si el SDK envía un extra como broadcast (ejemplo)
                if 'SDK_ACTIVE' in stdout.upper():
                    return True
                elif 'SDK_INACTIVE' in stdout.upper():
                    return False

                print("No se encontró información del estado en la respuesta del broadcast.")
                return None
            else:
                print(f"Error al enviar broadcast: {stderr or stdout}")
                return None

        except Exception as e:
            print(f"Error al consultar estado del SDK: {str(e)}")
            return None

    def _detect_sdk_status_by_ui(self):
        """Detección por elementos visuales en la interfaz"""
        max_retries = 5
        retry_delay = 2  # segundos

        try:
            for attempt in range(max_retries):
                time.sleep(10)
                try:
                    # Intentar hacer clic en el botón
                    self.driver.find_element(By.ID, "amazonia.iu.com:id/button10").click()
                except NoSuchElementException:
                    print(f"[Intento {attempt + 1}] Botón no encontrado")
                    continue

                time.sleep(retry_delay)

                try:
                    # Verificar el texto
                    text_view_element = self.driver.find_element(By.ID, "amazonia.iu.com:id/textView")
                    text = text_view_element.text.strip()

                    # Extraer Client Id
                    client_id_element = self.driver.find_element(By.ID, "amazonia.iu.com:id/deviceIdValue")
                    client_id_text = client_id_element.text.strip()

                    print(f"[Intento {attempt + 1}] Status del SDK: {text}, Client Id: {client_id_text}")

                    if text == "REGISTERED" and client_id_text:
                        print("✔ Estado válido detectado y Client Id encontrado")
                        return True  # SDK activo
                except NoSuchElementException:
                    print(f"[Intento {attempt + 1}] Elementos de texto no encontrados")
                    continue

            print("❌ No se obtuvo un estado válido o información de SDK después de varios intentos.")
            return False  # SDK inactivo

        except Exception as e:
            print(f"Error durante la detección de SDK: {str(e)}")
            return None

    def _detect_sdk_status_by_behavior(self):
        """Detección por comportamiento característico"""
        try:
            # Prueba 1: Intentar operación que solo funciona con SDK activo
            try:
                self.driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'Función SDK')]").click()
                time.sleep(1)
                return True
            except:
                pass

            # Prueba 2: Verificar tiempo de respuesta
            start_time = time.time()
            self.driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'Inicio')]").click()
            response_time = time.time() - start_time

            # SDK activo generalmente añade un pequeño retraso
            if response_time > 1.5:  # Umbral en segundos
                return True
            return False

        except:
            return None

    def _detect_sdk_status_by_logs(self):
        """Detección por logs de la aplicación (si son accesibles)"""
        try:
            logs = self.driver.get_log('logcat')
            for entry in logs[-20:]:  # Últimos 20 logs
                if 'SDK State' in entry['message']:
                    return 'active' in entry['message'].lower()
            return None
        except:
            return None

    def _detect_sdk_status_by_performance(self):
        """Detección por métricas de rendimiento (opcional)"""
        try:
            # Obtener uso de CPU de la aplicación
            cpu_usage = self.driver.get_performance_data(
                'amazonia.iu.com',
                'cpuinfo',
                5
            )
            # SDK activo generalmente consume más CPU
            if float(cpu_usage[-1][0]) > 10.0:  # 10% de uso
                return True
            return False
        except:
            return None
