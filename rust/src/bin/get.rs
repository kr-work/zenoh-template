//! キー式に一致する Queryable に問い合わせ、返ってきた応答をすべて表示する。
//!   cargo run --bin get -- -s 'demo/info/**'

use std::time::Duration;

use clap::Parser;
use zenoh_template::CommonArgs;

#[derive(Parser)]
struct Cli {
    /// 問い合わせ先(キー式 + ?パラメータ)
    #[arg(short, long, default_value = "demo/info/**")]
    selector: String,
    /// 問い合わせに添えるデータ
    #[arg(short, long)]
    payload: Option<String>,
    /// 待ち時間 [秒]
    #[arg(short, long, default_value_t = 5.0)]
    timeout: f64,
    #[command(flatten)]
    common: CommonArgs,
}

#[tokio::main]
async fn main() -> zenoh::Result<()> {
    zenoh::init_log_from_env_or("error");
    let cli = Cli::parse();

    let session = zenoh::open(cli.common.to_config()?).await?;
    println!("get: '{}'", cli.selector);

    let mut builder = session
        .get(cli.selector.as_str())
        .timeout(Duration::from_secs_f64(cli.timeout));
    if let Some(p) = cli.payload {
        builder = builder.payload(p);
    }
    let replies = builder.await?;

    let mut count = 0;
    // 応答は複数返ることがある。全員が応答し終えるか、タイムアウトするとループを抜ける
    while let Ok(reply) = replies.recv_async().await {
        match reply.result() {
            Ok(sample) => {
                let text = sample.payload().try_to_string().unwrap_or_default();
                println!("<- {}: {text}", sample.key_expr());
            }
            Err(err) => {
                let text = err.payload().try_to_string().unwrap_or_default();
                println!("<- error: {text}");
            }
        }
        count += 1;
    }
    println!("{count} 件の応答");
    session.close().await?;
    Ok(())
}
