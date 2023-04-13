#include <pgmspace.h>

#define THINGNAME ""

// MQTT topics for the device
#define AWS_IOT_PUBLISH_TOPIC ""
#define AWS_IOT_SUBSCRIBE_TOPIC ""

const char WIFI_SSID[] = "";
const char WIFI_PASSWORD[] = "";
const char AWS_IOT_ENDPOINT[] = "";

const char* ntpServer1 = "pool.ntp.org";
const char* ntpServer2 = "time.nist.gov";

// Example:
// UTC -5.00 : -5 * 60 * 60 : -18000
// UTC +1.00 : 1 * 60 * 60 : 3600
// UTC +0.00 : 0 * 60 * 60 : 0
const long gmtOffset_sec = -18000;

// If conutry observes Daylight Saving, set to 3600; Otherwise, 0
const int daylightOffset_sec = 3600;

// ADC Default Pin to read
float voltage = 0.0;
int16_t ADC;

// Amazon Root CA 1 (AmazonRootCA1.pem)
static const char AWS_CERT_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
-----END CERTIFICATE-----
)EOF";

// Device Certificate (...-certificate.pem.crt)
static const char AWS_CERT_CRT[] PROGMEM = R"KEY(
-----BEGIN CERTIFICATE-----
-----END CERTIFICATE-----
)KEY";

// Device Private Key (...-private.pem.key)
static const char AWS_CERT_PRIVATE[] PROGMEM = R"KEY(
-----BEGIN RSA PRIVATE KEY-----
-----END RSA PRIVATE KEY-----
)KEY";
