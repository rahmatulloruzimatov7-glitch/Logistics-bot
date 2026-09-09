# Logistics Bot

Telegram bot for logistics trip report processing.

## Setup

### 1. Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Enable **Google Sheets API**
4. Go to **Credentials** → **Create Credentials** → **Service Account**
5. Download the JSON key file
6. Save it as `credentials/service_account.json`
7. Copy the service account email (looks like `xxx@yyy.iam.gserviceaccount.com`)
8. Share your Google Sheet with that email (Editor access)

### 2. Environment variables

```bash
cp .env.example .env
```

Fill in `.env`:
```
TELEGRAM_BOT_TOKEN=your_token_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_SHEET_ID=your_sheet_id_here
ERROR_GROUP_CHAT_ID=your_group_id_here
```

To find ERROR_GROUP_CHAT_ID:
- Add the bot to your error group
- Send `/start` in the group
- Bot will reply with the chat ID

### 3. Install dependencies

```bash
python3.11 -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 4. Run locally

```bash
python bot.py
```

### 5. Deploy to VPS

```bash
# On VPS
git clone https://github.com/your-username/Logistics-bot.git
cd Logistics-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # fill in real values
# copy credentials/service_account.json to server

# Create systemd service
sudo nano /etc/systemd/system/logistics-bot.service
```

Systemd service file:
```ini
[Unit]
Description=Logistics Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/logistics-bot
ExecStart=/home/logistics-bot/venv/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable logistics-bot
systemctl start logistics-bot
```

## Google Sheet structure

### Malumotnoma sheet (reference data)
- Column B: TV davlat raqami
- Column C: Haydovchi
- Column D: Transport turi
- Column H: Punktlar
- Column I: Mijozlar
- Column K: Shartnoma raqamlari

### Reyslar sheet (output)
- A: Sana
- B: Reys ID
- C: Jo'natish nuqtasi
- D: Yetkazish nuqtasi
- E: Mijoz
- F: Shartnoma raqami
- G: Yuk
- H: Transport turi
- I: TV davlat raqami
- J: Haydovchi
- K: Naqd tushum
- L: Naqdsiz tushum
- M: Jami tushum
