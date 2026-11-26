// アプリの設定(キー名やピン番号)。Wi-Fi の情報は secrets.h に書く。
#pragma once

// 1 秒ごとに状態(JSON)を publish するキー
#define KEY_STATUS "demo/hello/esp32"

// "on" / "off" を受け取って LED を切り替えるキー
#define KEY_LED "demo/esp32/led"

// LED をつないだ GPIO。多くの ESP32 DevKit は GPIO2 にオンボード LED がある
#define LED_PIN 2

#define STATUS_INTERVAL_MS 1000
