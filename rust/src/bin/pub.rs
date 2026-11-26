//! 一定間隔で文字列を publish する。
//!   cargo run --bin pub -- -e tcp/127.0.0.1:7447 -m client

use std::time::Duration;

use clap::Parser;
use zenoh_template::CommonArgs;

#[derive(Parser)]
struct Cli {
    /// publish するキー
    #[arg(short, long, default_value = "demo/hello/rust")]
    key: String,
    /// 送る文字列
    #[arg(short, long, default_value = "Hello from Rust")]
    payload: String,
    #[command(flatten)]
    common: CommonArgs,
}

#[tokio::main]
async fn main() -> zenoh::Result<()> {
    // RUST_LOG 環境変数があればそれを、なければ error レベルでログを出す
    zenoh::init_log_from_env_or("error");
    let cli = Cli::parse();

    let session = zenoh::open(cli.common.to_config()?).await?;
    let publisher = session.declare_publisher(cli.key.clone()).await?;
    println!("publish: '{}'  (Ctrl+C で終了)", cli.key);

    let mut interval = tokio::time::interval(Duration::from_secs(1));
    for i in 0u64.. {
        tokio::select! {
            _ = interval.tick() => {
                let msg = format!("[{i:4}] {}", cli.payload);
                publisher.put(msg.clone()).await?;
                println!("-> {}: {msg}", cli.key);
            }
            _ = tokio::signal::ctrl_c() => break,
        }
    }
    session.close().await?;
    Ok(())
}
