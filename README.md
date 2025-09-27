# Simple Telegram Bot

## Environment Variables

Before running the bot, configure the following environment variables:

- `BOT_TOKEN` – Telegram bot token from [BotFather](https://t.me/botfather).  
- `API_URL` – URL of the backend (FastAPI service). Example: `http://backend:8000`.  

## Run without Docker

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables (example for Linux/macOS):
   ```bash
   export BOT_TOKEN="your_bot_token"
   export API_URL="http://localhost:8000"
   ```

3. Start the bot:
   ```bash
   python bot.py
   ```

## Run with Docker

1. Build the image:
   ```bash
   docker build -t simple-telegram-bot .
   ```

2. Run the container:
   ```bash
   docker run -d \
     -e BOT_TOKEN=your_bot_token \
     -e API_URL=http://backend:8000 \
     simple-telegram-bot
    ```
