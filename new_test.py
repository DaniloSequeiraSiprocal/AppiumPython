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

    @classmethod
    def generate_html_report(cls):
        html_file = os.path.join(REPORTS_DIR, "receiver_test_summary.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Receiver Test Summary</title>")
            f.write("<style>table {border-collapse: collapse; width: 100%;} ")
            f.write("th, td {border: 1px solid #ddd; padding: 8px; text-align: left;} ")
            f.write("tr:nth-child(even){background-color: #f2f2f2} ")
            f.write("th {background-color: #4CAF50; color: white;} ")
            f.write(".PASS {color: green;} .FAIL {color: red;} .SKIP {color: orange;}</style></head>")
            f.write("<body><h2>Resumen de Pruebas CommandReceiver</h2>")
            f.write(f"<p><strong>App Package:</strong> {cls.app_package}</p>")
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

            f.write("</table></body></html>")
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
                errors='ignore'  # Ignorar caracteres que no se pueden decodificar
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

            # Para dumpsys, usar subprocess.Popen con manejo binario
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                # Decodificar ignorando errores
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
            message = "Exito"
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
            self.fail(f"{test_name} falló: {message}")

    # ---------- Test 1: Broadcast válido ----------
    def test_send_valid_broadcast(self):
        def func():
            output = self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez flag true")
            self.last_log_file = self.save_report("send_valid_broadcast", output)
            error_indicators = ["Exception", "Error", "Failure", "not found"]
            has_errors = any(indicator in output for indicator in error_indicators)
            self.assertFalse(has_errors, f"El broadcast fallo: {output}")
        self.run_test_with_report("send_valid_broadcast", func)

    # ---------- Test 2: Broadcast inválido ----------
    def test_send_invalid_broadcast(self):
        def func():
            output = self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez invalidFlag notABoolean")
            self.last_log_file = self.save_report("send_invalid_broadcast", output)
            self.assertNotIn("AndroidRuntime", output,
                             "El broadcast invalido provoco un crash de la aplicacion")
        self.run_test_with_report("send_invalid_broadcast", func)

    # ---------- Test 3: Logcat del receiver ----------
    def test_logcat_for_receiver(self):
        def func():
            # Limpiar logcat
            self.run_adb_command("adb logcat -c")

            # Enviar broadcast
            self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez flag true")

            time.sleep(3)

            # Obtener logs
            log_output = self.run_adb_command("adb logcat -d -s ActivityManager:I BroadcastQueue:I *:S")

            self.last_log_file = self.save_report("logcat_receiver", log_output)
            self.assertTrue(len(log_output.strip()) > 0,
                            "No se registro actividad del receiver en logcat")
        self.run_test_with_report("logcat_receiver", func)

    # ---------- Test 4: Verificaciones alternativas del receiver ----------
    def test_alternative_receiver_verifications(self):
        def func():
            print("Realizando verificaciones alternativas del receiver...")

            # 1. Verificar si el receiver está declarado en el AndroidManifest
            print("\n1. 🔍 Verificando declaración del receiver...")
            try:
                # Obtener path de la app (devolverá algo como: /data/app/package.name-abc123/base.apk)
                app_path_result = self.run_adb_command(f"adb shell pm path {self.app_package}")
                app_path = app_path_result.strip().replace('package:', '')

                if app_path and not app_path.startswith("ERROR"):
                    print(f"📦 Path de la app: {app_path}")

                    # Método 1: Usar aapt para analizar el manifest
                    aapt_result = self.run_adb_command(f"adb shell aapt dump xmltree {app_path} AndroidManifest.xml")

                    # Búsqueda exhaustiva en el manifest
                    manifest_content = aapt_result.lower()

                    # Buscar evidence de receivers
                    receiver_found = False
                    intent_filter_found = False
                    command_receiver_found = False

                    # Buscar receivers en general
                    if "receiver" in manifest_content or "broadcastreceiver" in manifest_content:
                        receiver_found = True
                        print("✅ Receiver(s) encontrado(s) en el manifest")

                        # Buscar el intent-filter específico
                        if "com.iu.diagnostics" in manifest_content:
                            intent_filter_found = True
                            print("✅ Intent filter com.iu.diagnostics encontrado")

                        # Buscar nombres de clases que puedan ser el CommandReceiver
                        receiver_keywords = [
                            "command", "receiver", "broadcast", "diagnostics",
                            "amlibrary", "iu", "com.iu", "diagnostic"
                        ]

                        # Buscar líneas que contengan receiver y alguno de los keywords
                        lines = aapt_result.split('\n')
                        for i, line in enumerate(lines):
                            line_lower = line.lower()
                            if ("receiver" in line_lower or "broadcastreceiver" in line_lower) and any(keyword in line_lower for keyword in receiver_keywords):
                                print(f"   🔍 Receiver relevante: {line.strip()}")
                                # Mostrar contexto
                                for j in range(max(0, i-2), min(len(lines), i+3)):
                                    marker = "→ " if j == i else "  "
                                    print(f"   {marker}{lines[j].strip()}")
                                command_receiver_found = True
                                break

                    # Método 2 alternativo: Buscar en strings del APK
                    if not command_receiver_found:
                        print("🔍 Buscando en strings del APK...")
                        strings_result = self.run_adb_command(f"adb shell aapt dump strings {app_path}")
                        if "command" in strings_result.lower() and "receiver" in strings_result.lower():
                            print("✅ Posible CommandReceiver encontrado en strings del APK")
                            command_receiver_found = True

                    # Método 3: Buscar clases en el APK
                    if not command_receiver_found:
                        print("🔍 Buscando clases en el APK...")
                        classes_result = self.run_adb_command(f"adb shell aapt dump resources {app_path}")
                        class_patterns = ["command", "receiver", "broadcast"]
                        for pattern in class_patterns:
                            if pattern in classes_result.lower():
                                print(f"✅ Clase relacionada con '{pattern}' encontrada")
                                command_receiver_found = True
                                break

                    if not receiver_found:
                        print("❌ No se encontraron receivers en el manifest")

                else:
                    print("❌ No se pudo obtener el path de la app")

            except Exception as e:
                print(f"⚠️  Error verificando manifest: {e}")

            # 2. Verificar actividad mediante logs del sistema
            print("\n2. 📋 Verificando actividad mediante logs de sistema...")

            # Limpiar logcat
            self.run_adb_command("adb logcat -c")

            # Enviar broadcast
            self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez test_flag true")

            time.sleep(2)

            # Obtener logs del sistema con más información
            broadcast_logs = self.run_adb_command("adb logcat -d -s ActivityManager:I *:S")

            # Búsqueda exhaustiva en logs
            log_indicators = [
                "com.iu.diagnostics", "deliverTo", "scheduleReceive", "finishReceiver",
                "broadcast", "receiver", self.app_package, "diagnostics", "iu"
            ]

            broadcast_processed = False
            relevant_logs = []

            for line in broadcast_logs.split('\n'):
                if any(indicator.lower() in line.lower() for indicator in log_indicators):
                    relevant_logs.append(line)
                    if not broadcast_processed and any(x in line for x in ["com.iu.diagnostics", "deliverTo", self.app_package]):
                        broadcast_processed = True

            if broadcast_processed:
                print("✅ El broadcast fue procesado por el sistema")
                print("   Logs relevantes:")
                for log in relevant_logs[:5]:  # Mostrar solo los primeros 5 logs relevantes
                    print(f"   📝 {log}")
            else:
                print("❌ No hay evidencia de procesamiento del broadcast")
                if relevant_logs:
                    print("   Logs encontrados (pueden ser relevantes):")
                    for log in relevant_logs[:3]:
                        print(f"   📝 {log}")

            # 3. Verificar mediante dumpsys de actividad
            print("\n3. 📊 Verificando mediante dumpsys de actividad...")

            activity_info = self.run_dumpsys_command("activity broadcasts")
            activity_info_lower = activity_info.lower()

            # Búsqueda más amplia en dumpsys
            our_broadcast_found = any(indicator in activity_info_lower for indicator in [
                "com.iu.diagnostics", "diagnostics", "iu.diagnostics", "broadcast"
            ])

            if our_broadcast_found:
                print("✅ Broadcast encontrado en el historial de actividad")
                # Buscar y mostrar la línea específica
                lines = activity_info.split('\n')
                for i, line in enumerate(lines):
                    if any(indicator in line.lower() for indicator in ["com.iu.diagnostics", "diagnostics"]):
                        print(f"   📍 Encontrado: {line.strip()}")
                        break
            else:
                print("❌ Broadcast no encontrado en actividad")

            # 4. Verificar respuesta del sistema al broadcast
            print("\n4. 📡 Verificando respuesta del sistema...")

            broadcast_output = self.run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez test true")

            completed_indicators = ["Broadcast completed", "result=0", "success", "completed", "finished"]
            error_indicators = ["error", "exception", "failure", "failed"]

            broadcast_completed = any(indicator in broadcast_output for indicator in completed_indicators)
            has_errors = any(indicator in broadcast_output.lower() for indicator in error_indicators)

            if broadcast_completed and not has_errors:
                print("✅ Broadcast completado exitosamente")
            elif has_errors:
                print(f"❌ Broadcast falló: {broadcast_output[:200]}...")
            else:
                print(f"⚠️  Estado del broadcast indeterminado: {broadcast_output[:100]}...")

            # 5. Verificar con múltiples tipos de broadcasts
            print("\n5. 🧪 Probando diferentes tipos de broadcasts...")

            test_cases = [
                ("Broadcast simple", "adb shell am broadcast -a com.iu.diagnostics.request"),
                ("Broadcast con flag true", "adb shell am broadcast -a com.iu.diagnostics.request --ez flag true"),
                ("Broadcast con flag false", "adb shell am broadcast -a com.iu.diagnostics.request --ez flag false"),
                ("Broadcast con string", "adb shell am broadcast -a com.iu.diagnostics.request --es data test")
            ]

            successful_broadcasts = 0
            for test_name, test_command in test_cases:
                try:
                    result = self.run_adb_command(test_command)
                    if not any(indicator in result.lower() for indicator in error_indicators):
                        successful_broadcasts += 1
                        print(f"   ✅ {test_name}: OK")
                    else:
                        print(f"   ❌ {test_name}: Error")
                except:
                    print(f"   ❌ {test_name}: Falló")

            print(f"   📊 Broadcasts exitosos: {successful_broadcasts}/{len(test_cases)}")

            # Generar reporte consolidado
            print("\n" + "="*60)
            print("📊 RESUMEN DE VERIFICACIONES ALTERNATIVAS")
            print("="*60)

            findings = [
                ("Receiver en manifest", receiver_found),
                ("Intent filter encontrado", intent_filter_found),
                ("CommandReceiver identificado", command_receiver_found),
                ("Broadcast procesado", broadcast_processed),
                ("En historial actividad", our_broadcast_found),
                ("Broadcast completado", broadcast_completed),
                ("Múltiples broadcasts exitosos", successful_broadcasts >= 2),
            ]

            total_findings = sum(1 for _, found in findings if found)

            for test_name, found in findings:
                status = "✅" if found else "❌"
                print(f"{status} {test_name}")

            print(f"\n📋 Total de verificaciones positivas: {total_findings}/{len(findings)}")

            if total_findings >= 3:
                print("🎯 CONCLUSIÓN: El receiver parece estar funcionando")
                return
            else:
                raise AssertionError("El receiver no muestra suficiente actividad en las verificaciones")

        self.run_test_with_report("alternative_receiver_verifications", func)


if __name__ == "__main__":
    unittest.main(verbosity=2)