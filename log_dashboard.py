from flask import Flask, render_template_string
import subprocess
import os

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <title>Dashboard de Logs IoT</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 min-h-screen">
  <div class="max-w-5xl mx-auto p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-green-400 flex items-center gap-2">
        <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><path fill="#43f98b" d="M19.56 15.67A2.38 2.38 0 0 1 18 15.2l-2.67-1.33a3.12 3.12 0 0 1-1.1-.85l-.4-.48a7.11 7.11 0 0 1-2.74-1.27l-.55-.41a6.41 6.41 0 0 1-1.3-1.22l-1.26-1.59a2.38 2.38 0 0 1-.25-2.46l.92-2.12a2.38 2.38 0 0 1 2.23-1.39c5.07.08 9.19 4.2 9.27 9.27a2.38 2.38 0 0 1-1.39 2.23l-2.12.92Z"/></svg>
        Dashboard de Logs IoT
      </h1>
      <a href="/" class="text-gray-300 bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg text-sm shadow transition-all">🔄 Atualizar</a>
    </div>
    {% for nome, log in logs %}
      <div class="bg-gray-900 rounded-xl mb-6 shadow-lg border border-gray-800 overflow-hidden">
        <div class="flex items-center px-5 py-3 border-b border-gray-800 bg-gray-800">
          <span class="font-bold text-green-400 mr-2">●</span>
          <span class="font-semibold text-gray-100 text-lg">{{nome}}</span>
        </div>
        <pre class="text-gray-200 text-sm px-5 py-4 overflow-x-auto leading-tight max-h-96 bg-gray-950">{{log}}</pre>
      </div>
    {% endfor %}
  </div>
</body>
</html>
"""

GATEWAY_LOG = "gateway_core/gateway.log"
BLE_LOG = "/tmp/ble_scanner.log"
CONTAINERS = [
    ("sensor_gateway", "Gateway Ruby"),
    ("mosquitto", "Mosquitto MQTT"),
    ("gateway_iot_watchdog", "Watchdog Docker")
]

@app.route("/")
def index():
    logs = []

    # Gateway Ruby
    try:
        with open(GATEWAY_LOG) as f:
            lines = f.readlines()[-50:]
            log = ''.join(lines)
    except Exception as e:
        log = f"Erro: {str(e)}"
    logs.append(("Gateway Ruby", log))

    # BLE Scanner
    try:
        if os.path.exists(BLE_LOG):
            with open(BLE_LOG) as f:
                lines = f.readlines()[-40:]
                log = ''.join(lines)
        else:
            log = "Ficheiro de log não encontrado (BLE Scanner não iniciado?)"
    except Exception as e:
        log = f"Erro: {str(e)}"
    logs.append(("BLE Scanner (sudo python3)", log))

    # Logs dos containers Docker
    for container, nice_name in CONTAINERS:
        try:
            log = subprocess.check_output(
                ["docker", "logs", "--tail", "40", container],
                stderr=subprocess.STDOUT
            ).decode("utf-8")
        except Exception as e:
            log = f"Erro: {str(e)}"
        logs.append((nice_name, log))

    return render_template_string(TEMPLATE, logs=logs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
