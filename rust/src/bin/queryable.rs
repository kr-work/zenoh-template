//! 問い合わせ(get)に応答する Queryable。
//!   cargo run --bin queryable

use std::time::{SystemTime, UNIX_EPOCH};

use clap::Parser;
use zenoh_template::CommonArgs;

#[derive(Parser)]
struct Cli {
    /// 応答するキー
    #[arg(short, long, default_value = "demo/info/rust")]
    key: String,
    #[command(flatten)]
    common: CommonArgs,
}

#[tokio::main]
async fn main() -> zenoh::Result<()> {
    zenoh::init_log_from_env_or("error");
    let cli = Cli::parse();

    let session = zenoh::open(cli.common.to_config()?).await?;
    let queryable = session.declare_queryable(cli.key.clone()).await?;
    println!("queryable: '{}'  (Ctrl+C で終了)", cli.key);

    loop {
        tokio::select! {
            query = queryable.recv_async() => {
                let Ok(query) = query else { break };
                let body = query
                    .payload()
                    .and_then(|p| p.try_to_string().ok().map(|s| s.into_owned()))
                    .unwrap_or_default();
                println!("<- query: {}  payload='{body}'", query.selector());
                let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
                // query を drop すると「応答はこれで全部」と相手に伝わる
                query.reply(cli.key.clone(), format!("rust queryable, unix_time={now}")).await?;
            }
            _ = tokio::signal::ctrl_c() => break,
        }
    }
    session.close().await?;
    Ok(())
}
