# 🔵 BLE Wi-Fi Config Gateway

Este projeto transforma um Raspberry Pi 4 num gateway inteligente que recebe credenciais Wi-Fi via Bluetooth (BLE), grava-as no sistema e reinicia a interface de rede automaticamente. Ideal para dispositivos IoT sem ecrã, onde a configuração Wi-Fi precisa de ser feita por proximidade.

## 🛁 Funcionalidades

* Servidor BLE GATT com duas características (`SSID` e `Password`)
* Escreve diretamente no ficheiro `/etc/wpa_supplicant.conf`
* Reinicia o Wi-Fi após receber dados
* Corre automaticamente ao iniciar o sistema (`systemd`)
* Painel de controlo com Docker + MQTT + Web config
* Monitorização por watchdog

## 🚀 Estrutura do Projeto

```bash
iot-gateway/
├── ble_module/             # Contém o gatt_server_final.py e ble_listener.py
├── gateway_core/           # Código Ruby do sensor_gateway.rb
├── shared/                 # Pasta partilhada entre serviços
├── watchdog/               # Script de watchdog para monitorizar serviços
├── web_config/             # Interface Web simples para BLE via nginx
├── docker-compose.yml      # Orquestra todos os serviços
└── README.md
```

## 🧠 Lógica Geral

1. O Raspberry Pi entra em modo `discoverable` e `pairable`
2. Um smartphone envia SSID e password via BLE GATT characteristics
3. O `gatt_server_final.py` recebe os dados e grava no `/etc/wpa_supplicant.conf`
4. O Wi-Fi reinicia automaticamente
5. O container `sensor_gateway` começa a enviar dados para a app Rails via API

## ⚖️ Pré-requisitos

* Raspberry Pi 4 com Bluetooth e Docker instalado
* `bluez`, `python3-dbus`, `python3-gi`, `bluepy`, `wpasupplicant`
* Permissões root para acesso à rede e bluetooth
* Ruby >= 3.2 (para o sensor\_gateway.rb)

## 🐳 Instruções Docker

```bash
# Build e iniciar todos os serviços
docker-compose up -d --build

# Ou utilizar script personalizado
./start_gateway.sh

# Verificar estado
docker ps

# Ver logs do BLE listener
docker logs -f iot_ble_scanner
```

## ⚙️ Ativar GATT Server no arranque

```bash
# Criado em: /usr/local/bin/start-gatt-server.sh
# Service: /etc/systemd/system/gatt-server.service

sudo systemctl enable gatt-server.service
sudo systemctl start gatt-server.service
```

## ✅ Testar GATT Manualmente

```bash
sudo -E python3 ble_module/gatt_server_final.py
```

## 📦 Comandos úteis

```bash
docker ps                    # Ver serviços ativos
docker logs -f nome_servico  # Ver logs de um serviço
bluetoothctl                 # CLI para controlo do bluetooth
```

## 👤 Autor

Romão Filipe – Projeto IoT Gateway BLE (2025)

---

Feito com ❤️ em Portugal 🇵🇹
