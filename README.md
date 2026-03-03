# kiro-usage

Track token usage and costs across [Kiro CLI](https://kiro.dev) sessions.

Real-time terminal dashboard with session archiving that persists across `/clear` and restarts.

## Install

```sh
# install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

uv tool install kiro-usage && kiro-usage install
```

## Usage

```sh
kiro-usage              # today's usage, live refresh
kiro-usage week         # last 7 days
kiro-usage month        # last 30 days
kiro-usage all          # all time
kiro-usage --json       # JSON output
kiro-usage --no-live    # print once and exit
```

## Service Management

```sh
kiro-usage install      # register background archiver (launchd / systemd)
kiro-usage uninstall    # remove background archiver
kiro-usage status       # check archiver status
```

The background archiver watches the Kiro CLI database and snapshots sessions to `~/.kiro_sessions/` every 10 seconds. This ensures session data is preserved even if you `/clear` or quit Kiro CLI.

## How It Works

```
kiro-cli SQLite DB
       │
       │ mtime change (every 10s)
       ▼
  kiro-usage-archiver  ──► ~/.kiro_sessions/*.json
  (launchd / systemd)

  kiro-usage viewer    ◄── ~/.kiro_sessions/*.json
  (on-demand)
```

**Metrics:**
- **CacheWrite** — new tokens per turn (estimated, chars/4)
- **CacheRead** — prior context resent to API (estimated)
- **Output** — tokens streamed back (from chunks, accurate)
- **Cost** — cache-aware pricing estimate (5-min cache write rate)

## Uninstall

```sh
kiro-usage uninstall
uv tool uninstall kiro-usage
```

## License

MIT
