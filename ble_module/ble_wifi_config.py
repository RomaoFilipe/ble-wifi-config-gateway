import json
import os
import sys
import signal
from pybleno import *

# BLE config
SERVICE_UUID = '13333333-3333-3333-3333-333333333337'
CHAR_UUID = '13333333-3333-3333-3333-333333330001'

class WifiConfigCharacteristic(Characteristic):
    def __init__(self):
        Characteristic.__init__(self, {
            'uuid': CHAR_UUID,
            'properties': ['write'],
            'descriptors': [
                Descriptor({
                    'uuid': '2901',
                    'value': 'Wi-Fi SSID & password configurator'
                })
            ]
        })

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        try:
            msg = data.decode('utf-8')
            print(f"🔔 Dados recebidos via BLE: {msg}")
            conf = json.loads(msg)
            ssid = conf.get('ssid')
            password = conf.get('password')
            if ssid and password:
                print(f"📲 SSID recebido: '{ssid}', PASSWORD: '[oculto]'")
                self.write_wifi_config(ssid, password)
            else:
                print("❌ Formato inválido! Envia JSON: {\"ssid\": \"xxx\", \"password\": \"yyy\"}")
        except Exception as e:
            print(f"❌ Erro ao processar dados BLE: {e}")
        callback(Characteristic.RESULT_SUCCESS)

    def write_wifi_config(self, ssid, password):
        try:
            conf = f"""
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=PT

network={{
    ssid="{ssid}"
    psk="{password}"
}}
"""
            with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
                f.write(conf)
            print("💾 Ficheiro wpa_supplicant gravado com sucesso.")
            # Reiniciar Wi-Fi (opcional)
            os.system("sudo wpa_cli -i wlan0 reconfigure")
            print("🔁 Comando para reiniciar Wi-Fi enviado!")
        except Exception as e:
            print(f"❌ Erro ao gravar ficheiro Wi-Fi: {e}")

# BLE Service
wifiConfigService = BlenoPrimaryService({
    'uuid': SERVICE_UUID,
    'characteristics': [WifiConfigCharacteristic()]
})

# Setup BLE
bleno = Bleno()

def on_state_change(state):
    if state == 'poweredOn':
        print("🟢 BLE ativado, pronto para ligação via LightBlue/nRF Connect!")
        bleno.startAdvertising('IOT-Gateway', [SERVICE_UUID])
    else:
        print("🔴 BLE não ativo!")
        bleno.stopAdvertising()

def on_advertising_start(error):
    if not error:
        print("🚀 Publicidade BLE iniciada! Serviço disponível.")
        bleno.setServices([wifiConfigService])
    else:
        print(f"❌ Erro ao anunciar BLE: {error}")

bleno.on('stateChange', on_state_change)
bleno.on('advertisingStart', on_advertising_start)

# Para sair limpo
def handler(sig, frame):
    print('\n🛑 A terminar serviço BLE...')
    bleno.stopAdvertising()
    bleno.disconnect()
    sys.exit(0)
signal.signal(signal.SIGINT, handler)

# Run main BLE loop
bleno.start()
print("🟢 BLE GATT server a correr! Vai ao LightBlue e procura 'IOT-Gateway'.")
signal.pause()
