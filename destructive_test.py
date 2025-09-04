import unittest
import time
import os
from datetime import datetime
from appium import webdriver
from appium.options.android import UiAutomator2Options
from capabilities_loader import load_capabilities
from report_utils import generate_html_report
from adb_utils import run_adb_command, run_dumpsys_command


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
            raise ValueError("No se encontro appPackage en las capabilities")
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
        generate_html_report(cls.app_package, cls.test_results, cls.detailed_reports, REPORTS_DIR)

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

    def run_test_with_report(self, test_name, test_func):
        try:
            test_func()
            self.test_results.append({
                "name": test_name,
                "status": "PASS",
                "message": "OK",
                "log_file": getattr(self, "last_log_file", None)
            })
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            log_context = self.get_logcat_error_context()
            full_error = f"{error_msg}\n\nContexto de log relevante:\n{log_context}"
            self.test_results.append({
                "name": test_name,
                "status": "FAIL",
                "message": full_error,
                "log_file": getattr(self, "last_log_file", None)
            })
            self.save_report(test_name, full_error)
            self.save_detailed_report(test_name, "error", full_error)
            raise

    # Prueba destructiva: datos extremadamente grandes
    def test_broadcast_extremely_large_data(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: DATOS EXTREMADAMENTE GRANDES ===", f"Timestamp: {datetime.now()}", ""]
            large_data = "X" * 10000
            output = run_adb_command(f"adb shell am broadcast -a com.iu.diagnostics.request --es data \"{large_data}\"")
            time.sleep(3)
            report_content.append(f"Output: {output}")
            crash = "Exception" in output or "Error" in output or "Failure" in output
            self.last_log_file = self.save_report("destructive_large_data", "\n".join(report_content))
            self.save_detailed_report("destructive_large_data", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, f"La app fallo gravemente con datos extremadamente grandes. Output: {output}")
        self.run_test_with_report("destructive_large_data", func)

    # Prueba destructiva: tipo de dato inesperado
    def test_broadcast_unexpected_type(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: TIPO DE DATO INESPERADO ===", f"Timestamp: {datetime.now()}", ""]
            output = run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ei data 12345")
            time.sleep(3)
            report_content.append(f"Output: {output}")
            crash = "Exception" in output or "Error" in output or "Failure" in output
            self.last_log_file = self.save_report("destructive_unexpected_type", "\n".join(report_content))
            self.save_detailed_report("destructive_unexpected_type", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, "La app fallo gravemente con tipo de dato inesperado")
        self.run_test_with_report("destructive_unexpected_type", func)

    # Prueba destructiva: datos corruptos (caracteres no válidos)
    def test_broadcast_corrupt_data(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: DATOS CORRUPTOS ===", f"Timestamp: {datetime.now()}", ""]
            corrupt_data = "\x00\xff\xfe\xfd"
            output = run_adb_command(f"adb shell am broadcast -a com.iu.diagnostics.request --es data \"{corrupt_data}\"")
            time.sleep(3)
            report_content.append(f"Output: {output}")
            crash = "Exception" in output or "Error" in output or "Failure" in output
            self.last_log_file = self.save_report("destructive_corrupt_data", "\n".join(report_content))
            self.save_detailed_report("destructive_corrupt_data", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, "La app fallo gravemente con datos corruptos")
        self.run_test_with_report("destructive_corrupt_data", func)

    # Prueba destructiva: saturación de broadcasts en bucle rápido
    def test_broadcast_saturation(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: SATURACION DE BROADCASTS ===", f"Timestamp: {datetime.now()}", ""]
            errors = []
            for i in range(100):
                output = run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez flag true")
                time.sleep(0.1)
                report_content.append(f"Broadcast {i}: {output}")
                if any(e in output for e in ["Exception", "Error", "Failure"]):
                    errors.append(output)
            self.last_log_file = self.save_report("destructive_saturation", "\n".join(report_content))
            self.save_detailed_report("destructive_saturation", "analisis_completo", "\n".join(report_content))
            self.assertFalse(errors, f"Fallos graves detectados en saturación: {errors}")
        self.run_test_with_report("destructive_saturation", func)

    def get_logcat_error_context(self, context_lines=5):
        logcat_output = run_adb_command(f"adb logcat -d")
        lines = logcat_output.splitlines()
        for idx, line in enumerate(lines):
            if any(x in line.lower() for x in ["exception", "error", "failure", "crash"]):
                start = max(0, idx - context_lines)
                end = min(len(lines), idx + context_lines + 1)
                context = "\n".join(lines[start:end])
                return context
        return "(No se encontró línea de error relevante)"

    # Prueba destructiva: datos nulos o vacíos
    def test_broadcast_null_or_empty_data(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: DATOS NULOS O VACIOS ===", f"Timestamp: {datetime.now()}", ""]
            output = run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --es data \"\"")
            time.sleep(2)
            report_content.append(f"Output: {output}")
            crash = "Exception" in output or "Error" in output or "Failure" in output
            if crash:
                log_context = self.get_logcat_error_context()
                report_content.append(f"Contexto de log relevante:\n{log_context}")
            self.last_log_file = self.save_report("destructive_null_empty_data", "\n".join(report_content))
            self.save_detailed_report("destructive_null_empty_data", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, "La app fallo gravemente con datos nulos o vacios")
        self.run_test_with_report("destructive_null_empty_data", func)

    # Prueba destructiva: caracteres especiales y unicode extremo
    def test_broadcast_special_unicode(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: CARACTERES ESPECIALES/UNICODE ===", f"Timestamp: {datetime.now()}", ""]
            special_data = "😀🚀💥\u202e\u200b\u0000"
            output = run_adb_command(f"adb shell am broadcast -a com.iu.diagnostics.request --es data \"{special_data}\"")
            time.sleep(2)
            report_content.append(f"Output: {output}")
            crash = "Exception" in output or "Error" in output or "Failure" in output
            self.last_log_file = self.save_report("destructive_special_unicode", "\n".join(report_content))
            self.save_detailed_report("destructive_special_unicode", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, "La app fallo gravemente con caracteres especiales/unicode")
        self.run_test_with_report("destructive_special_unicode", func)

    # Prueba destructiva: tipo de dato incompatible (array en vez de string)
    def test_broadcast_incompatible_type(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: TIPO DE DATO INCOMPATIBLE ===", f"Timestamp: {datetime.now()}", ""]
            output = run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --esa data \"uno,dos,tres\"")
            time.sleep(2)
            report_content.append(f"Output: {output}")
            crash = "Exception" in output or "Error" in output or "Failure" in output
            self.last_log_file = self.save_report("destructive_incompatible_type", "\n".join(report_content))
            self.save_detailed_report("destructive_incompatible_type", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, "La app fallo gravemente con tipo de dato incompatible")
        self.run_test_with_report("destructive_incompatible_type", func)

    # Prueba destructiva: flags desconocidos
    def test_broadcast_unknown_flags(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: FLAGS DESCONOCIDOS ===", f"Timestamp: {datetime.now()}", ""]
            output = run_adb_command("adb shell am broadcast -a com.iu.diagnostics.request --ez unknown_flag true")
            time.sleep(2)
            report_content.append(f"Output: {output}")
            crash = "Exception" in output or "Error" in output or "Failure" in output
            self.last_log_file = self.save_report("destructive_unknown_flags", "\n".join(report_content))
            self.save_detailed_report("destructive_unknown_flags", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, "La app fallo gravemente con flags desconocidos")
        self.run_test_with_report("destructive_unknown_flags", func)

    # Prueba destructiva: datos binarios
    def test_broadcast_binary_data(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: DATOS BINARIOS ===", f"Timestamp: {datetime.now()}", ""]
            binary_data = "".join([chr(i) for i in range(32, 128)])  # Caracteres ASCII imprimibles
            output = run_adb_command(f"adb shell am broadcast -a com.iu.diagnostics.request --es data \"{binary_data}\"")
            time.sleep(2)
            report_content.append(f"Output: {output}")
            crash = "Exception" in output or "Error" in output or "Failure" in output
            self.last_log_file = self.save_report("destructive_binary_data", "\n".join(report_content))
            self.save_detailed_report("destructive_binary_data", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, "La app fallo gravemente con datos binarios")
        self.run_test_with_report("destructive_binary_data", func)

    # Monkey test to simulate random user interactions
    def test_monkey_crash(self):
        def func():
            report_content = ["=== TEST DESTRUCTIVA: MONKEY CRASH ===", f"Timestamp: {datetime.now()}", ""]
            monkey_cmd = f"adb shell monkey -p {self.app_package} -v 5000"
            output = run_adb_command(monkey_cmd, timeout=120)
            report_content.append(f"Monkey Output:\n{output}")
            crash = any(x in output.lower() for x in ["exception", "error", "failure", "crash"])
            if crash:
                log_context = self.get_logcat_error_context()
                report_content.append(f"Contexto de log relevante:\n{log_context}")
            self.last_log_file = self.save_report("destructive_monkey_crash", "\n".join(report_content))
            self.save_detailed_report("destructive_monkey_crash", "analisis_completo", "\n".join(report_content))
            self.assertFalse(crash, "La app fallo gravemente durante la prueba Monkey")
        self.run_test_with_report("destructive_monkey_crash", func)

if __name__ == "__main__":
    unittest.main(verbosity=2)