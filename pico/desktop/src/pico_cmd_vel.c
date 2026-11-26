// ROS 2 の geometry_msgs/msg/Twist を CDR に詰めて publish する。
// zenoh-bridge-ros2dds 経由で ROS 2 の /cmd_vel トピックに届く。
//
//   ./build/pico_cmd_vel -e tcp/127.0.0.1:7447            # キーは cmd_vel
//   ./build/pico_cmd_vel -e tcp/127.0.0.1:7447 -k bot1/cmd_vel   # ブリッジに namespace /bot1 を設定した場合
//
// ROS 2 側の確認:  ros2 topic echo /cmd_vel geometry_msgs/msg/Twist
#include <stdint.h>

#include "app_common.h"

// CDR のカプセル化ヘッダー(00 01 = リトルエンディアンの CDR)+ float64 × 6 = 52 バイト
#define TWIST_CDR_SIZE (4 + 6 * 8)

static void put_f64_le(uint8_t *dst, double value) {
    uint64_t bits;
    memcpy(&bits, &value, sizeof(bits));
    for (int i = 0; i < 8; i++) {
        dst[i] = (uint8_t)(bits >> (8 * i));
    }
}

// Twist = { linear: Vector3{x,y,z}, angular: Vector3{x,y,z} }。
// double は 8 バイト境界にそろえる決まりだが、ヘッダー直後の位置 0 から 8 の倍数で並ぶので詰め物は要らない。
static void encode_twist(uint8_t out[TWIST_CDR_SIZE], double vx, double wz) {
    const double fields[6] = {vx, 0.0, 0.0, 0.0, 0.0, wz};
    out[0] = 0x00;
    out[1] = 0x01;
    out[2] = 0x00;
    out[3] = 0x00;
    for (int i = 0; i < 6; i++) {
        put_f64_le(&out[4 + 8 * i], fields[i]);
    }
}

int main(int argc, char **argv) {
    app_args_t args = {.key = "cmd_vel", .count = 0};
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
    z_owned_publisher_t pub;
    if (z_declare_publisher(z_loan(s), &pub, z_loan(ke), NULL) < 0) {
        fprintf(stderr, "Unable to declare publisher\n");
        z_drop(z_move(s));
        return 1;
    }
    printf("publish Twist: '%s'  (Ctrl+C で終了)\n", args.key);

    uint8_t buf[TWIST_CDR_SIZE];
    for (int i = 0; args.count == 0 || i < args.count; i++) {
        // その場でゆっくり回る指令(前進 0.1 m/s、旋回 0.5 rad/s)
        encode_twist(buf, 0.1, 0.5);
        z_owned_bytes_t payload;
        z_bytes_copy_from_buf(&payload, buf, sizeof(buf));
        z_publisher_put(z_loan(pub), z_move(payload), NULL);
        printf("-> %s: linear.x=0.1 angular.z=0.5\n", args.key);
        z_sleep_ms(500);
    }

    z_drop(z_move(pub));
    z_drop(z_move(s));
    return 0;
}
