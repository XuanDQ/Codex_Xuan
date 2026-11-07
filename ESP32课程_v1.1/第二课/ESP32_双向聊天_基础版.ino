// 教学基础版：原版ESP32 + Bluetooth Classic SPP + Android。
// 不适用于ESP32-C3/S3。没有连接硬件实测；请先核对板包官方示例。
// readString()可能等待超时，且不保证一次读到完整消息。
// 手机基础版读当前缓存；进阶项目请使用双方一致的消息边界和缓存解析。
#include "BluetoothSerial.h"
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled for this target
#endif
#if !defined(CONFIG_BT_SPP_ENABLED)
#error Classic Bluetooth SPP is unavailable on this target
#endif
BluetoothSerial BT;

void setup() {
  Serial.begin(9600);
  // 配对方式依当前Arduino-ESP32版本的官方示例与手机提示。
  // 不使用旧课件中需要核对版本的BT.pinCode接口。
  if (!BT.begin("ESP32_Classroom")) {
    Serial.println("Bluetooth start failed");
  }
}

void loop() {
  if (BT.available() > 0) {
    String msg = BT.readString();
    Serial.print("对方: ");
    Serial.println(msg);
  }
  if (Serial.available() > 0) {
    String msg = Serial.readString();
    Serial.print("我: ");
    Serial.println(msg);
    BT.println(msg);
  }
}
