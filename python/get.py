"""キー式に一致する Queryable(とストレージ)に問い合わせ、返ってきた応答をすべて表示する。

uv run get.py                         # demo/info/** に問い合わせ
uv run get.py -s 'demo/info/**?verbose=true' -p "hello"
"""

from __future__ import annotations

import argparse

import zenoh

from zt.config import add_config_arguments, config_from_args


def main() -> None:
    parser = argparse.ArgumentParser(description="Zenoh get")
    add_config_arguments(parser)
    parser.add_argument(
        "-s", "--selector", default="demo/info/**", help="問い合わせ先(キー式 + ?パラメータ)"
    )
    parser.add_argument("-p", "--payload", help="問い合わせに添えるデータ")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="待ち時間 [秒]")
    args = parser.parse_args()

    zenoh.init_log_from_env_or("error")

    with zenoh.open(config_from_args(args)) as session:
        print(f"get: '{args.selector}'")
        replies = session.get(args.selector, payload=args.payload, timeout=args.timeout)
        count = 0
        # 応答は複数返ることがある。全員が応答し終えるか、タイムアウトするとループを抜ける
        for reply in replies:
            if reply.ok is not None:
                print(f"<- {reply.ok.key_expr}: {reply.ok.payload.to_string()}")
            else:
                print(f"<- error: {reply.err.payload.to_string()}")
            count += 1
        print(f"{count} 件の応答")


if __name__ == "__main__":
    main()
