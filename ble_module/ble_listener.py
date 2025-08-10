#!/usr/bin/env python3
"""
Script BLE Listener com bluepy - Raspberry Pi 4
Recebe SSID e Password via Bluetooth BLE e atualiza
/etc/wpa_supplicant/wpa_supplicant.conf
"""

from bluepy.btle import DefaultDelegate
import subprocess
import os
import platform
import shutil
import datetime
import time

WPA_CONF_PATH   = "/etc/wpa_supplicant/wpa_supplicant.conf"
BACKUP_DIR      = "/etc/wpa_supplicant/backups"

def backup_wpa_supplicant():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"wpa_supplicant.conf.backup.{ts}")
    shutil.copy2(WPA_CONF_PATH, bak)
    print(f"🗄️ Backup criado em {bak}")

def validate_ssid(ssid):
    if not ssid or '"' in ssid:
        return False
    return True

def validate_password(pw):
    return pw and 8 <= len(pw) <= 63

class WifiConfigDelegate(DefaultDelegate):
    def __init__(self, ssid, password):
        super().__init__()
        self.ssid     = ssid
        self.password = password
        self.apply_wifi_config()

    def apply_wifi_config(self):
        print(f"📲 SSID recebido: '{self.ssid}'   Password: '[oculto]'")

        if not validate_ssid(self.ssid):
            print("❌ SSID inválido! Abortando.")
            return
        if not validate_password(self.password):
            print("❌ Password inválida! Abortando.")
            return

        backup_wpa_supplicant()

        bloco = f"""
network={{
    ssid="{self.ssid}"
    psk="{self.password}"
}}
"""
        try:
            with open(WPA_CONF_PATH, "a") as f:
                f.write(bloco)
            print("💾 Configuração Wi-Fi gravada com sucesso.")
        except PermissionError:
            print("❌ Permissão negada ao escrever em", WPA_CONF_PATH)
            return

        if "microsoft" in platform.uname().release.lower():
            print("⚠️ Ambiente WSL — não reinicio Wi-Fi.")
        else:
            print("🔁 A tentar reiniciar Wi-Fi com wpa_cli...")
            res = subprocess.run(
                ["wpa_cli", "-i", "wlan0", "reconfigure"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                print("✅ Wi-Fi reiniciado com sucesso.")
            else:
                print("❌ Falha ao reiniciar Wi-Fi:", res.stderr)

def main():
    print("🔍 A iniciar serviço BLE com bluepy...")
    # AQUI colocas a lógica de GATT para obter ssid/password; por agora, valores de exemplo:
    ssid = "SSID_EXEMPLO"
    pw   = "PASSWORD_EXEMPLO"
    WifiConfigDelegate(ssid, pw)

    # Loop infinito para manter o serviço vivo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 BLE Scanner interrompido pelo utilizador")

if __name__ == "__main__":
    main()
