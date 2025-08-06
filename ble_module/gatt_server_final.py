#!/usr/bin/env python3

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib
import os
import subprocess

# Definições D-Bus e BLE
BLUEZ_SERVICE_NAME = 'org.bluez'
ADAPTER_PATH = '/org/bluez/hci0'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHARACTERISTIC_IFACE = 'org.bluez.GattCharacteristic1'

class Characteristic(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, service, label):
        self.path = service.path + f'/char{index}'
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.service = service
        self.label = label
        self.value = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_CHARACTERISTIC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': dbus.Array(self.flags, signature='s'),
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(dbus_interface=GATT_CHARACTERISTIC_IFACE,
                         in_signature='', out_signature='ay')
    def ReadValue(self):
        print(f"🔎 Leitura de {self.label}: {''.join([chr(b) for b in self.value])}")
        return self.value

    @dbus.service.method(dbus_interface=GATT_CHARACTERISTIC_IFACE,
                         in_signature='aya{sv}', out_signature='')
    def WriteValue(self, value, options):
        str_value = ''.join([chr(byte) for byte in value])
        self.value = value
        print(f"✍️ {self.label} recebido: {str_value}")
        self.service.update_config(self.label, str_value)

class Service(dbus.service.Object):
    def __init__(self, bus, index, uuid, primary=True):
        self.path = f'/org/bluez/example/service{index}'
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        self.config = {"SSID": "", "Password": ""}
        dbus.service.Object.__init__(self, bus, self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def update_config(self, label, value):
        self.config[label] = value
        if self.config["SSID"] and self.config["Password"]:
            self.save_wifi_config()

    def save_wifi_config(self):
        ssid = self.config["SSID"]
        password = self.config["Password"]
        print("💾 A guardar configuração Wi-Fi...")
        config_text = f"""
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=PT

network={{
    ssid="{ssid}"
    psk="{password}"
}}
"""
        try:
            with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
                f.write(config_text)
            print("✅ Ficheiro guardado com sucesso.")
            subprocess.run(["wpa_cli", "-i", "wlan0", "reconfigure"])
            print("🔁 Wi-Fi reiniciado.")
        except Exception as e:
            print("❌ Erro ao guardar Wi-Fi:", e)

class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def add_service(self, service):
        self.services.append(service)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_OM_IFACE,
                         out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for char in service.characteristics:
                response[char.get_path()] = char.get_properties()
        return response

def main():
    print("📡 A iniciar GATT Server BLE...")

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    adapter = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, ADAPTER_PATH),
        GATT_MANAGER_IFACE
    )

    app = Application(bus)

    wifi_service = Service(bus, 0, "12345678-1234-5678-1234-56789abcdef0")
    ssid_char = Characteristic(bus, 0, "12345678-1234-5678-1234-56789abcdef1", ["read", "write"], wifi_service, "SSID")
    pass_char = Characteristic(bus, 1, "12345678-1234-5678-1234-56789abcdef2", ["read", "write"], wifi_service, "Password")

    wifi_service.add_characteristic(ssid_char)
    wifi_service.add_characteristic(pass_char)
    app.add_service(wifi_service)

    adapter.RegisterApplication(app.get_path(), {},
        reply_handler=lambda: print("✅ GATT Server registado com sucesso."),
        error_handler=lambda e: print("❌ Erro ao registar aplicação GATT:", e)
    )

    GLib.MainLoop().run()

if __name__ == "__main__":
    main()
