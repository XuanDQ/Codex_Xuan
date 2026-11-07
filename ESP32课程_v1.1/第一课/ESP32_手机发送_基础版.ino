// 第一课：Android -> Classic Bluetooth SPP -> ESP32 -> USB Serial -> computer.
// For the original ESP32 with Classic Bluetooth support; not ESP32-C3/S3.
// No hardware/compiler validation was performed in the video production environment.
#include "BluetoothSerial.h"
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled for this target
#endif
#if !defined(CONFIG_BT_SPP_ENABLED)
#error Classic Bluetooth SPP is not available for this target
#endif
BluetoothSerial BT;

void setup() {
  Serial.begin(9600);
  // Check current board-package examples and phone prompts for pairing behavior.
  // Do not copy the old slide's BT.pinCode call without checking its API/version.
  if (!BT.begin("ESP32_Group3")) {
    Serial.println("Bluetooth start failed");
  }
}

void loop() {
  if (BT.available() > 0) {
    // Basic teaching version: may wait for timeout; message boundaries are not guaranteed.
    String message = BT.readString();
    Serial.println(message);
  }
}
