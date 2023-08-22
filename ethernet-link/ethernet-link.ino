
#include <Ethernet.h>
#include <Adafruit_Fingerprint.h>

byte mac[] = { 0xA8, 0x61, 0x0A, 0xAE, 0x3A, 0xC4 };
EthernetServer server(80);

SoftwareSerial mySerial(2,3);
Adafruit_Fingerprint finger(&mySerial);

void setup()
{
 
  Serial.begin(115200);
  Serial.println("----------------------------------------------------------------");
   server.begin();
  Ethernet.begin(mac);

  Serial.println(Ethernet.localIP());

  finger.begin(57600);
  delay(5);
  
  if (finger.verifyPassword()) {
    Serial.println(F("Found fingerprint sensor!"));
  } else {
    Serial.println(F("Fingerprint sensor not ready"));
    while(1) { delay(1); } // nonsense
  }
}

void loop()
{
  EthernetClient client = server.available();
  if (client) { 
    Serial.println("Client connected!");
    boolean currentLineIsBlank = true;
    while (client.connected()) {
      if (client.available()) { 
        char c = client.read(); 
        if (c == '\n' && currentLineIsBlank) {
          // check fingerprint
           uint8_t fingerprint_status = FINGERPRINT_NOFINGER;

          Serial.println(F("Place your fingerprint to confirm entry"));
          while (kggGetFingerprintID() != FINGERPRINT_OK) {
            delay(1000); // no need to run too fast
          }
          Serial.println(F("Fingerprint taken"));

          uint16_t return_id = 10000; // if fingerprint not found
          int search_code = kggSearchFinger();
          if ( search_code == -1) {
            Serial.print("Fingerprint found: ID #");
            return_id = finger.fingerID;
            Serial.println(return_id);
          } else if (search_code == -2) {
            Serial.println(F("Fingerprint not found"));
          }


          client.println("HTTP/1.1 200 OK");
          client.println("Content-Type: text/json");
          client.println("Connection: close");
          client.println();
          String res = String("{\"id\": \"") + String(return_id) + "\"}"; // {"id": "5"}
          char result[256] = {0};
          res.toCharArray(result, 256);

          client.write(result);
          // respond if the id is correct or false
          break;
          
        }
        if (c == '\n') {
          currentLineIsBlank = true;
        }
        else if (c != '\r') {
          currentLineIsBlank = false;
        }
      } 
    } 
    delay(1);      
    client.stop(); 
    Serial.println("Client disconnected!");
  }
}

uint8_t kggGetFingerprintID() {
  uint8_t p = finger.getImage();
  switch (p) {
    case FINGERPRINT_OK:
      Serial.println(F("Image taken"));
      break;
    case FINGERPRINT_NOFINGER:
      Serial.println(F("No finger detected"));
      delay(2000);
      return p;
    case FINGERPRINT_PACKETRECIEVEERR:
      Serial.println("Communication error");
      return p;
    case FINGERPRINT_IMAGEFAIL:
      Serial.println("Imaging error");
      return p;
    default:
      Serial.println("Unknown error");
      return p;
  }

  // OK success!

  p = finger.image2Tz();
  switch (p) {
    case FINGERPRINT_OK:
      Serial.println(F("Image converted"));
      break;
    case FINGERPRINT_IMAGEMESS:
      Serial.println(F("Image too messy"));
      return p;
    case FINGERPRINT_PACKETRECIEVEERR:
      Serial.println(F("Communication error"));
      return p;
    case FINGERPRINT_FEATUREFAIL:
      Serial.println(F("Could not find fingerprint features"));
      return p;
    case FINGERPRINT_INVALIDIMAGE:
      Serial.println("Could not find fingerprint features");
      return p;
    default:
      Serial.println("Unknown error");
      return p;
  }

  // OK converted!

  return p;
}

int kggSearchFinger() {
  uint8_t p = finger.fingerSearch();
  if (p == FINGERPRINT_OK) {
    Serial.println("Found a print match!");
  } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
    Serial.println("Communication error");
    return p;
  } else if (p == FINGERPRINT_NOTFOUND) {
    Serial.println("Did not find a match");
    return -2;
  } else {
    Serial.println("Unknown error");
    return p;
  }

  // found a match!
  Serial.print("Found ID #"); Serial.print(finger.fingerID);
  Serial.print(" with confidence of "); Serial.println(finger.confidence);

  return -1;
}