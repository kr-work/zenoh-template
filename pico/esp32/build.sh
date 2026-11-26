#!/usr/bin/env bash
# ESP32 のファームウェアを Docker の中でビルドする(macOS / Linux 用。Windows は build.ps1)。
#   ./build.sh            # esp32dev 向け
#   ./build.sh esp32dev
# 書き込み: esptool --chip esp32 --port /dev/ttyUSB0 write-flash 0x0 dist/esp32dev/firmware_merged.bin
set -euo pipefail
cd "$(dirname "$0")"

ENV_NAME="${1:-esp32dev}"
IMAGE="zenoh-template/esp32-builder:pio-6.2.0"

if [ ! -f include/secrets.h ]; then
    echo "include/secrets.h がありません。include/secrets.example.h をコピーして編集してください。" >&2
    exit 1
fi

docker build -t "$IMAGE" docker
mkdir -p dist
docker run --rm \
    -v "$PWD:/src:ro" \
    -v "$PWD/dist:/out" \
    -v zenoh-template-pio-home:/root/.platformio \
    -v zenoh-template-esp32-build:/work/.pio \
    "$IMAGE" bash /src/docker/build.sh "$ENV_NAME"
