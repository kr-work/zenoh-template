"""コマンドライン引数から zenoh.Config を組み立てる。

どのサンプルも次の引数を受け付ける。

  -c FILE        JSON5 の設定ファイル(例: ../config/client.json5)
  -m MODE        peer / client / router
  -e ENDPOINT    接続先(例: tcp/192.168.1.10:7447)。複数指定できる
  -l ENDPOINT    待ち受けアドレス(例: tcp/0.0.0.0:7448)。複数指定できる
  --no-multicast-scouting
                 UDP マルチキャストによる自動発見を止める

引数はファイルの内容より優先される。
"""

from __future__ import annotations

import argparse
import json
import sys

import zenoh


def add_config_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-c", "--config", metavar="FILE", help="JSON5 の設定ファイル")
    parser.add_argument(
        "-m", "--mode", choices=["peer", "client", "router"], help="セッションのモード"
    )
    parser.add_argument(
        "-e",
        "--connect",
        metavar="ENDPOINT",
        action="append",
        help="接続先(例: tcp/127.0.0.1:7447)",
    )
    parser.add_argument(
        "-l", "--listen", metavar="ENDPOINT", action="append", help="待ち受けアドレス"
    )
    parser.add_argument(
        "--no-multicast-scouting", action="store_true", help="マルチキャストでの自動発見を止める"
    )


def config_from_args(args: argparse.Namespace) -> zenoh.Config:
    # 出力をファイルやパイプにリダイレクトすると、Python は出力をまとめて溜めてから書き出す。
    # 受信のたびに表示が出るよう、1 行ごとに書き出す設定にしておく(CI でログを確かめるときにも要る)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    conf = zenoh.Config.from_file(args.config) if args.config else zenoh.Config()
    # insert_json5 には「キーのパス」と「JSON5 として解釈できる文字列」を渡す
    if args.mode:
        conf.insert_json5("mode", json.dumps(args.mode))
    if args.connect:
        conf.insert_json5("connect/endpoints", json.dumps(args.connect))
    if args.listen:
        conf.insert_json5("listen/endpoints", json.dumps(args.listen))
    if args.no_multicast_scouting:
        conf.insert_json5("scouting/multicast/enabled", "false")
    return conf
