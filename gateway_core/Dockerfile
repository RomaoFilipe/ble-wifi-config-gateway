FROM ruby:3.2

WORKDIR /app

COPY . .

RUN gem install mqtt json net-http dotenv

CMD ["ruby", "sensor_gateway.rb"]
