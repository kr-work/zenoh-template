// 問い合わせ(get)に応答する。マイコンが自分の状態を返す用途を想定している。
//   ./build/pico_queryable -e tcp/127.0.0.1:7447
//   (別端末で) uv run get.py -s 'demo/info/**'
#include "app_common.h"

static volatile int g_queries = 0;

// ctx には main で作ったキー式(このキューリブルのキー)へのポインターを渡している
static void on_query(z_loaned_query_t *query, void *ctx) {
    const z_view_keyexpr_t *own_key = (const z_view_keyexpr_t *)ctx;

    z_view_string_t key;
    z_keyexpr_as_view_string(z_query_keyexpr(query), &key);
    printf("<- query: %.*s\n", (int)z_string_len(z_loan(key)), z_string_data(z_loan(key)));

    char buf[64];
    snprintf(buf, sizeof(buf), "pico queryable, queries=%d", g_queries + 1);
    z_owned_bytes_t reply;
    z_bytes_copy_from_str(&reply, buf);
    // 応答のキーは問い合わせのキー式と重なっていればよい。ここでは自分のキー(例: demo/info/pico)で返す
    z_query_reply(query, z_loan(*own_key), z_move(reply), NULL);
    g_queries++;
}

int main(int argc, char **argv) {
    app_args_t args = {.key = "demo/info/pico", .count = 0};
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

    z_owned_closure_query_t callback;
    z_closure(&callback, on_query, NULL, (void *)&ke);
    z_owned_queryable_t qable;
    if (z_declare_queryable(z_loan(s), &qable, z_loan(ke), z_move(callback), NULL) < 0) {
        fprintf(stderr, "Unable to declare queryable\n");
        z_drop(z_move(s));
        return 1;
    }
    printf("queryable: '%s'  (Ctrl+C で終了)\n", args.key);

    while (args.count == 0 || g_queries < args.count) {
        z_sleep_ms(100);
    }
    // 最後の応答が送り出されるまで少し待ってから閉じる
    z_sleep_ms(200);

    z_drop(z_move(qable));
    z_drop(z_move(s));
    return 0;
}
