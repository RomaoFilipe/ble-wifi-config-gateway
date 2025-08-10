require 'mqtt'
require 'json'

class MqttPublisher
  BROKER = ENV['MQTT_BROKER'] || 'sensor_gateway'
  PORT = (ENV['MQTT_PORT'] || 1883).to_i

  def self.send_command(device_id, duration)
    topic = "sensors/irrigation/#{device_id}/command"
    payload = {
      action: 'start',
      duration: duration
    }

    puts "📡 Enviando para MQTT -> tópico: #{topic} | duração: #{duration}s"

    MQTT::Client.connect(host: BROKER, port: PORT) do |client|
      client.publish(topic, payload.to_json)
    end
  rescue => e
    puts "❌ Erro ao enviar comando MQTT: #{e.message}"
  end
end
