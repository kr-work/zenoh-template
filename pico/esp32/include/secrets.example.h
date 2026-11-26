// このファイルを secrets.h という名前でコピーして、値を書き換える。
// secrets.h は .gitignore に入っているので、リポジトリには含まれない。
#pragma once

#define WIFI_SSID "your-ssid"
#define WIFI_PASS "your-password"

// Zenoh ルーター(zenohd や zenoh-bridge-ros2dds)のアドレス。
// 空文字列 "" にすると、UDP マルチキャストで同じ LAN のルーターを探す。
#define ZENOH_CONNECT "tcp/192.168.1.10:7447"
