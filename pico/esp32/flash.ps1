<#
.SYNOPSIS
  build.ps1 で作ったファームウェアを、USB でつないだ ESP32 に書き込む。

.DESCRIPTION
  Windows の Docker Desktop からは USB シリアル(COM ポート)を直接使えないので、書き込みだけは
  Windows 側で行う。esptool は uv が一時的に取得して実行するので、事前のインストールは要らない。

.EXAMPLE
  .\flash.ps1                         # COM ポートの一覧を表示する
  .\flash.ps1 -Port COM5              # COM5 につないだ ESP32 に書き込む
  .\flash.ps1 -Port COM5 -Monitor     # 書き込んだあとシリアル出力を表示する(Ctrl+] で終了)
#>
param(
    [string]$Port,
    [string]$PioEnv = "esp32dev",
    # esptool に渡すチップ名(ESP32-C6 なら esp32c6)
    [string]$Chip = "esp32",
    [int]$Baud = 460800,
    [switch]$Monitor
)
$ErrorActionPreference = "Stop"
$esptool = "esptool==5.7.0"

$bin = Join-Path $PSScriptRoot "dist\$PioEnv\firmware_merged.bin"
if (-not (Test-Path $bin)) {
    Write-Error "$bin がありません。先に .\build.ps1 を実行してください。"
}

if (-not $Port) {
    Write-Host "書き込み先を -Port COM5 のように指定してください。見つかったシリアルポート:"
    uvx --from pyserial pyserial-ports -v
    exit 1
}

# まとめたイメージ(ブートローダー + パーティションテーブル + アプリ)をアドレス 0x0 に書き込む
uvx --from $esptool esptool --chip $Chip --port $Port --baud $Baud write-flash 0x0 $bin
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($Monitor) {
    Write-Host "== シリアルモニター($Port, 115200 bps)。Ctrl+] で終了"
    uvx --from pyserial pyserial-miniterm $Port 115200
}
