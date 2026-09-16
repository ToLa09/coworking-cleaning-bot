import os

CLEANING_INTERVAL_WEEKS = os.environ["CLEANING_INTERVAL_WEEKS"]
ADMIN_IDS = {
    int(user_id)
    for user_id in os.environ["ADMIN_IDS"].split(",")
}
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GROUP_CHAT_ID = int(os.environ["GROUP_CHAT_ID"])