//! サンプル共通のコマンドライン引数と、そこから zenoh::Config を作る処理。
//!
//! どの実行ファイルも次の引数を受け付ける(Python 版と同じ):
//!   -c FILE / -m MODE / -e ENDPOINT / -l ENDPOINT / --no-multicast-scouting

use clap::Args;
use zenoh::Config;

#[derive(Args, Debug, Clone)]
pub struct CommonArgs {
    /// JSON5 の設定ファイル(例: ../config/client.json5)
    #[arg(short, long, value_name = "FILE")]
    pub config: Option<String>,

    /// セッションのモード
    #[arg(short, long, value_parser = ["peer", "client", "router"])]
    pub mode: Option<String>,

    /// 接続先(例: tcp/127.0.0.1:7447)。複数指定できる
    #[arg(short = 'e', long, value_name = "ENDPOINT")]
    pub connect: Vec<String>,

    /// 待ち受けアドレス(例: tcp/0.0.0.0:7448)。複数指定できる
    #[arg(short, long, value_name = "ENDPOINT")]
    pub listen: Vec<String>,

    /// UDP マルチキャストによる自動発見を止める
    #[arg(long)]
    pub no_multicast_scouting: bool,
}

impl CommonArgs {
    pub fn to_config(&self) -> zenoh::Result<Config> {
        let mut config = match &self.config {
            Some(path) => Config::from_file(path)?,
            None => Config::default(),
        };
        // insert_json5 には「キーのパス」と「JSON5 として解釈できる文字列」を渡す
        if let Some(mode) = &self.mode {
            config.insert_json5("mode", &serde_json::to_string(mode).unwrap())?;
        }
        if !self.connect.is_empty() {
            config.insert_json5("connect/endpoints", &serde_json::to_string(&self.connect).unwrap())?;
        }
        if !self.listen.is_empty() {
            config.insert_json5("listen/endpoints", &serde_json::to_string(&self.listen).unwrap())?;
        }
        if self.no_multicast_scouting {
            config.insert_json5("scouting/multicast/enabled", "false")?;
        }
        Ok(config)
    }
}
