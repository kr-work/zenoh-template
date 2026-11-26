//! キー式に一致するデータを受け取って表示する。
//!   cargo run --bin sub -- -k 'demo/**'

use clap::Parser;
use zenoh_template::CommonArgs;

#[derive(Parser)]
struct Cli {
    /// 購読するキー式
    #[arg(short, long, default_value = "demo/hello/**")]
    key: String,
    #[command(flatten)]
    common: CommonArgs,
}

#[tokio::main]
async fn main() -> zenoh::Result<()> {
    zenoh::init_log_from_env_or("error");
    let cli = Cli::parse();

    let session = zenoh::open(cli.common.to_config()?).await?;
    // ハンドラーを指定しないと、受信したサンプルは FIFO キューにたまり recv_async() で取り出せる
    let subscriber = session.declare_subscriber(cli.key.clone()).await?;
    println!("subscribe: '{}'  (Ctrl+C で終了)", cli.key);

    loop {
        tokio::select! {
            sample = subscriber.recv_async() => {
                let Ok(sample) = sample else { break };
                let payload = sample
                    .payload()
                    .try_to_string()
                    .map(|s| s.into_owned())
                    .unwrap_or_else(|_| format!("{:02x?}", sample.payload().to_bytes()));
                println!("<- {} [{}]: {payload}", sample.key_expr(), sample.kind());
            }
            _ = tokio::signal::ctrl_c() => break,
        }
    }
    session.close().await?;
    Ok(())
}
