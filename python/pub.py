"""一定間隔で文字列を publish する。

uv run pub.py                                  # ピアモード(同じ LAN を自動発見)
uv run pub.py -e tcp/127.0.0.1:7447 -m client  # ルーターにつなぐ
"""

from __future__ import annotations

import argparse
import itertools
import time

import zenoh

from zt.config import add_config_arguments, config_from_args


def main() -> None:
    parser = argparse.ArgumentParser(description="Zenoh publisher")
    add_config_arguments(parser)
    parser.add_argument("-k", "--key", default="demo/hello/python", help="publish するキー")
    parser.add_argument("-p", "--payload", default="Hello from Python", help="送る文字列")
    parser.add_argument("-n", "--count", type=int, help="送信回数(省略すると Ctrl+C まで続ける)")
    parser.add_argument("--interval", type=float, default=1.0, help="送信間隔 [秒]")
    parser.add_argument(
        "--raw", action="store_true", help="通し番号を付けず、--payload の文字列をそのまま送る"
    )
    args = parser.parse_args()

    # RUST_LOG 環境変数があればそれを、なければ error レベルでログを出す
    zenoh.init_log_from_env_or("error")

    with zenoh.open(config_from_args(args)) as session:
        pub = session.declare_publisher(args.key)
        print(f"publish: '{args.key}'  (Ctrl+C で終了)")
        counter = range(args.count) if args.count else itertools.count()
        try:
            for i in counter:
                msg = args.payload if args.raw else f"[{i:4d}] {args.payload}"
                pub.put(msg)
                print(f"-> {args.key}: {msg}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
