# adb_utils.py
import subprocess

def run_adb_command(command, timeout=30):
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

def run_dumpsys_command(command_suffix, timeout=60):
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