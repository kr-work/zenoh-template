"""PlatformIO の追加スクリプト。`pio run -t mergebin` で、書き込みに必要なイメージ
(ブートローダー、パーティションテーブル、アプリなど)を 1 つのファイルにまとめる。

まとめたファイルはアドレス 0x0 に書き込めばよいので、PlatformIO が入っていない PC からでも
esptool だけで書き込める。

    esptool --chip esp32 --port COM5 write-flash 0x0 firmware_merged.bin
"""

Import("env")  # noqa: F821  (PlatformIO が実行時に用意する関数)

APP_BIN = "$BUILD_DIR/${PROGNAME}.bin"
MERGED_BIN = "$BUILD_DIR/${PROGNAME}_merged.bin"


def merge_bin(source, target, env):
    mcu = env.BoardConfig().get("build.mcu", "esp32")
    # FLASH_EXTRA_IMAGES は [(アドレス, ファイル), ...]。ブートローダーやパーティションテーブルが入っている
    images = []
    for offset, image in env.get("FLASH_EXTRA_IMAGES", []):
        images += [offset, image]
    images += ["$ESP32_APP_OFFSET", APP_BIN]
    # espressif32 プラットフォームでは $OBJCOPY が esptool.py を指している
    cmd = ["$PYTHONEXE", "$OBJCOPY", "--chip", mcu, "merge_bin", "-o", MERGED_BIN] + images
    env.Execute(" ".join('"%s"' % env.subst(str(c)) for c in cmd))


env.AddCustomTarget(  # noqa: F821
    name="mergebin",
    dependencies=APP_BIN,
    actions=merge_bin,
    title="Merge binary",
    description="Merge bootloader, partitions and app into one image for address 0x0",
)
