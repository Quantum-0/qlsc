#include <ESP8266WiFi.h>
#include "led_strip_control.h"
#include "protocol.h"
#include "ota.h"

#define WIFI_SSID "L0k1 Home" // "MGTS 70" //
#define WIFI_PSK  "dspdsp999" // "4953332195" //

const char* ssid = WIFI_SSID;
const char* password = WIFI_PSK;
const char* host = "OTA-LEDS";


void setup() {
  Serial.begin(115200);
  
  lsc_init();

  WiFi.mode(WIFI_STA);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    lsc_loop();
    delay(10);
  }

  ota_init();

  Udp.begin(localPort);
}

bool aaa = 0;
int d = 2;

void loop() {
  ota_loop();
  handle_udp();

  /*aaa = !aaa;
  d++;
  strip.fill(aaa?0:0xFFFFFF);
  strip.show();
  delay(d/25);*/

  // for(int i = 0; i < STRIP_LENGHT; i++)
  // {
  //   strip.setPixelColor(i, 0x190104);
  //   //strip.setPixelColor(i, 0x040119);
  //   if (i > 0)
  //     strip.setPixelColor(i-1, 0);
  //   strip.show();
  //   delay(3);
  // }
  // for(int i = 0; i < STRIP_LENGHT; i++)
  // {
  //   strip.setPixelColor(STRIP_LENGHT-i, 0x040119);
  //   if (i > 0)
  //     strip.setPixelColor(STRIP_LENGHT-i+1, 0);
  //   strip.show();
  //   delay(3);
  // }

  lsc_loop();
  delay(1);
}
