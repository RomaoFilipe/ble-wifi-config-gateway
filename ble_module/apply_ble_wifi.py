import json
import subprocess
import time
import shutil

BLE_WIFI_FILE = "/tmp/ble_wifi.json"
WPA_SUPPLICANT_CONF = "/etc/wpa_supplicant/wpa_supplicant.conf"

def backup_wpa():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = f"/etc/wpa_supplicant/wpa_supplicant.conf.backup.{timestamp}"
    shutil.copy2(WPA_SUPPLICANT_CONF, backup_path)
    print(f"🗄️ Backup criado: {backup_path}")

def read_ble_wifi():
    with open(BLE_WIFI_FILE) as f:
        data = json.load(f)
        return data["ssid"], data["password"]

def write_wpa_supplicant(ssid, password):
    config = f'''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=PT

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
    with open(WPA_SUPPLICANT_CONF, "w") as f:
        f.write(config)
    print("💾 Novo wpa_supplicant.conf gravado.")

def restart_wifi():
    print("🔁 A reiniciar Wi-Fi...")
    res = subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"], capture_output=True, text=True)
    if res.returncode == 0:
        print("✅ Wi-Fi reiniciado com sucesso.")
    else:
        print("❌ Falha ao reiniciar Wi-Fi:", res.stderr)

def main():
    ssid, password = read_ble_wifi()
    print(f"🔑 SSID: {ssid} | PASSWORD: [oculto]")
    backup_wpa()
    write_wpa_supplicant(ssid, password)
    restart_wifi()

if __name__ == "__main__":
    main()
