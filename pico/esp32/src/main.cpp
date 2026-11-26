// ESP32 + zenoh-pico のサンプル。
//   - KEY_STATUS に 1 秒ごとに状態(JSON)を publish する
//   - KEY_LED を購読し、"on" / "off" で LED を切り替える
//
// PC 側での確認(ルーターに接続した状態で):
//   uv run sub.py -e tcp/<ルーターのIP>:7447 -m client -k 'demo/hello/**'
//   uv run pub.py -e tcp/<ルーターのIP>:7447 -m client -k demo/esp32/led -p on -n 1 --raw
//
// 注意: PlatformIO の Arduino ESP32 ビルドでは zenoh-pico が C99 扱い(ZENOH_C_STANDARD=99)になり、
// z_loan / z_move / z_drop / z_closure といった汎用マクロが定義されない。
// そのため、z_session_loan(&s) のように型ごとの関数を直接呼んでいる。
#include <Arduino.h>
#include <WiFi.h>
#include <zenoh-pico.h>

#include "app_config.h"

#if __has_include("secrets.h")
#include "secrets.h"
#else
#error "include/secrets.example.h を include/secrets.h にコピーして、Wi-Fi の情報を書いてください"
#endif

static z_owned_session_t s;
static z_owned_publisher_t pub;
static z_owned_subscriber_t sub;
static uint32_t count = 0;

static void halt(const char *msg) {
    Serial.println(msg);
    while (true) {
        delay(1000);
    }
}

// zenoh-pico の受信タスクから呼ばれる。時間のかかる処理は置かない
static void on_led(z_loaned_sample_t *sample, void *ctx) {
    (void)ctx;
    z_owned_string_t value;
    z_bytes_to_string(z_sample_payload(sample), &value);
    const char *data = z_string_data(z_string_loan(&value));
    const size_t len = z_string_len(z_string_loan(&value));
    const bool on = (len == 2 && strncmp(data, "on", 2) == 0);
    digitalWrite(LED_PIN, on ? HIGH : LOW);
    Serial.printf("<- %s: %.*s\n", KEY_LED, (int)len, data);
    z_string_drop(z_string_move(&value));
}

static void connect_wifi() {
    Serial.printf("Connecting to Wi-Fi '%s'", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf(" OK (%s)\n", WiFi.localIP().toString().c_str());
}

void setup() {
    Serial.begin(115200);
    delay(500);
    pinMode(LED_PIN, OUTPUT);
    connect_wifi();

    // クライアントモードでルーターにつなぐ。ZENOH_CONNECT が空ならマルチキャストで探す
    z_owned_config_t config;
    z_config_default(&config);
    zp_config_insert(z_config_loan_mut(&config), Z_CONFIG_MODE_KEY, "client");
    if (strlen(ZENOH_CONNECT) > 0) {
        zp_config_insert(z_config_loan_mut(&config), Z_CONFIG_CONNECT_KEY, ZENOH_CONNECT);
    }

    Serial.print("Opening Zenoh session...");
    if (z_open(&s, z_config_move(&config), NULL) < 0) {
        halt(" failed. ルーターのアドレスと、PC 側のファイアウォール(7447/tcp)を確認してください");
    }
    Serial.println(" OK");

    z_view_keyexpr_t ke_status;
    z_view_keyexpr_from_str_unchecked(&ke_status, KEY_STATUS);
    if (z_declare_publisher(z_session_loan(&s), &pub, z_view_keyexpr_loan(&ke_status), NULL) < 0) {
        halt("Unable to declare publisher");
    }

    z_view_keyexpr_t ke_led;
    z_view_keyexpr_from_str_unchecked(&ke_led, KEY_LED);
    z_owned_closure_sample_t callback;
    z_closure_sample(&callback, on_led, NULL, NULL);
    if (z_declare_subscriber(z_session_loan(&s), &sub, z_view_keyexpr_loan(&ke_led), z_closure_sample_move(&callback),
                             NULL) < 0) {
        halt("Unable to declare subscriber");
    }
    Serial.printf("publish: %s / subscribe: %s\n", KEY_STATUS, KEY_LED);
}

void loop() {
    char buf[128];
    snprintf(buf, sizeof(buf), "{\"count\":%lu,\"uptime_ms\":%lu,\"rssi\":%d}", (unsigned long)count++,
             (unsigned long)millis(), (int)WiFi.RSSI());

    z_owned_bytes_t payload;
    z_bytes_copy_from_str(&payload, buf);
    if (z_publisher_put(z_publisher_loan(&pub), z_bytes_move(&payload), NULL) < 0) {
        Serial.println("publish failed");
    } else {
        Serial.printf("-> %s: %s\n", KEY_STATUS, buf);
    }
    delay(STATUS_INTERVAL_MS);
}
