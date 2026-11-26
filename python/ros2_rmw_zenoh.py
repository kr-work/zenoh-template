"""rmw_zenoh(RMW_IMPLEMENTATION=rmw_zenoh_cpp)で動く ROS 2 ノードと、素の Zenoh からやり取りする。

rmw_zenoh はブリッジを使わず、ROS 2 の通信そのものを Zenoh で行う。キーとペイロードの形は次のとおり
(rmw_zenoh の docs/design.md による)。

  キー        <domain_id>/<トピック名>/<型名>/<型ハッシュ>
              例: 0/chatter/std_msgs::msg::dds_::String_/RIHS01_df668c...
  ペイロード  CDR のバイト列
  添付データ  int64 シーケンス番号(LE) + int64 送信時刻 ns(LE) + 1 バイトの長さ(16) + 16 バイトの GID

受信だけなら型ハッシュをワイルドカードにすればよい。送信するときは、ROS 2 側の購読者が
型ハッシュまで含めた正確なキーで待っているので、ハッシュを正しく入れ、添付データも付ける。
添付データがないサンプルを rmw_zenoh は捨てる。

なお、ここでの送信はデータを流すだけで、ノードやパブリッシャーの存在を知らせる
liveliness トークンは出さない。そのため ros2 topic list には現れないが、購読者には届く。

使い方(rmw_zenohd が localhost:7447 で待ち受けている前提):
    uv run ros2_rmw_zenoh.py graph     # ROS 2 のノードとトピックを liveliness トークンから一覧
    uv run ros2_rmw_zenoh.py listen    # /chatter を受信
    uv run ros2_rmw_zenoh.py talk      # /chatter に送信(ros2 run demo_nodes_cpp listener で受かる)
"""

from __future__ import annotations

import argparse
import itertools
import os
import struct
import time
from collections import defaultdict

import zenoh

from zt.cdr import decode_string, encode_string
from zt.config import add_config_arguments, config_from_args

# std_msgs/msg/String の型名と型ハッシュ(Jazzy 以降)。
# 別の型を使うときは `graph` サブコマンドの出力からコピーする。
STRING_TYPE = "std_msgs::msg::dds_::String_"
STRING_HASH = "RIHS01_df668c740482bbd48fb39d76a70dfd4bd59db1288021743503259e948f6b1a18"

ENTITY_KINDS = {
    "NN": "node",
    "MP": "publisher",
    "MS": "subscription",
    "SS": "service server",
    "SC": "service client",
}


def make_attachment(seq: int, gid: bytes) -> bytes:
    return struct.pack("<qq", seq, time.time_ns()) + bytes([len(gid)]) + gid


def parse_attachment(data: bytes) -> tuple[int, int, bytes]:
    seq, ts = struct.unpack_from("<qq", data, 0)
    n = data[16]
    return seq, ts, data[17 : 17 + n]


def unmangle(name: str) -> str:
    # liveliness トークンのキーでは、名前の中の '/' が '%' に置き換えられている
    return name.replace("%", "/")


def cmd_graph(session: zenoh.Session, domain: int) -> None:
    nodes: dict[str, list[str]] = defaultdict(list)
    for reply in session.liveliness().get(f"@ros2_lv/{domain}/**", timeout=3.0):
        if reply.ok is None:
            continue
        parts = str(reply.ok.key_expr).split("/")
        # @ros2_lv/<domain>/<session>/<node_id>/<entity_id>/<kind>/<enclave>/<namespace>/<node>[/...]
        if len(parts) < 9:
            continue
        kind, namespace, node = parts[5], unmangle(parts[7]), parts[8]
        node_fqn = (namespace.rstrip("/") + "/" + node) if namespace != "/" else "/" + node
        if kind == "NN" or len(parts) < 12:
            nodes.setdefault(node_fqn, [])
            continue
        topic, type_name, type_hash = unmangle(parts[9]), parts[10], parts[11]
        nodes[node_fqn].append(
            f"{ENTITY_KINDS.get(kind, kind):<15} {topic}  [{type_name}]  {type_hash}"
        )
    if not nodes:
        print("ノードが見つかりません。rmw_zenohd に接続できているか確認してください。")
    for node, entities in sorted(nodes.items()):
        print(node)
        for e in sorted(entities):
            print(f"    {e}")


def cmd_listen(session: zenoh.Session, domain: int, topic: str) -> None:
    # 型名と型ハッシュの 2 チャンクを * で受ける
    key = f"{domain}/{topic.strip('/')}/*/*"

    def on_sample(sample: zenoh.Sample) -> None:
        text = decode_string(sample.payload.to_bytes())
        info = ""
        if sample.attachment is not None:
            seq, _ts, gid = parse_attachment(sample.attachment.to_bytes())
            info = f"  (seq={seq}, gid={gid.hex()[:8]}...)"
        print(f"<- data='{text}'{info}")

    session.declare_subscriber(key, on_sample)
    print(f"subscribe: '{key}'  Ctrl+C で終了")
    while True:
        time.sleep(1)


def cmd_talk(session: zenoh.Session, domain: int, topic: str, interval: float) -> None:
    key = f"{domain}/{topic.strip('/')}/{STRING_TYPE}/{STRING_HASH}"
    gid = os.urandom(16)  # このパブリッシャーの ID。ROS 2 側では送信元の識別に使われる
    pub = session.declare_publisher(key)
    print(f"publish: '{key}'  Ctrl+C で終了")
    for seq in itertools.count(1):
        text = f"Hello rmw_zenoh from plain Zenoh: {seq}"
        pub.put(encode_string(text), attachment=make_attachment(seq, gid))
        print(f"-> data='{text}'")
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="rmw_zenoh で動く ROS 2 とやり取りする")
    add_config_arguments(parser)
    parser.add_argument("--domain", type=int, default=int(os.environ.get("ROS_DOMAIN_ID", "0")))
    parser.add_argument("--topic", default="/chatter")
    parser.add_argument("--interval", type=float, default=1.0, help="送信間隔 [秒]")
    parser.add_argument("command", choices=["graph", "listen", "talk"])
    args = parser.parse_args()

    # 何も指定がなければ、ローカルの rmw_zenohd にクライアントとしてつなぐ
    if not args.config and not args.connect:
        args.connect = ["tcp/127.0.0.1:7447"]
    if not args.mode:
        args.mode = "client"

    zenoh.init_log_from_env_or("error")
    with zenoh.open(config_from_args(args)) as session:
        try:
            if args.command == "graph":
                cmd_graph(session, args.domain)
            elif args.command == "listen":
                cmd_listen(session, args.domain, args.topic)
            else:
                cmd_talk(session, args.domain, args.topic, args.interval)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
