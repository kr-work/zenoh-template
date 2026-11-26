"""zenoh-bridge-ros2dds を経由して、DDS で動く ROS 2 ノードとやり取りする。

ブリッジは ROS 2 のトピック名から先頭の '/' を取ったものを Zenoh のキーにする。
(ブリッジに namespace を設定すると、その前に namespace が付く)

    ROS 2 のトピック     Zenoh のキー
    /chatter         ->  chatter
    /cmd_vel         ->  cmd_vel          namespace "/bot1" なら bot1/cmd_vel

ペイロードは CDR のバイト列そのもの。

使い方(ブリッジが localhost:7447 で待ち受けている前提):
    uv run ros2_bridge.py listen            # ROS 2 の /chatter を受信
    uv run ros2_bridge.py talk              # Zenoh から ROS 2 の /chatter に送信
    uv run ros2_bridge.py cmd_vel --vx 0.2 --wz 0.5   # /cmd_vel に Twist を送信
"""

from __future__ import annotations

import argparse
import itertools
import time

import zenoh

from zt.cdr import Twist, decode_string, encode_string, encode_twist
from zt.config import add_config_arguments, config_from_args


def key_for(topic: str, namespace: str) -> str:
    topic = topic.strip("/")
    namespace = namespace.strip("/")
    return f"{namespace}/{topic}" if namespace else topic


def cmd_listen(session: zenoh.Session, key: str) -> None:
    def on_sample(sample: zenoh.Sample) -> None:
        print(f"<- {sample.key_expr}: data='{decode_string(sample.payload.to_bytes())}'")

    session.declare_subscriber(key, on_sample)
    print(f"subscribe: '{key}' (std_msgs/msg/String)  Ctrl+C で終了")
    while True:
        time.sleep(1)


def cmd_talk(session: zenoh.Session, key: str, interval: float) -> None:
    pub = session.declare_publisher(key)
    print(f"publish: '{key}' (std_msgs/msg/String)  Ctrl+C で終了")
    for i in itertools.count():
        text = f"Hello ROS 2 from Zenoh: {i}"
        pub.put(encode_string(text))
        print(f"-> {key}: data='{text}'")
        time.sleep(interval)


def cmd_cmd_vel(session: zenoh.Session, key: str, interval: float, twist: Twist) -> None:
    pub = session.declare_publisher(key)
    print(f"publish: '{key}' (geometry_msgs/msg/Twist)  Ctrl+C で終了")
    payload = encode_twist(twist)
    while True:
        pub.put(payload)
        print(f"-> {key}: {twist}")
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="zenoh-bridge-ros2dds 経由で ROS 2 とやり取りする")
    add_config_arguments(parser)
    parser.add_argument("--namespace", default="", help="ブリッジに設定した namespace(例: /bot1)")
    parser.add_argument("--interval", type=float, default=1.0, help="送信間隔 [秒]")
    sub = parser.add_subparsers(dest="command", required=True)
    p_listen = sub.add_parser("listen", help="std_msgs/String を受信する")
    p_listen.add_argument("--topic", default="/chatter")
    p_talk = sub.add_parser("talk", help="std_msgs/String を送信する")
    p_talk.add_argument("--topic", default="/chatter")
    p_vel = sub.add_parser("cmd_vel", help="geometry_msgs/Twist を送信する")
    p_vel.add_argument("--topic", default="/cmd_vel")
    p_vel.add_argument("--vx", type=float, default=0.2, help="並進速度 x [m/s]")
    p_vel.add_argument("--wz", type=float, default=0.0, help="角速度 z [rad/s]")
    args = parser.parse_args()

    # 何も指定がなければ、ローカルのブリッジ(ルーターモードで 7447 を待ち受け)につなぐ
    if not args.config and not args.connect:
        args.connect = ["tcp/127.0.0.1:7447"]
    if not args.mode:
        args.mode = "client"

    zenoh.init_log_from_env_or("error")
    key = key_for(args.topic, args.namespace)
    with zenoh.open(config_from_args(args)) as session:
        try:
            if args.command == "listen":
                cmd_listen(session, key)
            elif args.command == "talk":
                cmd_talk(session, key, args.interval)
            else:
                cmd_cmd_vel(session, key, args.interval, Twist(linear_x=args.vx, angular_z=args.wz))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
