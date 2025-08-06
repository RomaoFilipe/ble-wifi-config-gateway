#!/bin/bash

echo "🔄 A parar e limpar containers antigos..."
docker-compose down
docker container prune -f

echo "🔧 A verificar estado do Bluetooth (hci0)..."
if hciconfig | grep -q "hci0"; then
  echo "✅ Bluetooth está ativo:"
  hciconfig
else
  echo "⚠️ Bluetooth não detetado. A tentar reativar..."
  sudo rfkill unblock bluetooth
  sudo systemctl restart bluetooth
  sleep 2
  if hciconfig | grep -q "hci0"; then
    echo "✅ Bluetooth ativado com sucesso:"
    hciconfig
  else
    echo "❌ ERRO: Bluetooth ainda indisponível. Verifica drivers ou hardware."
    exit 1
  fi
fi

echo "🚀 A fazer build de todos os serviços..."
docker-compose build

echo "✅ A iniciar todos os containers em modo detached..."
docker-compose up -d

echo ""
echo "📋 Estado dos containers:"
docker ps

echo ""
echo "📡 Logs do serviço BLE (iot_ble_scanner):"
docker logs -f iot_ble_scanner
