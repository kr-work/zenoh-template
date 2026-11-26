<#
.SYNOPSIS
  ESP32 のファームウェアを Docker の中でビルドする。PC に PlatformIO・CMake・コンパイラは要らない。

.EXAMPLE
  .\build.ps1                  # esp32dev 向けにビルド
  .\build.ps1 -PioEnv esp32dev

  できたファイル: dist\<環境名>\firmware_merged.bin
  書き込みは .\flash.ps1 -Port COM5 で行う。

  スクリプトの実行が許可されていない場合は、次のように実行する。
  powershell -ExecutionPolicy Bypass -File .\build.ps1
#>
param(
    # platformio.ini の [env:...] の名前
    [string]$PioEnv = "esp32dev"
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$image = "zenoh-template/esp32-builder:pio-6.2.0"

if (-not (Test-Path (Join-Path $here "include\secrets.h"))) {
    Write-Error "include\secrets.h がありません。include\secrets.example.h をコピーして、Wi-Fi とルーターの情報を書いてください。"
}

Write-Host "== ビルド用イメージを用意しています ($image)"
docker build -t $image (Join-Path $here "docker")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$dist = Join-Path $here "dist"
New-Item -ItemType Directory -Force $dist | Out-Null

# PlatformIO のツールチェーンとビルド結果はボリュームに残し、2 回目以降のビルドを速くする
Write-Host "== $PioEnv をビルドしています"
docker run --rm `
    -v "${here}:/src:ro" `
    -v "${dist}:/out" `
    -v zenoh-template-pio-home:/root/.platformio `
    -v "zenoh-template-esp32-build:/work/.pio" `
    $image bash /src/docker/build.sh $PioEnv
exit $LASTEXITCODE
