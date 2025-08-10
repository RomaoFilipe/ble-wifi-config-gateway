# cron_worker/lib/tasks/irrigation_scheduler.rake
require_relative "../../models"        # para usar Sensor, IrrigationSchedule, helpers (ensure_irrigation_in_rails!, create_irrigation_log)
require_relative "../mqtt_publisher"   # usa MqttPublisher.send_command

namespace :irrigation do
  desc "Executa agendamentos do minuto atual (day_of_week/hour/minute) se ainda não correram hoje"
  task :run do
    now = (defined?(Time.zone) && Time.zone) ? Time.zone.now : Time.now
    puts "⏰ #{now.strftime('%Y-%m-%d %H:%M')} — verificar agendamentos..."

    schedules = IrrigationSchedule
                  .where(hour: now.hour, minute: now.min, day_of_week: now.wday)
                  .where("executed_at IS NULL OR DATE(executed_at) <> CURRENT_DATE")

    if schedules.empty?
      puts "📭 Nenhum agendamento para este minuto."
      next
    end

    schedules.find_each do |schedule|
      begin
        sensor = schedule.sensor
        if sensor.nil?
          puts "⚠️ Sensor não encontrado para agendamento #{schedule.id}"
          next
        end

        # Apenas sensores de irrigação
        unless sensor.sensor_type.to_s.downcase == "irrigation"
          puts "⏭️ Agendamento #{schedule.id}: sensor #{sensor.id} é '#{sensor.sensor_type}', não 'irrigation'"
          next
        end

        # Duração segura
        duration = (schedule.duration || schedule.try(:seconds) || 60).to_i
        duration = 60 if duration <= 0

        # Reforçar identify no Rails (não falha o ciclo se erro)
        begin
          ensure_irrigation_in_rails!(sensor.device_id)
        rescue => e
          puts "⚠️ identify falhou para #{sensor.device_id}: #{e.class} #{e.message}"
        end

        # Publicar comando e registar log
        puts "💧 Enviando irrigação para #{sensor.device_id} (#{duration}s)"
        MqttPublisher.send_command(sensor.device_id, duration)
        create_irrigation_log(sensor, duration, status: "agendado")

        # Marcar como executado hoje
        schedule.update!(executed_at: now)
        puts "✅ Schedule #{schedule.id} → START #{duration}s no #{sensor.device_id}"
      rescue => e
        puts "❌ Falha no schedule #{schedule.id}: #{e.class} #{e.message}"
        # não marca executed_at; voltará a tentar se ainda coincidir
      end
    end
  end
end
