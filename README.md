# FORC Checker

Telegram bot that checks a task list URL and notifies you when the list changes.

## Run

```bash
python run.py
```

Configure `config.py` (BOT_TOKEN, URL, INTERVAL) before running.

## Project structure

```
forc_checker/
  run.py              # Entry point — run the bot
  config.py            # BOT_TOKEN, URL, INTERVAL
  monitoring_chats.json   # Persisted monitoring subscribers

  src/
    checker/           # FORC task list fetcher
      client.py        # CheckerClient — session(), run_loop()
    telegram_bot/      # Telegram app
      app.py           # Builds application, runs polling
      handlers.py      # /start, /search, /monitoring, buttons
      monitoring.py    # Chat persistence, job, broadcast on change
    utils/
      logger.py
```

## Requirements

- Python 3.9+
- `requests`, `python-telegram-bot` (see requirements.txt)
