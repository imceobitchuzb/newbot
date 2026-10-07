"""Telegram Bot runner for SAT MASTER Mini App."""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import httpx
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sat_master_bot")

TELEGRAM_API = "https://api.telegram.org/bot"

WELCOME_TEXT = (
    "🎯 **SAT MASTER — Твой путь к 1400+ на Digital SAT**\n\n"
    "Привет! Это официальный бот и Mini App для подготовки к Digital SAT.\n\n"
    "✨ **Что внутри:**\n"
    "• **Diagnostic Module**: точная калибровка начального балла (Math + Reading & Writing)\n"
    "• **Adaptive Math Practice**: умная система адаптации сложности под твои пробелы\n"
    "• **Mistake Book**: умный банк ошибок с интервальным повторением (+1d, +3d, +7d)\n"
    "• **Desmos Lab**: 12 канонических техник решения SAT за секунды\n"
    "• **AI SAT Tutor**: персональный наставник по задачам и стратегиям\n\n"
    "👇 Нажми кнопку ниже, чтобы запустить тренажер!"
)


async def send_message(client: httpx.AsyncClient, token: str, chat_id: int, text: str, reply_markup: dict | None = None):
    url = f"{TELEGRAM_API}{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        resp = await client.post(url, json=payload, timeout=10.0)
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return None


async def run_bot():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set.")
        return

    logger.info("Starting SAT MASTER Telegram Bot polling...")
    
    # Check bot info
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            me_resp = await client.get(f"{TELEGRAM_API}{token}/getMe")
            me_data = me_resp.json()
            if me_data.get("ok"):
                bot_user = me_data["result"]
                logger.info(f"Connected as @{bot_user.get('username')} ({bot_user.get('first_name')})")
            else:
                logger.error(f"Invalid token: {me_data}")
                return
        except Exception as e:
            logger.error(f"Error checking bot token: {e}")
            return

        # Determine WebApp URL
        webapp_url = os.getenv("TELEGRAM_WEBAPP_URL", settings.TELEGRAM_WEBAPP_URL or "https://001214c36c6783.lhr.life")
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "🚀 Open SAT MASTER",
                        "web_app": {"url": webapp_url}
                    }
                ],
                [
                    {
                        "text": "📖 Desmos Lab (Embedded)",
                        "web_app": {"url": f"{webapp_url}/desmos"}
                    }
                ],
                [
                    {
                        "text": "🌐 Open in Browser (Direct Link)",
                        "url": webapp_url
                    }
                ]
            ]
        }

        offset = 0
        while True:
            try:
                updates_resp = await client.get(
                    f"{TELEGRAM_API}{token}/getUpdates",
                    params={"offset": offset, "timeout": 20},
                    timeout=25.0
                )
                updates = updates_resp.json()
                if updates.get("ok"):
                    for update in updates.get("result", []):
                        offset = max(offset, update["update_id"] + 1)
                        message = update.get("message")
                        if not message:
                            continue
                        chat_id = message.get("chat", {}).get("id")
                        text = message.get("text", "")

                        if text.startswith("/start"):
                            user_name = message.get("from", {}).get("first_name", "Friend")
                            greeting = (
                                f"👋 Привет, {user_name}!\n\n"
                                f"{WELCOME_TEXT}\n\n"
                                f"🔗 Ссылка для браузера: {webapp_url}\n"
                                f"📐 Desmos Lab: {webapp_url}/desmos"
                            )
                            await send_message(client, token, chat_id, greeting, keyboard)
                        elif text.startswith("/help"):
                            help_text = (
                                "📚 *Команды SAT MASTER:*\n"
                                "/start — Запустить приложение и открыть меню\n"
                                "/help — Список возможностей\n\n"
                                f"Прямая ссылка: {webapp_url}\n"
                                "Для начала тренировки нажмите кнопку 'Open SAT MASTER'!"
                            )
                            await send_message(client, token, chat_id, help_text, keyboard)
                        else:
                            await send_message(client, token, chat_id, f"Нажми кнопку ниже или перейди по ссылке: {webapp_url} 👇", keyboard)
                else:
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Polling warning: {e}")
                await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
