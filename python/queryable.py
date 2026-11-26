"""問い合わせ(get)に応答する Queryable。RPC のサーバー側に当たる。

uv run queryable.py                   # demo/info/python への問い合わせに応答
"""

from __future__ import annotations

import argparse
import datetime

import zenoh

from zt.config import add_config_arguments, config_from_args


def main() -> None:
    parser = argparse.ArgumentParser(description="Zenoh queryable")
    add_config_arguments(parser)
    parser.add_argument("-k", "--key", default="demo/info/python", help="応答するキー")
    args = parser.parse_args()

    zenoh.init_log_from_env_or("error")

    with zenoh.open(config_from_args(args)) as session:
        # ハンドラーを渡さないと、届いた問い合わせはキューにたまり recv() で 1 件ずつ取り出せる
        queryable = session.declare_queryable(args.key)
        print(f"queryable: '{args.key}'  (Ctrl+C で終了)")
        try:
            while True:
                # with で囲むと、ブロックを抜けたときに「応答はこれで全部」と相手に伝わる
                with queryable.recv() as query:
                    body = query.payload.to_string() if query.payload is not None else ""
                    print(f"<- query: {query.selector}  payload='{body}'")
                    now = datetime.datetime.now().isoformat(timespec="seconds")
                    query.reply(args.key, f"python queryable, time={now}")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
