const bleno = require('bleno');
const fs = require('fs');

const SERVICE_UUID = '13333333-3333-3333-3333-333333333337';
const CHAR_UUID    = '13333333-3333-3333-3333-333333330001';

class WifiConfigCharacteristic extends bleno.Characteristic {
  constructor() {
    super({
      uuid: CHAR_UUID,
      properties: ['write'],
      descriptors: [
        new bleno.Descriptor({
          uuid: '2901',
          value: 'Wi-Fi SSID & password configurator'
        })
      ]
    });
  }

  onWriteRequest(data, offset, withoutResponse, callback) {
    try {
      const msg = data.toString('utf8');
      console.log('🔔 Dados recebidos via BLE:', msg);
      const conf = JSON.parse(msg);
      const ssid = conf.ssid;
      const password = conf.password;
      if (ssid && password) {
        // Gravar para ficheiro temporário
        const payload = { ssid, password, timestamp: new Date().toISOString() };
        fs.writeFileSync('/tmp/ble_wifi.json', JSON.stringify(payload, null, 2));
        console.log('💾 SSID e password gravados em /tmp/ble_wifi.json');
      } else {
        console.log('❌ Formato inválido! Envia JSON: {"ssid":"xxx","password":"yyy"}');
      }
    } catch (err) {
      console.log('❌ Erro ao processar dados BLE:', err.message);
    }
    callback(this.RESULT_SUCCESS);
  }
}

const wifiConfigCharacteristic = new WifiConfigCharacteristic();

bleno.on('stateChange', (state) => {
  if (state === 'poweredOn') {
    console.log('🟢 BLE ativo, pronto para ligação via LightBlue/nRF Connect!');
    bleno.startAdvertising('IOT-Gateway', [SERVICE_UUID]);
  } else {
    console.log('🔴 BLE não ativo!');
    bleno.stopAdvertising();
  }
});

bleno.on('advertisingStart', (error) => {
  if (!error) {
    console.log('🚀 Publicidade BLE iniciada! Serviço disponível.');
    bleno.setServices([
      new bleno.PrimaryService({
        uuid: SERVICE_UUID,
        characteristics: [wifiConfigCharacteristic]
      })
    ]);
  } else {
    console.log('❌ Erro ao anunciar BLE:', error);
  }
});

// Sair limpo ao Ctrl+C
process.on('SIGINT', function() {
  console.log('\n🛑 A terminar serviço BLE...');
  bleno.stopAdvertising();
  process.exit();
});
