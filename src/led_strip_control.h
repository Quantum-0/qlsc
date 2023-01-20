#pragma once
#include "Adafruit_NeoPixel.h"

int led_pin = 13;

Adafruit_NeoPixel strip = Adafruit_NeoPixel(1, 4, NEO_GRB + NEO_KHZ800);

void lsc_init()
{
    strip.begin();
    strip.setBrightness(255);
    strip.fill(0);
    strip.show();
}

void lsc_loop()
{
    bool odd_second = (millis() / 1000 % 2 == 0);
    bool odd_half_second = (millis() / 500 % 2 == 0);

    if (WiFi.status() == WL_CONNECTED) // Connected
        strip.setPixelColor(0, odd_second ? 0x001100 : 0);
    else if (WiFi.status() == WL_IDLE_STATUS) // Connecting
        strip.setPixelColor(0, odd_half_second ? 0xFFFF00 : 0);
    else if (WiFi.status() == WL_CONNECTION_LOST) // Lost connection
        strip.setPixelColor(0, odd_half_second ? 0xFF0000 : 0);
    else if (WiFi.status() == WL_CONNECT_FAILED) // Disconnected
        strip.setPixelColor(0, odd_second ? 0xFF0000 : 0);
    else if (WiFi.status() == WL_DISCONNECTED) // Disconnected
        strip.setPixelColor(0, 0xFF0000);
    else if (WiFi.status() == WL_NO_SSID_AVAIL) // Disconnected
        strip.setPixelColor(0, 0x0000FF);

    strip.show();
}

// TODO:
/*
Modes:
- color
- manual
- rainbow all
- rainbow cirle
- thunderstorm
- 3 points: R G B in different places
- 3 moving lines
*/