import os
import time
import subprocess

# Lista de containers a monitorizar
containers = [
    "iot_sensor_gateway",
    "iot_ble_scanner",
    "mosquitto"
]

# Tempo entre verificações (em segundos)
CHECK_INTERVAL = 60

def is_container_running(name):
    """Verifica se o container está a correr"""
    try:
        output = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Running}}", name])
        return output.strip() == b'true'
    except subprocess.CalledProcessError:
        return False

def restart_container(name):
    """Reinicia o container se estiver parado"""
    print(f"🔄 A reiniciar o container: {name}")
    os.system(f"docker restart {name}")

if __name__ == "__main__":
    print("🛡️ Watchdog a correr...")

    while True:
        for container in containers:
            if not is_container_running(container):
                print(f"⚠️  {container} está parado!")
                restart_container(container)
            else:
                print(f"✅ {container} está ativo.")
        print("⏳ A aguardar próxima verificação...\n")
        time.sleep(CHECK_INTERVAL)
