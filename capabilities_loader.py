# capabilities_loader.py
import json
import os

def load_capabilities():
    profile = os.getenv("CAPS_PROFILE", "android_default")  # valor por defecto
    with open("capabilities.json", "r") as f:
        caps = json.load(f)
    if profile not in caps:
        raise ValueError(f"Perfil '{profile}' no encontrado en capabilities.json")
    return caps[profile]
