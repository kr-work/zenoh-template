# zenoh-template

[Eclipse Zenoh](https://zenoh.io/) 1.10 系で pub/sub と問い合わせ(query)を始めるためのテンプレートです。Python・Rust・zenoh-pico(PC と ESP32)のサンプルと、ROS 2 につなぐ 2 通りの構成(zenoh-bridge-ros2dds と rmw_zenoh)が入っています。

Zenoh の考え方、zenoh-pico の使い方、ROS 2 との接続方法は [docs/zenoh-guide.md](docs/zenoh-guide.md) で解説しています。

## ディレクトリ構成

```
zenoh-template/
├── docker-compose.yml        Zenoh ルーター(zenohd)を起動する
├── config/                   router / peer / client の設定ファイル(JSON5)
├── python/                   Python のサンプル(uv で実行)
│   ├── pub.py sub.py         pub/sub
│   ├── queryable.py get.py   問い合わせと応答
│   ├── ros2_bridge.py        zenoh-bridge-ros2dds 経由で ROS 2 とやり取りする
│   ├── ros2_rmw_zenoh.py     rmw_zenoh で動く ROS 2 とやり取りする
│   └── zt/                   設定の読み込みと CDR 変換の共通コード
├── rust/                     Rust のサンプル(src/bin/*.rs)
├── pico/
│   ├── desktop/              zenoh-pico を PC 向けに CMake でビルドする
│   └── esp32/                zenoh-pico を ESP32 で動かす PlatformIO プロジェクト
├── ros2/
│   ├── docker/Dockerfile     ROS 2 Jazzy + rmw_cyclonedds + rmw_zenoh のイメージ
│   ├── bridge/               DDS の ROS 2 と zenoh-bridge-ros2dds の構成
│   └── rmw_zenoh/            rmw_zenoh の構成
└── docs/zenoh-guide.md       解説記事
```

どの言語のサンプルも、pub/sub は `demo/hello/<言語>`、問い合わせは `demo/info/<言語>` というキーを使います。購読側は `demo/hello/**` を受けるので、言語を混ぜて動かせます。

## まず動かす

必要なもの: [uv](https://docs.astral.sh/uv/)、Docker(ルーターをコンテナで動かす場合)。

1. ルーターを起動します。

   ```powershell
   docker compose up -d
   ```

   Docker を使わない場合は、[リリースページ](https://github.com/eclipse-zenoh/zenoh/releases/tag/1.10.2)から `zenoh-1.10.2-x86_64-pc-windows-msvc-standalone.zip` を取得し、展開した `zenohd.exe` を `zenohd -c config/router.json5` で起動します。

2. 別々のターミナルで、購読側と送信側を起動します。

   ```powershell
   cd python
   uv run sub.py -m client -e tcp/127.0.0.1:7447
   ```

   ```powershell
   cd python
   uv run pub.py -m client -e tcp/127.0.0.1:7447
   ```

   `sub.py` 側に `<- demo/hello/python [SampleKind.PUT]: [   0] Hello from Python` のような行が出れば成功です。

3. 問い合わせも試せます。

   ```powershell
   uv run queryable.py -m client -e tcp/127.0.0.1:7447
   ```

   ```powershell
   uv run get.py -m client -e tcp/127.0.0.1:7447
   ```

ルーターなしでも、同じ LAN の中ならピアモード(引数なし)で互いを自動発見してつながります。ただし、Wi-Fi のクライアント間通信が遮断されている環境や、Docker Desktop のコンテナとホストの間では UDP マルチキャストが届かないので、`-e` で接続先を指定してください。

## サンプル

| ディレクトリ | 内容 | 実行例 |
|---|---|---|
| `python/` | pub/sub、get/queryable | `uv run sub.py -k 'demo/**'` |
| `rust/` | 同じ 4 種類を Rust で | `cargo run --bin sub -- -e tcp/127.0.0.1:7447` |
| `pico/desktop/` | zenoh-pico の pub/sub、queryable、ROS 2 の Twist 送信 | `cmake -B build`、`cmake --build build` のあと `./build/pico_sub -e tcp/127.0.0.1:7447` |
| `pico/esp32/` | ESP32 から状態を publish し、LED の指令を購読 | `include/secrets.h` を用意して `pio run -t upload` |
| `ros2/bridge/` | DDS の ROS 2 ノード + zenoh-bridge-ros2dds | `docker compose up --build` のあと `uv run ros2_bridge.py listen` |
| `ros2/rmw_zenoh/` | rmw_zenoh の ROS 2 ノード + rmw_zenohd | `docker compose up --build` のあと `uv run ros2_rmw_zenoh.py graph` |

`pico/desktop` は Windows でもビルドできます(Visual Studio の C コンパイラと CMake が必要です)。生成された実行ファイルは `build\Debug\pico_sub.exe` のように構成名のフォルダーに入ります。

`pico/esp32` のビルドにも、PC 側に CMake と C コンパイラが要ります。zenoh-pico のビルドスクリプトが、ビルドのたびに PC 上で cmake を実行して設定ヘッダーを生成するためです。

## ROS 2 とつなぐ

ROS 2 と Zenoh をつなぐ方法は 2 つあります。この 2 つの方式どうしは通信できません。どちらを選ぶかは [解説記事の 6 章](docs/zenoh-guide.md#6-ros-2-とつなぐ2-つの方法) を参照してください。

- `ros2/bridge/`: ROS 2 は DDS(CycloneDDS)のまま動かし、zenoh-bridge-ros2dds が DDS と Zenoh を相互に変換します。ROS 2 の `/chatter` は Zenoh のキー `chatter` になります。
- `ros2/rmw_zenoh/`: ROS 2 の通信そのものを Zenoh で行います(`RMW_IMPLEMENTATION=rmw_zenoh_cpp`)。キーは `0/chatter/std_msgs::msg::dds_::String_/RIHS01_...` の形です。

どちらの構成も、ホストの 7447/tcp で Zenoh として見えます。同時には起動しないでください(ポートがぶつかります)。

## バージョンを上げるとき

Zenoh のバージョンは次の箇所で 1.10.2 に固定しています。上げるときは全部そろえてください。

- `python/pyproject.toml` の `eclipse-zenoh`
- `rust/Cargo.toml` の `zenoh`
- `pico/desktop/CMakeLists.txt` の `ZENOH_PICO_VERSION`
- `pico/esp32/platformio.ini` の `lib_deps`
- `docker-compose.yml` と `ros2/bridge/compose.yml` のイメージのタグ

## テンプレートとして使うとき

- キーの先頭の `demo/` を、プロジェクトの名前に置き換えます。キーは `/` 区切りの階層なので、`<プロジェクト>/<装置>/<データの種類>` のように決めておくと、ワイルドカードで購読しやすくなります。
- `.github/workflows/ci.yml` は Python のスモークテスト、Rust のビルド、zenoh-pico の PC 向けビルド(Linux と Windows)、ESP32 向けビルドを実行します。使わない言語のジョブは削除してください。
- ライセンスファイルは入れていません。公開するときは用途に合わせて追加してください。Zenoh 本体は EPL-2.0 と Apache-2.0 のデュアルライセンスです。
