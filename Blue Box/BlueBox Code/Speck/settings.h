float SampleRate = 3200; // any positive value can be used, but will be converted to 3200/2^n where n = 0 .. 16
byte Range = 8; // possible values are: 2, 4, 8, 16
static const int num_networks = 2;
static const char* const ssid[num_networks] = {"iiNet520A2B", "SHL"};
static const char* const password[num_networks] = {"REH25Q4YEHNYKG7", "reliability"};
IPAddress ips[num_networks] = { {10,1,1,154}, {192,168,0,48} };
int send_port = 5005;
