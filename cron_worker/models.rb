# cron_worker/models.rb
require "logger"
require "json"
require "time"
require "net/http"

require "active_record"
require "pg"
require "mqtt"

# Se quiseres usar Time.zone, carrega ActiveSupport
require "active_support"
require "active_support/time"
require "active_support/core_ext/object/blank"


LOGGER = Logger.new($stdout)

# =========================
# ⏱️ Timezone
# =========================
tz = ENV["TZ"].presence || "Europe/Lisbon"
Time.zone = tz
LOGGER.info "🕒 Timezone: #{Time.zone.name}"

# =========================
# 🔌 LIGAÇÃO À BASE DE DADOS
# =========================
def establish_db!
  db_url = ENV["DATABASE_URL"]
  raise "DATABASE_URL em falta" if db_url.nil? || db_url.empty?

  # Mantém simples: a URL já deve trazer sslmode=require quando necessário
  ActiveRecord::Base.establish_connection(db_url)
  ActiveRecord::Base.logger = LOGGER
  LOGGER.info "✅ Ligado à BD"
end

# =========================
# 🗄️ MODELOS (sem STI)
# =========================
class Sensor < ActiveRecord::Base
  self.table_name = "sensors"
  self.inheritance_column = :_type_disabled
  has_many :irrigation_schedules, foreign_key: :sensor_id
  has_many :irrigation_logs, foreign_key: :sensor_id
end

class IrrigationSchedule < ActiveRecord::Base
  self.table_name = "irrigation_schedules"
  belongs_to :sensor, foreign_key: :sensor_id
end

class IrrigationLog < ActiveRecord::Base
  self.table_name = "irrigation_logs"
  belongs_to :sensor, foreign_key: :sensor_id, optional: true
end

# =========================
# 🌐 Rails API (para identify e logs)
# =========================
API_URL   = ENV.fetch("RAILS_API_URL") # ex.: http://13.48.48.4:3000
API_TOKEN = ENV.fetch("API_TOKEN")

def http_get(url)
  uri = URI(url)
  req = Net::HTTP::Get.new(uri)
  req["Authorization"] = "Bearer #{API_TOKEN}"

  Net::HTTP.start(uri.host, uri.port, open_timeout: 5, read_timeout: 8) do |http|
    http.request(req)
  end
rescue => e
  LOGGER.warn "⚠️ HTTP GET falhou: #{e.class} #{e.message} (#{url})"
  nil
end

def http_post_json(url, body_hash)
  uri = URI(url)
  req = Net::HTTP::Post.new(uri)
  req["Content-Type"]  = "application/json"
  req["Authorization"] = "Bearer #{API_TOKEN}"
  req.body = JSON.dump(body_hash)

  Net::HTTP.start(uri.host, uri.port, open_timeout: 5, read_timeout: 8) do |http|
    http.request(req)
  end
rescue => e
  LOGGER.error "❌ HTTP POST falhou: #{e.class} #{e.message} (#{url})"
  nil
end

def ensure_irrigation_in_rails!(device_id)
  url = "#{API_URL}/api/sensors/identify?device_id=#{device_id}&sensor_type=irrigation"
  res = http_get(url)
  if res && res.code.to_i.between?(200,299)
    LOGGER.info "🔎 identify OK para #{device_id} (#{res.code})"
  else
    LOGGER.warn "⚠️ identify NOK para #{device_id} (#{res&.code || 'sem resposta'})"
  end
end

def create_irrigation_log(sensor, duration, status: "agendado")
  payload = {
    device_id:   sensor.device_id,
    executed_at: Time.zone.now.utc.iso8601,
    duration:    duration.to_i,
    status:      status
  }
  res = http_post_json("#{API_URL}/api/irrigation_logs", payload)
  if res && res.code.to_i.between?(200,299)
    LOGGER.info "📝 Log Rails (#{res.code}) #{res.body.to_s[0,120]}..."
  else
    LOGGER.warn "⚠️ Falha ao criar log em Rails (#{res&.code || 'sem resposta'})"
  end
end

# =========================
# 📡 MQTT
# =========================
MQTT_HOST = ENV.fetch("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = ENV.fetch("MQTT_PORT", "1883").to_i

def with_mqtt
  MQTT::Client.connect(host: MQTT_HOST, port: MQTT_PORT) do |c|
    yield c
  end
rescue => e
  LOGGER.error "❌ MQTT erro: #{e.class} #{e.message}"
  sleep 3
  retry
end

def publish_start(device_id, duration, origin: "schedule")
  payload = { action: "start", duration: duration.to_i, origin: origin }
  topic   = "sensors/irrigation/#{device_id}/command"
  with_mqtt { |c| c.publish(topic, payload.to_json) }
  LOGGER.info "📤 MQTT → #{topic} | #{payload}"
end

# =========================
# 🧠 LÓGICA do WORKER
# =========================
def process_due_schedules!
  now = Time.zone.now

  due = IrrigationSchedule
          .where(hour: now.hour, minute: now.min, day_of_week: now.wday)
          .where("executed_at IS NULL OR DATE(executed_at) <> CURRENT_DATE")

  return if due.empty?

  due.find_each do |sch|
    begin
      sensor = sch.sensor
      unless sensor
        LOGGER.warn "⚠️ Schedule #{sch.id} sem sensor associado"
        next
      end

      if sensor.sensor_type.to_s.downcase != "irrigation"
        LOGGER.info "⏭️ Schedule #{sch.id}: sensor #{sensor.id} é '#{sensor.sensor_type}', não 'irrigation'"
        next
      end

      duration = (sch.try(:duration) || sch.try(:seconds) || 60).to_i
      duration = 60 if duration <= 0

      begin
        ensure_irrigation_in_rails!(sensor.device_id)
      rescue => e
        LOGGER.warn "⚠️ identify falhou para #{sensor.device_id}: #{e.class} #{e.message}"
      end

      publish_start(sensor.device_id, duration, origin: "schedule")
      create_irrigation_log(sensor, duration, status: "agendado")

      sch.update!(executed_at: now)
      LOGGER.info "✅ Schedule #{sch.id} → START #{duration}s no #{sensor.device_id}"
    rescue => e
      LOGGER.error "❌ Falha no schedule #{sch.id}: #{e.class} #{e.message}"
      # Não marca executed_at; volta a tentar em execuções futuras se ainda coincidir
    end
  end
end

# =========================
# ▶️ MAIN LOOP
# =========================
establish_db!

loop do
  begin
    process_due_schedules!
  rescue => e
    LOGGER.error "❌ Loop erro (process_due_schedules!): #{e.class} #{e.message}"
  end
  sleep 5
end
