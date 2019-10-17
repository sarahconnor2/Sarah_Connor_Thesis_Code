#include "Arduino.h"
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

//This code is based on the NTP code from:
// https://github.com/esp8266/Arduino/blob/master/libraries/ESP8266WiFi/examples/NTPClient/NTPClient.ino


unsigned long sendNTPpacket(IPAddress& address);
void ntp_sync(unsigned long& epoch,unsigned long& fraction_sec);

