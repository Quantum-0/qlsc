#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <ArduinoOTA.h>
#include "led_strip_control.h"

static char ota_status = 0;

void ota_init()
{
    //ArduinoOTA.setHostname(host);
    ArduinoOTA.onStart([]() { // switch off all the PWMs during upgrade
        strip.fill(0);
        strip.setPixelColor(0, 0x4400FF);
        strip.show();
    });

    ArduinoOTA.onEnd([]() { // do a fancy thing with our board led at end
        strip.fill(0);
        strip.setPixelColor(0, 0x0077FF);        
        strip.show();
    });

    ArduinoOTA.onError([](ota_error_t error) {
        (void)error;
        ESP.restart();
    });

    /* setup the OTA server */
    ArduinoOTA.begin();
}

void ota_loop()
{
    ArduinoOTA.handle();
}