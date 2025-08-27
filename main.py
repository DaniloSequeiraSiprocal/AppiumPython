import unittest
import time
import os
import subprocess
from datetime import datetime
from appium import webdriver
from appium.options.android import UiAutomator2Options
from capabilities_loader import load_capabilities

REPORTS_DIR = "receiver_test_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

class CommandReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Cargar capabilities del perfil específico
        cls.caps = load_capabilities()
        cls.driver = None

        # Obtener el appPackage directamente de las capabilities cargadas
        cls.app_package = cls.caps.get('appium:appPackage') or cls.caps.get('appPackage')
        if not cls.app_package:
            raise ValueError("No se encontró appPackage en las capabilities")

        try:
            # Configurar capabilities
            options = UiAutomator2Options().load_capabilities(cls.caps)

            cls.driver = webdriver.Remote(
                command_executor="http://localhost:4723",
                options=options
            )
            cls.driver.implicitly_wait(10)
            print(f"Driver inicializado correctamente para package: {cls.app_package}")
        except Exception as e:
            raise Exception(f"Error al inicializar el driver: {str(e)}")

        cls.test_results = []
        cls.detailed_reports = {}  # Diccionario para reportes detallados

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()
            print("Driver cerrado")
        cls.generate_html_report()

    def save_report(self, test_name, content):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(REPORTS_DIR, f"{test_name}_{timestamp}.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"Test: {test_name}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write("="*50 + "\n")
            f.write(content)
            if not content.strip():
                f.write("(El comando no devolvio output)")
        return report_file

    def save_detailed_report(self, test_name, section_name, content):
        """Guarda un reporte detallado por sección"""
        if test_name not in self.detailed_reports:
            self.detailed_reports[test_name] = {}

        self.detailed_reports[test_name][section_name] = content
        return f"{test_name}_{section_name}"

    @classmethod
    def generate_html_report(cls):
        html_file = os.path.join(REPORTS_DIR, "receiver_test_summary.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Receiver Test Summary</title>")
            f.write("<style>table {border-collapse: collapse; width: 100%;} ")
            f.write("th, td {border: 1px solid #ddd; padding: 8px; text-align: left;} ")
            f.write("tr:nth-child(even){background-color: #f2f2f2} ")
            f.write("th {background-color: #4CAF50; color: white;} ")
            f.write(".PASS {color: green;} .FAIL {color: red;} .SKIP {color: orange;}")
            f.write(".details {background-color: #f9f9f9; padding: 10px; margin: 5px; border: 1px solid #ddd;}</style></head>")
            f.write("<body><h2>Resumen de Pruebas CommandReceiver</h2>")
            f.write(f"<p><strong>App Package:</strong> {cls.app_package}</p>")

            # Tabla principal de resultados
            f.write("<table><tr><th>Test Name</th><th>Status</th><th>Message/Error</th><th>Log File</th></tr>")

            for result in cls.test_results:
                status_class = result['status']
                f.write(f"<tr><td>{result['name']}</td>")
                f.write(f"<td class='{status_class}'>{status_class}</td>")
                f.write(f"<td>{result['message'][:100]}{'...' if len(result['message']) > 100 else ''}</td>")
                if result['log_file']:
                    f.write(f"<td><a href='{os.path.basename(result['log_file'])}'>Ver Log</a></td></tr>")
                else:
                    f.write("<td>N/A</td></tr>")

            f.write("</table>")

            # Sección de reportes detallados
            f.write("<h2>Reportes Detallados</h2>")
            for test_name, sections in cls.detailed_reports.items():
                f.write(f"<h3>Test: {test_name}</h3>")
                for section_name, content in sections.items():
                    f.write(f"<div class='details'>")
                    f.write(f"<h4>{section_name}</h4>")
                    f.write(f"<pre>{content}</pre>")
                    f.write("</div>")

            f.write("</body></html>")
        print(f"[INFO] Resumen HTML generado: {html_file}")

    def run_adb_command(self, command, timeout=30):
        """Ejecuta comandos ADB usando subprocess directamente con codificación UTF-8"""
        try:
            print(f"Ejecutando comando: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            print(f"Resultado: '{output.strip()}'")
            return output
        except subprocess.TimeoutExpired:
            return "ERROR: Timeout ejecutando el comando"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def run_dumpsys_command(self, command_suffix, timeout=60):
        """Ejecuta comandos dumpsys con manejo especial de codificación"""
        try:
            command = f"adb shell dumpsys {command_suffix}"
            print(f"Ejecutando comando dumpsys: {command}")

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                output = stdout.decode('utf-8', errors='ignore')
                if process.returncode != 0:
                    error_output = stderr.decode('utf-8', errors='ignore')
                    return f"ERROR: {error_output}"

                print(f"Comando dumpsys completado, longitud output: {len(output)} caracteres")
                return output

            except subprocess.TimeoutExpired:
                process.kill()
                return "ERROR: Timeout ejecutando el comando dumpsys"

        except Exception as e:
            return f"ERROR: {str(e)}"

    def run_test_with_report(self, test_name, test_func):
        """Ejecuta una prueba y captura el resultado"""
        try:
            test_func()
            status = "PASS"
            message = "Exito - Ver reporte detallado para más informacion"
        except AssertionError as e:
            status = "FAIL"
            message = f"AssertionError: {str(e)}"
        except Exception as e:
            status = "FAIL"
            message = f"Exception: {str(e)}"

        self.test_results.append({
            "name": test_name,
            "status": status,
            "message": message,
            "log_file": getattr(self, "last_log_file", "")
        })

        if status == "FAIL":
            self.fail(f"{test_name} fallo: {message}")

    # ---------- Test 1: Broadcast válido ----------
    def test_send_valid_broadcast(self):
        def func():
            report_content = []
            report_content.append("=== TEST: BROADCAST VALIDO ===")
            report_content.append(f"Timestamp: {datetime.now()}")
            report_content.append("")

            output = self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez flag true")
            report_content.append("Comando ejecutado: adb shell am broadcast -a com.iu.diagnostics.request --ez flag true")
            report_content.append(f"Output: {output}")
            report_content.append("")

            error_indicators = ["Exception", "Error", "Failure", "not found"]
            has_errors = any(indicator in output for indicator in error_indicators)

            report_content.append("Análisis de errores:")
            for indicator in error_indicators:
                found = indicator in output
                report_content.append(f"  {indicator}: {'ENCONTRADO' if found else 'No encontrado'}")

            report_content.append(f"¿Tiene errores?: {'SI' if has_errors else 'NO'}")

            full_report = "\n".join(report_content)
            self.last_log_file = self.save_report("send_valid_broadcast", full_report)
            self.save_detailed_report("send_valid_broadcast", "analisis_completo", full_report)

            self.assertFalse(has_errors, f"El broadcast fallo: {output}")
        self.run_test_with_report("send_valid_broadcast", func)

    # ---------- Test 2: Broadcast inválido ----------
    def test_send_invalid_broadcast(self):
        def func():
            report_content = []
            report_content.append("=== TEST: BROADCAST INVALIDO ===")
            report_content.append(f"Timestamp: {datetime.now()}")
            report_content.append("")

            output = self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez invalidFlag notABoolean")
            report_content.append("Comando ejecutado: adb shell am broadcast -a com.iu.diagnostics.request --ez invalidFlag notABoolean")
            report_content.append(f"Output: {output}")
            report_content.append("")

            # Verificar que no cause crash de AndroidRuntime
            has_android_runtime = "AndroidRuntime" in output
            report_content.append(f"¿Contiene 'AndroidRuntime'?: {'SI' if has_android_runtime else 'NO'}")

            # Análisis adicional
            error_patterns = ["Exception", "Error", "Failure", "crash", "failed"]
            report_content.append("Analisis de patrones de error:")
            for pattern in error_patterns:
                found = pattern in output
                report_content.append(f"  {pattern}: {'ENCONTRADO' if found else 'No encontrado'}")

            full_report = "\n".join(report_content)
            self.last_log_file = self.save_report("send_invalid_broadcast", full_report)
            self.save_detailed_report("send_invalid_broadcast", "analisis_completo", full_report)

            self.assertNotIn("AndroidRuntime", output, "El broadcast invalido provoco un crash de la aplicacion")
        self.run_test_with_report("send_invalid_broadcast", func)

    # ---------- Test 3: Logcat del receiver ----------
    def test_logcat_for_receiver(self):
        def func():
            report_content = []
            report_content.append("=== TEST: LOGCAT DEL RECEIVER ===")
            report_content.append(f"Timestamp: {datetime.now()}")
            report_content.append("")

            # Limpiar logcat
            report_content.append("1. Limpiando logcat...")
            clear_output = self.run_adb_command("adb logcat -c")
            report_content.append(f"Resultado limpieza: {clear_output}")
            report_content.append("")

            # Enviar broadcast
            report_content.append("2. Enviando broadcast...")
            broadcast_output = self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez flag true")
            report_content.append(f"Resultado broadcast: {broadcast_output}")
            report_content.append("")

            time.sleep(3)

            # Obtener logs
            report_content.append("3. Obteniendo logs...")
            log_output = self.run_adb_command("adb logcat -d -s ActivityManager:I BroadcastQueue:I *:S")
            report_content.append(f"Logs obtenidos (longitud: {len(log_output)} caracteres):")
            report_content.append(log_output)
            report_content.append("")

            # Análisis de logs
            report_content.append("4. Analisis de logs:")
            has_activity = len(log_output.strip()) > 0
            report_content.append(f"¿Logs con actividad?: {'SI' if has_activity else 'NO'}")

            # Buscar patrones específicos
            patterns = ["com.iu.diagnostics", "deliverTo", "receive", "broadcast", self.app_package]
            report_content.append("Búsqueda de patrones específicos:")
            for pattern in patterns:
                found = pattern in log_output
                report_content.append(f"  {pattern}: {'ENCONTRADO' if found else 'No encontrado'}")

            full_report = "\n".join(report_content)
            self.last_log_file = self.save_report("logcat_receiver", full_report)
            self.save_detailed_report("logcat_receiver", "analisis_completo", full_report)

            self.assertTrue(has_activity, "No se registró actividad del receiver en logcat")
        self.run_test_with_report("logcat_receiver", func)

    # ---------- Test 4: Verificaciones alternativas del receiver ----------
    def test_alternative_receiver_verifications(self):
        def func():
            report_content = []
            report_content.append("=== VERIFICACIONES ALTERNATIVAS DEL RECEIVER ===")
            report_content.append(f"Timestamp: {datetime.now()}")
            report_content.append(f"Package: {self.app_package}")
            report_content.append("")

            # 1. Verificar AndroidManifest
            report_content.append("1. VERIFICACION DEL ANDROIDMANIFEST")
            report_content.append("=" * 50)

            try:
                app_path_result = self.run_adb_command(f"adb shell pm path {self.app_package}")
                app_path = app_path_result.strip().replace('package:', '')
                report_content.append(f"Path de la app: {app_path}")
                report_content.append("")

                if app_path and not app_path.startswith("ERROR"):
                    # Análisis con aapt
                    aapt_result = self.run_adb_command(f"adb shell aapt dump xmltree {app_path} AndroidManifest.xml")
                    report_content.append("Analisis del AndroidManifest:")
                    report_content.append(aapt_result)
                    report_content.append("")

                    # Búsqueda de componentes
                    manifest_lower = aapt_result.lower()
                    components = {
                        "receiver": "receiver" in manifest_lower,
                        "broadcastreceiver": "broadcastreceiver" in manifest_lower,
                        "intent_filter": "com.iu.diagnostics" in manifest_lower,
                        "activity": "activity" in manifest_lower,
                        "service": "service" in manifest_lower
                    }

                    report_content.append("Componentes encontrados:")
                    for comp, found in components.items():
                        report_content.append(f"  {comp}: {':D' if found else ':('}")

                else:
                    report_content.append(" No se pudo obtener el path de la app")

            except Exception as e:
                report_content.append(f"Error verificando manifest: {e}")

            report_content.append("")
            report_content.append("2. ACTIVIDAD EN LOGS DEL SISTEMA")
            report_content.append("=" * 50)

            # 2. Verificar logs del sistema
            self.run_adb_command("adb logcat -c")
            self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez test_flag true")
            time.sleep(2)

            broadcast_logs = self.run_adb_command("adb logcat -d -s ActivityManager:I *:S")
            report_content.append("Logs del sistema:")
            report_content.append(broadcast_logs)
            report_content.append("")

            # 3. Verificar dumpsys de actividad
            report_content.append("3. DUMPSYS DE ACTIVIDAD")
            report_content.append("=" * 50)

            activity_info = self.run_dumpsys_command("activity broadcasts")
            report_content.append("Dumpsys activity broadcasts:")
            report_content.append(activity_info[:2000] + "..." if len(activity_info) > 2000 else activity_info)
            report_content.append("")

            # 4. Verificar respuesta del sistema
            report_content.append("4. RESPUESTA DEL SISTEMA")
            report_content.append("=" * 50)

            broadcast_output = self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez test true")
            report_content.append("Respuesta del broadcast:")
            report_content.append(broadcast_output)
            report_content.append("")

            # 5. Múltiples pruebas de broadcast
            report_content.append("5. PRUEBAS MULTIPLES DE BROADCAST")
            report_content.append("=" * 50)

            test_cases = [
                ("Broadcast simple", "adb shell am broadcast -a com.iu.diagnostics.request"),
                ("Broadcast con flag true", "adb shell am broadcast -a com.iu.diagnostics.request --ez flag true"),
                ("Broadcast con flag false", "adb shell am broadcast -a com.iu.diagnostics.request --ez flag false"),
                ("Broadcast con string", "adb shell am broadcast -a com.iu.diagnostics.request --es data test")
            ]

            for test_name, test_command in test_cases:
                result = self.run_adb_command(test_command)
                report_content.append(f"{test_name}:")
                report_content.append(f"Resultado: {result}")
                report_content.append("")

            full_report = "\n".join(report_content)
            self.last_log_file = self.save_report("alternative_verifications", full_report)
            self.save_detailed_report("alternative_verifications", "analisis_completo", full_report)

            # Siempre pasa este test ya que es solo de recolección de información
            print(":D Verificaciones alternativas completadas - Ver reporte para detalles :D")

        self.run_test_with_report("alternative_receiver_verifications", func)


if __name__ == "__main__":
    unittest.main(verbosity=2)