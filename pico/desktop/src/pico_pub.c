// 1 秒ごとに文字列を publish する。
//   ./build/pico_pub -e tcp/127.0.0.1:7447
#include "app_common.h"

int main(int argc, char **argv) {
    app_args_t args = {.key = "demo/hello/pico", .count = 0};
    app_parse_args(argc, argv, &args);

    z_owned_session_t s;
    if (app_open_session(&s, &args) != 0) {
        return 1;
    }

    // キー式は文字列から「ビュー」を作って渡す(コピーしない)
    z_view_keyexpr_t ke;
    if (z_view_keyexpr_from_str(&ke, args.key) < 0) {
        fprintf(stderr, "'%s' is not a valid key expression\n", args.key);
        z_drop(z_move(s));
        return 1;
    }

    z_owned_publisher_t pub;
    if (z_declare_publisher(z_loan(s), &pub, z_loan(ke), NULL) < 0) {
        fprintf(stderr, "Unable to declare publisher\n");
        z_drop(z_move(s));
        return 1;
    }
    printf("publish: '%s'  (Ctrl+C で終了)\n", args.key);

    char buf[128];
    for (int i = 0; args.count == 0 || i < args.count; i++) {
        snprintf(buf, sizeof(buf), "[%4d] Hello from zenoh-pico", i);
        // ペイロードは z_owned_bytes_t に入れ、z_move で所有権ごと put に渡す
        z_owned_bytes_t payload;
        z_bytes_copy_from_str(&payload, buf);
        z_publisher_put(z_loan(pub), z_move(payload), NULL);
        printf("-> %s: %s\n", args.key, buf);
        z_sleep_s(1);
    }

    // 宣言したものは逆順に破棄する
    z_drop(z_move(pub));
    z_drop(z_move(s));
    return 0;
}
