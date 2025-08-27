import subprocess

# Definimos los parámetros del broadcast
package_name = "amazonia.iu.com"
receiver_name = ".receivers.CommandReceiver"
action = "com.iu.diagnostics.request"
extra_key = "reply_pkg"
extra_value = package_name

# Comando adb para enviar el broadcast directamente al receiver
broadcast_cmd = [
    "adb", "shell", "am", "broadcast",
    "-n", f"{package_name}/{receiver_name}",
    "-a", action,
    f"--es", extra_key, extra_value,
    "-S"  # Mostrar el resultado devuelto por el broadcast
]

try:
    print("Enviando broadcast al receiver...")
    result = subprocess.run(broadcast_cmd, capture_output=True, text=True, check=True)

    # Mostramos la salida del broadcast
    print("==== Resultado del Broadcast ====")
    print(result.stdout)
    print("==== Fin del Resultado ====")

except subprocess.CalledProcessError as e:
    print("Error al enviar el broadcast:")
    print(e.stderr)
