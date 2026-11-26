// サンプル共通の引数処理とセッションの開始。
//
//   -m MODE      client(既定) または peer
//   -e ENDPOINT  接続先(例: tcp/127.0.0.1:7447)。省略するとマルチキャストでルーターを探す
//   -l ENDPOINT  待ち受けアドレス(peer モードで使う。例: udp/224.0.0.123:7447#iface=eth0)
//   -k KEY       キー式
//   -n COUNT     送信・受信の回数(0 なら無限)
//
// Windows でもビルドできるよう、getopt や unistd.h は使わない。
#ifndef ZENOH_TEMPLATE_APP_COMMON_H
#define ZENOH_TEMPLATE_APP_COMMON_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zenoh-pico.h>

typedef struct {
    const char *mode;
    const char *connect;
    const char *listen;
    const char *key;
    int count;
} app_args_t;

static void app_usage(const char *prog) {
    fprintf(stderr, "usage: %s [-m client|peer] [-e ENDPOINT] [-l ENDPOINT] [-k KEY] [-n COUNT]\n", prog);
}

static void app_parse_args(int argc, char **argv, app_args_t *args) {
    for (int i = 1; i < argc; i++) {
        const char *opt = argv[i];
        if (i + 1 >= argc) {
            app_usage(argv[0]);
            exit(1);
        }
        const char *val = argv[++i];
        if (strcmp(opt, "-m") == 0) {
            args->mode = val;
        } else if (strcmp(opt, "-e") == 0) {
            args->connect = val;
        } else if (strcmp(opt, "-l") == 0) {
            args->listen = val;
        } else if (strcmp(opt, "-k") == 0) {
            args->key = val;
        } else if (strcmp(opt, "-n") == 0) {
            args->count = atoi(val);
        } else {
            app_usage(argv[0]);
            exit(1);
        }
    }
}

// 設定を組み立ててセッションを開く。成功なら 0。
// zenoh-pico 1.x では、マルチスレッド版ならば受信やキープアライブのタスクが z_open の中で自動的に始まる。
static int app_open_session(z_owned_session_t *session, const app_args_t *args) {
    z_owned_config_t config;
    z_config_default(&config);
    if (args->mode != NULL) {
        zp_config_insert(z_loan_mut(config), Z_CONFIG_MODE_KEY, args->mode);
    }
    if (args->connect != NULL) {
        zp_config_insert(z_loan_mut(config), Z_CONFIG_CONNECT_KEY, args->connect);
    }
    if (args->listen != NULL) {
        zp_config_insert(z_loan_mut(config), Z_CONFIG_LISTEN_KEY, args->listen);
    }
    printf("Opening session (mode=%s, connect=%s)...\n", args->mode ? args->mode : "client",
           args->connect ? args->connect : "(scouting)");
    if (z_open(session, z_move(config), NULL) < 0) {
        fprintf(stderr, "Unable to open session. ルーターが起動しているか、接続先が正しいか確認してください。\n");
        return -1;
    }
    return 0;
}

#endif
