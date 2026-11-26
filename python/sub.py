"""キー式に一致するデータを受け取って表示する。

uv run sub.py                         # demo/hello/** を購読
uv run sub.py -k 'demo/**'            # ワイルドカードで広く購読
"""

from __future__ import annotations

import argparse
import time

import zenoh

from zt.config import add_config_arguments, config_from_args


def payload_to_text(payload: zenoh.ZBytes) -> str:
    try:
        return payload.to_string()
    except ValueError:
        # UTF-8 でないバイト列(CDR など)は 16 進で表示する
        return payload.to_bytes().hex(" ")


def main() -> None:
    parser = argparse.ArgumentParser(description="Zenoh subscriber")
    add_config_arguments(parser)
    parser.add_argument("-k", "--key", default="demo/hello/**", help="購読するキー式")
    args = parser.parse_args()

    zenoh.init_log_from_env_or("error")

    def on_sample(sample: zenoh.Sample) -> None:
        # kind は PUT(値の更新)か DELETE(削除)
        print(f"<- {sample.key_expr} [{sample.kind}]: {payload_to_text(sample.payload)}")

    with zenoh.open(config_from_args(args)) as session:
        sub = session.declare_subscriber(args.key, on_sample)  # noqa: F841
        print(f"subscribe: '{args.key}'  (Ctrl+C で終了)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
