# ESP32 向けのファームウェアを PlatformIO でビルドするための環境。
# zenoh-pico のビルドスクリプトは、ビルド時に cmake と C/C++ コンパイラで設定ヘッダーを作るので、それも入れる。
# 使い方は pico/esp32/build.ps1(Windows)または build.sh(macOS / Linux)を参照。
FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates git cmake make gcc g++ libc6-dev python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

ARG PLATFORMIO_VERSION=6.2.0
RUN python3 -m venv /opt/pio \
    && /opt/pio/bin/pip install --no-cache-dir "platformio==${PLATFORMIO_VERSION}"
ENV PATH=/opt/pio/bin:$PATH

WORKDIR /work
