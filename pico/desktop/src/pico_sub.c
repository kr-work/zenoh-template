// キー式に一致するデータを受け取って表示する。
//   ./build/pico_sub -e tcp/127.0.0.1:7447 -k 'demo/**'
#include "app_common.h"

static volatile int g_received = 0;

// 受信のたびに zenoh-pico の受信タスクから呼ばれる。重い処理はここでしない。
static void on_sample(z_loaned_sample_t *sample, void *ctx) {
    (void)ctx;
    z_view_string_t key;
    z_keyexpr_as_view_string(z_sample_keyexpr(sample), &key);
    z_owned_string_t value;
    z_bytes_to_string(z_sample_payload(sample), &value);
    printf("<- %.*s: %.*s\n", (int)z_string_len(z_loan(key)), z_string_data(z_loan(key)),
           (int)z_string_len(z_loan(value)), z_string_data(z_loan(value)));
    z_drop(z_move(value));
    g_received++;
}

int main(int argc, char **argv) {
    app_args_t args = {.key = "demo/hello/**", .count = 0};
    app_parse_args(argc, argv, &args);

    z_owned_session_t s;
    if (app_open_session(&s, &args) != 0) {
        return 1;
    }

    z_view_keyexpr_t ke;
    if (z_view_keyexpr_from_str(&ke, args.key) < 0) {
        fprintf(stderr, "'%s' is not a valid key expression\n", args.key);
        z_drop(z_move(s));
        return 1;
    }

    // コールバックは「クロージャー」に包んで渡す(第 3 引数は破棄時に呼ぶ関数、第 4 引数は ctx)
    z_owned_closure_sample_t callback;
    z_closure(&callback, on_sample, NULL, NULL);
    z_owned_subscriber_t sub;
    if (z_declare_subscriber(z_loan(s), &sub, z_loan(ke), z_move(callback), NULL) < 0) {
        fprintf(stderr, "Unable to declare subscriber\n");
        z_drop(z_move(s));
        return 1;
    }
    printf("subscribe: '%s'  (Ctrl+C で終了)\n", args.key);

    while (args.count == 0 || g_received < args.count) {
        z_sleep_ms(100);
    }

    z_drop(z_move(sub));
    z_drop(z_move(s));
    return 0;
}
