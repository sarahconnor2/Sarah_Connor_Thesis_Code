/*
 * Authors: Ben Travaglione, Praveen Sundaram 
 * Created : 31/01/17
 * Modified : 12/09/17
 * 
 * Collects instantaneous data from ADXL345
 * and sends transmits the collected data via
 * WiFi using the UDP protocol
 */

#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include "ADXL345_OGRAFF_MODIFIED.h"
#include "Crypto.h"
#include "CryptoLW.h"
#include "Acorn128.h"
#include "utility/ProgMemUtil.h"

#include <sys/time.h>


#include "NTP.h"
#include "settings.h"
/* settings.h should contain something like:
float SampleRate = 3200; // any positive value can be used, but will be converted to 3200/2^n where n = 0 .. 16
byte Range = 8; // possible values are: 2, 4, 8, 16
static const int num_networks = 2;
static const char* const ssid[num_networks] = {"smartMEMS", "SSID"};
static const char* const password[num_networks] = {"33AD1F6DCD", "password"};
IPAddress ips[num_networks] = { {10,3,1,2}, {192,168,0,23} };
int send_port = 5005;
 */

#define verbose false
#define BLUE_LED 2
#define CHIP_SELECT 5

IPAddress ip;

WiFiUDP UDP;
unsigned int localUDPPort = 4210;  // local port to listen on

uint8_t fifo_before, fifo_after = 0;
uint8_t WaterMark = 22;

Accelerometer accel(CHIP_SELECT);
int16_t ax, ay, az;
byte mac[6];
byte dataPacket[6 + 8 + 4 + 96 + 4 + 4 + 1 + 5];
byte enc_dataPacket[144];
struct timeval start, stop;
double secs = 0;
int repeat = 0;

unsigned long packet_num = 0;
float nominal_sample_rate = 0;
/*
 * Each datapacket is 123 bytes long
 * 
 * mac address : 6 bytes
 * ntp timestamp : 8 bytes
 * microseconds since timestamp : 4 bytes
 * 3 (axes) x 2 bytes (16-bit) x 16 values : 96 bytes
 * packet_num : 4 byte
 * nominal_sample_rate : 4 bytes
 * range : 1 byte
 */
char macString[20] = {0};

unsigned long StartTime = 0;
unsigned long ElapsedTime = 0;
unsigned long LastTime = 0;

byte key[16] = {0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
               0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c};

size_t size = 128;

Acorn128 cipher;


void setup() {

  pinMode(BLUE_LED, OUTPUT);
  WiFi.mode(WIFI_STA);
  WiFi.macAddress(mac);
  sprintf(macString,"%02X:%02X:%02X:%02X:%02X:%02X",mac[0],mac[1],mac[2],mac[3],mac[4],mac[5]);

  delay(100);
  Serial.begin(115200);
  Serial.println("Begin Setup");    
  Serial.print("Mac Address of device : ");
  Serial.println(macString);
  Serial.println("Attempting to connect to a network ....");
  byte numSsid = WiFi.scanNetworks();
  Serial.print("Found ");
  Serial.print(numSsid);
  Serial.println(" networks.");
  for (int thisNet = 0; thisNet<numSsid; thisNet++) {
    Serial.println(WiFi.SSID(thisNet));
    for (int n = 0; n < num_networks; n++) {
      if (WiFi.SSID(thisNet) == ssid[n]) {
        WiFi.begin(ssid[n], password[n]);
        ip = ips[n];
        goto wifi_done;
      }
    }
  }

  wifi_done:
  while (WiFi.status() != WL_CONNECTED)
  {
    digitalWrite(BLUE_LED, LOW);
    delay(200);
    digitalWrite(BLUE_LED, HIGH);
    delay(200);
    Serial.print(".");
}
  
  digitalWrite(BLUE_LED, LOW);

  Serial.println("Connected!");
  Serial.print("Sending UDP packets to ");
  Serial.print(ip);
  Serial.print(":");
  Serial.println(send_port);

  unsigned long epoch = 0;
  unsigned long fraction_sec = 0;
  ntp_sync(epoch,fraction_sec);
  memcpy(dataPacket+6,&epoch,4);
  memcpy(dataPacket+10,&fraction_sec,4);

  UDP.begin(localUDPPort);
  Serial.println("UDP begin");
  Serial.println("Initializing Accelerometer");
  initAccel();
  delay(500);
  
  memcpy(dataPacket,mac,6);
  //memcpy(dataPacket+6,&ntp_time,8);

  nominal_sample_rate = accel.getRate();
  memcpy(dataPacket+118,&nominal_sample_rate,4);

  memcpy(dataPacket+122,&Range,1);

  Serial.println("End Setup");
  Serial.println("Ready to send data");
  //Clear some data from the FIFO
  for (int i = 0; i<16; i++) {
    accel.readAccel(&ax, &ay, &az);
  }
  StartTime = micros();

}


void initAccel() {
   
  if(!accel.powerOn()){
    Serial.println("ADXL345 not detected. Failed to initialize accelerometer");
    while(1);
  }
  else
  {
    Serial.println("Accelerometer initialized");
    delay(2000);
  }
  
  accel.setRangeSetting(Range);
  accel.setRate(SampleRate);
  accel.setFIFOMode(1);
  accel.setFullResBit(1);
  accel.setFIFOSampleSize(WaterMark);
 
  uint8_t rangeSetting = accel.getRangeSetting();
  float outputRate = accel.getRate();
  uint8_t FIFOMode = accel.getFIFOMode();
  uint8_t fullResBitStatus = accel.getFullResBit();
  uint8_t FIFOSampleSize = accel.getFIFOSampleSize();
  
  Serial.print("Range Setting: ");
  Serial.println(rangeSetting);
  Serial.print("Output Data Rate: ");
  Serial.println(outputRate);
  Serial.print("FIFO Mode: ");
  Serial.println(FIFOMode);
  Serial.print("Full Resolution Bit Status: ");
  Serial.println(fullResBitStatus);
  Serial.print("FIFO Sample Size: ");
  Serial.println(FIFOSampleSize);

}

void getAccel() {

  if (verbose) {
    Serial.println("Get acceleration");
  }

  unsigned long CurrentTime = micros();
  if (CurrentTime < LastTime) {
    //We have been running for long enough for the time to overflow
    unsigned long epoch = 0;
    unsigned long fraction_sec = 0;
    ntp_sync(epoch,fraction_sec);
    memcpy(dataPacket+6,&epoch,4);
    memcpy(dataPacket+10,&fraction_sec,4);
    packet_num = 0;
    StartTime = 0;
  }
  LastTime = CurrentTime;

  ElapsedTime = CurrentTime - StartTime;
  memcpy(dataPacket+14,&ElapsedTime,4);

  for (int i = 0; i<16; i++) {
    accel.readAccel(&ax, &ay, &az);
    memcpy(dataPacket+6*i+18,&ax,2);
    memcpy(dataPacket+6*i+18+2,&ay,2);
    memcpy(dataPacket+6*i+18+4,&az,2);    
  }

  packet_num += 1;
  memcpy(dataPacket+114,&packet_num,4);
}

uint8_t getrnd() {
    uint8_t really_random = *(volatile uint8_t *)0x3FF20E44;
    return really_random;
}

bool encryptData(Acorn128 *cipher)
{
    size_t posn, len;
    size_t inc = 128;
  
    byte iv[16] = {getrnd(),getrnd(),getrnd(),getrnd(),getrnd(),getrnd(),getrnd(),getrnd(),
                  getrnd(),getrnd(),getrnd(),getrnd(),getrnd(),getrnd(),getrnd(),getrnd()};
    
    cipher->clear();
    if (!cipher->setKey(key, cipher->keySize())) {
        Serial.print("setKey ");
        return false;
    }
    if (!cipher->setIV(iv, cipher->ivSize())) {
        Serial.print("setIV ");
        return false;
    }

    memset(enc_dataPacket, 0xBA, sizeof(enc_dataPacket));

    for (posn = 0; posn < size; posn += inc) {
        len = size - posn;
        if (len > inc)
            len = inc;
        cipher->encrypt(enc_dataPacket + posn, dataPacket + posn, len);
    }
    
    memcpy(enc_dataPacket + 128, &iv, 16);
}




void sendAccelData(){

  
  UDP.beginPacket(ip,send_port);
  UDP.write(enc_dataPacket,144);
  UDP.endPacket();
}

char serial_buff[100];
int short_delay = 100;

void loop() {
  // put your main code here, to run repeatedly:  
  

  
  uint8_t WaterMarkBit = accel.getIntWatermarkSource();

  if (WaterMarkBit == 1){

      fifo_before = accel.getNumFIFOEntries();
      getAccel();
      fifo_after = accel.getNumFIFOEntries();
      //sprintf(serial_buff, "FIFO before : %3d FIFO after : %3d packet : %10d", fifo_before, fifo_after, packet_num);
      //Serial.println(serial_buff);

      encryptData(&cipher);

      gettimeofday(&start, NULL);
      
      sendAccelData();

      gettimeofday(&stop, NULL);
      secs = (double)(stop.tv_usec - start.tv_usec) + (double)(stop.tv_sec - start.tv_sec)*1000000;
      Serial.println(secs);

  } else { delayMicroseconds(short_delay); }

 
  
}
