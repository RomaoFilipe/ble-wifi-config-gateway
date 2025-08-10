require 'dotenv/load'
require 'mqtt'
require 'json'
require 'net/http'

require 'logger'

logfile = File.open('gateway.log', 'a')
logfile.sync = true
logger = Logger.new(logfile)
logger.level = Logger::INFO

puts "🚀 Sensor Gateway a iniciar..."
logger.info "🚀 Sensor Gateway a iniciar..."


broker_host = ENV['MQTT_BROKER'] ||'localhost'
broker_port = (ENV['MQTT_PORT'] || 1883).to_i
api_url = ENV['API_URL']
token = ENV['API_TOKEN']

MQTT::Client.connect(host: broker_host, port: broker_port) do |client|
  puts "✅ Ligado ao broker MQTT! A escutar tópico: sensors/data"
  client.subscribe('sensors/data')

  client.get do |topic, message|
    puts "📥 Mensagem recebida no tópico #{topic}"

    begin
      data = JSON.parse(message)
      device_id = data['device_id']

      if device_id.nil?
        puts "⚠️ Dados sem device_id, ignorado."
        next
      end

      # 1. Procurar sensor pelo device_id
      uri_lookup = URI("#{api_url}/identify?device_id=#{device_id}")
      req_lookup = Net::HTTP::Get.new(uri_lookup)
      req_lookup['Authorization'] = "Bearer #{token}"
      res_lookup = Net::HTTP.start(uri_lookup.hostname, uri_lookup.port) { |http| http.request(req_lookup) }

      if res_lookup.code.to_i == 200
        sensor = JSON.parse(res_lookup.body)
        sensor_id = sensor["id"]

        # 2. Enviar leitura
        uri_post = URI("#{api_url}/#{sensor_id}/readings")
        req_post = Net::HTTP::Post.new(uri_post)
        req_post['Authorization'] = "Bearer #{token}"
        req_post['Content-Type'] = 'application/json'
        req_post.body = data.to_json

        res_post = Net::HTTP.start(uri_post.hostname, uri_post.port) { |http| http.request(req_post) }

        puts "📤 Dados enviados para sensor ##{sensor_id} (#{res_post.code})"
      else
        puts "❌ Sensor não encontrado (#{res_lookup.code})"
      end

    rescue => e
      puts "❌ Erro ao processar mensagem: #{e.message}"
    end
  end
end
