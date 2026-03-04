# kiro-usage

**Track token usage and costs across [Kiro](https://kiro.dev) AI coding sessions — in real time.**

[![PyPI version](https://img.shields.io/pypi/v/kiro-usage)](https://pypi.org/project/kiro-usage/)
[![Python](https://img.shields.io/pypi/pyversions/kiro-usage)](https://pypi.org/project/kiro-usage/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-blue)](#install)

A lightweight terminal dashboard that monitors your **Kiro CLI** token consumption and cost estimates — including cache-read/cache-write breakdown — and persists data across `/clear` and restarts via a background archiver.

> **Why?** Kiro does not expose running token totals in the UI. This tool fills that gap: see exactly how many tokens and dollars each session costs, live, as you work.

---

## Features

- **Real-time dashboard** — live-refreshing terminal UI (powered by [Rich](https://github.com/Textualize/rich))
- **Session archiving** — background service snapshots sessions every 10 s; data survives `/clear` and Kiro restarts
- **Cache breakdown** — separates CacheWrite (new tokens), CacheRead (context resent), and Output tokens
- **Cost estimates** — cache-aware pricing (5-min write rate vs. 1-hour read rate)
- **Multiple time windows** — today / last 7 days / last 30 days / all time
- **JSON output** — pipe-friendly `--json` flag for scripting
- **IDE tracking** — tracks usage across Kiro IDE sessions as well as CLI sessions
- **macOS + Linux** — service registration via `launchd` (macOS) or `systemd` (Linux)

---

## Install

Requires [uv](https://docs.astral.sh/uv/) (recommended) or pip with Python ≥ 3.9.

```sh
# install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# install kiro-usage and register the background archiver
uv tool install kiro-usage && kiro-usage install
```

Or with pip:

```sh
pip install kiro-usage
kiro-usage install
```

---

## Usage

```sh
kiro-usage              # today's usage, live refresh
kiro-usage week         # last 7 days
kiro-usage month        # last 30 days
kiro-usage all          # all time

kiro-usage --json       # JSON output (machine-readable)
kiro-usage --no-live    # print once and exit (good for scripts/CI)
```

### Service Management

```sh
kiro-usage install      # register background archiver (launchd / systemd)
kiro-usage uninstall    # remove background archiver
kiro-usage status       # check archiver status
```

The background archiver watches the Kiro CLI SQLite database for changes and snapshots sessions to `~/.kiro_sessions/` every 10 seconds. This ensures session data is preserved even after `/clear` or a Kiro restart.

---

## How It Works

```
Kiro CLI / Kiro IDE
  SQLite database (~/.kiro/...)
        │
        │  file mtime poll (every 10 s)
        ▼
  kiro-usage-archiver  ──►  ~/.kiro_sessions/*.json
  (launchd / systemd)

  kiro-usage viewer    ◄──  ~/.kiro_sessions/*.json
  (on-demand, live-refresh)
```

### Token Metrics

| Metric | Description |
|---|---|
| **CacheWrite** | New tokens sent this turn (estimated, chars ÷ 4) |
| **CacheRead** | Prior context resent to the API (estimated) |
| **Output** | Tokens streamed back from the model (from chunks, accurate) |
| **Cost** | Cache-aware estimate — write tokens at 5-min rate, read tokens at 1-hour rate |

---

## FAQ

**Q: Does this work with Claude / Anthropic models?**
Yes — Kiro uses Claude models under the hood. `kiro-usage` tracks whatever tokens Kiro sends and receives.

**Q: Does it need an API key?**
No. It reads Kiro's local SQLite database directly — no network calls, no extra credentials.

**Q: Is data sent anywhere?**
No. Everything stays local in `~/.kiro_sessions/`.

**Q: Why do costs look like estimates?**
Kiro doesn't expose the exact prompt/completion split, so input tokens are approximated from character count (÷ 4). Output tokens come from streaming chunks and are accurate.

**Q: Does it work without systemd / launchd?**
Yes. Run `kiro-usage-archiver` manually in a terminal, or just use `kiro-usage` without the background service (you'll only see current-session data without persistence across `/clear`).

---

## Uninstall

```sh
kiro-usage uninstall
uv tool uninstall kiro-usage
```

---

## License

[MIT](LICENSE)
