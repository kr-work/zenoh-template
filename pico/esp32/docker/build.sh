#!/usr/bin/env bash
# コンテナの中で実行する(build.ps1 / build.sh から呼ばれる)。
#   /src  : プロジェクト(読み取り専用でマウント)
#   /work : ビルド用の作業場所。/work/.pio はボリュームにして、2 回目以降のビルドを速くする
#   /out  : 書き込み用のファイルの出力先(ホストの dist/ に対応)
set -euo pipefail

ENV_NAME="${1:-esp32dev}"

# ソースだけを作業場所にコピーする(ホストのフォルダーに .pio を作らないため)
mkdir -p /work
rm -rf /work/src /work/include /work/scripts /work/lib
cp /src/platformio.ini /work/
cp -r /src/src /src/include /src/scripts /work/
if [ -d /src/lib ]; then cp -r /src/lib /work/; fi

cd /work
pio run -e "$ENV_NAME" -t mergebin

BUILD_DIR=".pio/build/$ENV_NAME"
mkdir -p "/out/$ENV_NAME"
cp "$BUILD_DIR/firmware.bin" "$BUILD_DIR/firmware_merged.bin" "/out/$ENV_NAME/"
echo "出力: dist/$ENV_NAME/firmware_merged.bin(アドレス 0x0 に書き込む)"
