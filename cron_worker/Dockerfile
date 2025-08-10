FROM ruby:3.2

ENV TZ=Europe/Lisbon

WORKDIR /app

# Dependências para pg + TZ
RUN apt-get update -qq && apt-get install -y build-essential libpq-dev tzdata nodejs && rm -rf /var/lib/apt/lists/*

# Bundle com cache
COPY cron_worker/Gemfile cron_worker/Gemfile.lock ./
RUN gem install bundler && \
    bundle config set path /usr/local/bundle && \
    bundle install --jobs 4

# Código
COPY cron_worker/Rakefile Rakefile
COPY cron_worker/models.rb models.rb
COPY cron_worker/lib lib

# Loop por defeito (podes mudar para ruby models.rb se quiseres o loop contínuo)
# Aqui vamos de loop contínuo já no models.rb, por isso:
CMD ["ruby", "models.rb"]
