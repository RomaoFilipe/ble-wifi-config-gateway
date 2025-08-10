from bluepy.btle import Peripheral, UUID, Service, Characteristic, DefaultDelegate, Advertisement
import time
import json
import subprocess

WIFI_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
WIFI_CHAR_UUID    = "12345678-1234-5678-1234-56789abcdef1"

class WifiConfigDelegate(DefaultDelegate):
    def __init__(self):
        super().__init__()

    def handleWrite(self, cHandle, data):
        try:
            msg = data.decode("utf-8")
            print(f"🔔 Dados recebidos via BLE: {msg}")
            conf = json.loads(msg)
            ssid = conf.get('ssid')
            password = conf.get('password')
            if ssid and password:
                print(f"📲 SSID recebido: '{ssid}', PASSWORD: '[oculto]'")
                # Aqui podes gravar o ficheiro wpa_supplicant, se quiseres.
            else:
                print("❌ Formato inválido! Envia JSON: {\"ssid\": \"xxx\", \"password\": \"yyy\"}")
        except Exception as e:
            print(f"❌ Erro ao processar dados BLE: {e}")

class WifiCharacteristic(Characteristic):
    def __init__(self):
        Characteristic.__init__(
            self,
            UUID(WIFI_CHAR_UUID),
            props=Characteristic.props["WRITE"],
            perms=Characteristic.perms["WRITEABLE"]
        )
        self.value = b""

    def WriteValue(self, value, options):
        self.value = value
        delegate.handleWrite(self.getHandle(), value)

# NOTA: bluepy não tem GATT server puro nativo.
# Para servidores BLE completos em Python, usa bleak ou pygatt — mas bluepy pode ser usado como demo.

print("🔵 [INFO] BLE GATT server demo - onboarding Wi-Fi.")
print("⚠️ bluepy só faz GATT client puro, não server puro.")
print("Para um GATT Server 100% no Pi4, usa pygattlib (ou instala node-bleno).")
print("Este exemplo serve para DEMO/teste. Para produção BLE server, usa C ou Node.js (bleno).")

# Recomendo fortemente: para produção real BLE GATT server no Pi, usa node-bleno.
# Podes correr um script Node.js que faz BLE server e comunica via ficheiro ou pipe ao Python!


