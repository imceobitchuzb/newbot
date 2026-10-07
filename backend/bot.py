"""Telegram Bot runner for SAT MASTER Mini App with 24/7 resilience and persistent menu."""
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
    "🎯 *SAT MASTER — Твой путь к 1400+ на Digital SAT*\n\n"
    "Привет! Это официальный бот и Mini App для умной подготовки к Digital SAT.\n\n"
    "✨ *Что внутри тренажера:*\n"
    "• 🎯 *Diagnostic Module* — точная калибровка начального балла (Math + Reading & Writing)\n"
    "• 📐 *Desmos Lab* — 12 канонических техник решения SAT за секунды (калькулятор встроен прямо в приложение!)\n"
    "• 🤖 *AI SAT Tutor* — персональный наставник по задачам и стратегиям\n"
    "• 📈 *Adaptive Math Practice* — подбор сложности под твои слабые темы\n"
    "• 📕 *Mistake Book* — интервальное повторение ошибок (+1d, +3d, +7d)\n\n"
    "👇 Нажми на кнопку ниже или используй постоянное меню внизу экрана!"
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
        resp = await client.post(url, json=payload, timeout=12.0)
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return None


async def setup_bot_interface(client: httpx.AsyncClient, token: str, webapp_url: str):
    """Sets up Telegram native menu button, commands, and descriptions."""
    try:
        # 1. Set Chat Menu Button (permanent Mini App button on the bottom-left of input field)
        menu_btn_resp = await client.post(
            f"{TELEGRAM_API}{token}/setChatMenuButton",
            json={
                "menu_button": {
                    "type": "web_app",
                    "text": "🚀 SAT MASTER",
                    "web_app": {"url": webapp_url}
                }
            },
            timeout=10.0
        )
        logger.info(f"Set chat menu button: {menu_btn_resp.status_code}")

        # 2. Set Bot Commands
        commands_resp = await client.post(
            f"{TELEGRAM_API}{token}/setMyCommands",
            json={
                "commands": [
                    {"command": "start", "description": "🚀 Запустить тренажер SAT MASTER"},
                    {"command": "desmos", "description": "📐 Открыть Desmos Lab со встроенным калькулятором"},
                    {"command": "tutor", "description": "🤖 AI SAT Репетитор"},
                    {"command": "diagnostic", "description": "🎯 Диагностический тест"},
                    {"command": "help", "description": "📚 Справка и возможности"}
                ]
            },
            timeout=10.0
        )
        logger.info(f"Set bot commands: {commands_resp.status_code}")

        # 3. Set Short Description
        await client.post(
            f"{TELEGRAM_API}{token}/setMyShortDescription",
            json={"short_description": "🎯 Тренажер Digital SAT 1400+ со встроенным Desmos и AI Тьютором"},
            timeout=10.0
        )
    except Exception as e:
        logger.warning(f"Could not setup bot interface: {e}")


def get_keyboards(webapp_url: str):
    """Generates both inline keyboard and persistent reply keyboard."""
    inline_keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🚀 Открыть SAT MASTER",
                    "web_app": {"url": webapp_url}
                }
            ],
            [
                {
                    "text": "📐 Desmos Lab (Калькулятор внутри)",
                    "web_app": {"url": f"{webapp_url}/desmos"}
                }
            ],
            [
                {
                    "text": "🤖 AI SAT Репетитор",
                    "web_app": {"url": f"{webapp_url}/tutor"}
                },
                {
                    "text": "🎯 Диагностика",
                    "web_app": {"url": f"{webapp_url}/diagnostic"}
                }
            ],
            [
                {
                    "text": "🌐 Открыть в браузере (прямая ссылка)",
                    "url": webapp_url
                }
            ]
        ]
    }

    # Persistent keyboard fixed at the bottom of the screen (never disappears)
    persistent_keyboard = {
        "keyboard": [
            [
                {"text": "🚀 Открыть SAT MASTER", "web_app": {"url": webapp_url}},
                {"text": "📐 Desmos Lab", "web_app": {"url": f"{webapp_url}/desmos"}},
            ],
            [
                {"text": "🤖 AI Репетитор", "web_app": {"url": f"{webapp_url}/tutor"}},
                {"text": "🎯 Диагностика", "web_app": {"url": f"{webapp_url}/diagnostic"}},
            ],
            [
                {"text": "🔄 /start"}
            ]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }

    return inline_keyboard, persistent_keyboard


async def poll_updates(client: httpx.AsyncClient, token: str, webapp_url: str):
    """Main polling loop with command routing and smart fallback."""
    inline_kb, persistent_kb = get_keyboards(webapp_url)
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
                    text = (message.get("text") or "").strip()
                    user_name = message.get("from", {}).get("first_name", "Друг")

                    lower_text = text.lower()

                    if lower_text.startswith("/start") or lower_text in ["start", "старт", "начать", "меню", "заново", "перезапустить"]:
                        greeting = (
                            f"👋 Привет, {user_name}!\n\n"
                            f"{WELCOME_TEXT}\n\n"
                            f"🔗 Прямой адрес: {webapp_url}\n"
                            f"📐 Desmos Lab: {webapp_url}/desmos"
                        )
                        # Send with persistent keyboard to dock buttons permanently
                        await send_message(client, token, chat_id, greeting, persistent_kb)
                        # Also send inline keyboard for direct one-tap opening
                        await send_message(client, token, chat_id, "Выбери раздел для старта 👇", inline_kb)

                    elif lower_text.startswith("/desmos") or "desmos" in lower_text or "десмос" in lower_text:
                        desmos_text = (
                            "📐 *Desmos Lab — Секретное оружие на Digital SAT Math*\n\n"
                            "В SAT MASTER калькулятор Desmos встроен прямо в интерфейс!\n"
                            "Ты можешь практиковать 12 канонических техник:\n"
                            "• Регрессии `y1 ~ mx1 + b`\n"
                            "• Пересечения систем уравнений\n"
                            "• Слайдеры для параметров\n"
                            "• Поиск экстремумов и корней\n\n"
                            "Нажми кнопку ниже, чтобы открыть интерактивный Desmos Lab 👇"
                        )
                        desmos_kb = {
                            "inline_keyboard": [
                                [{"text": "📐 Открыть Desmos Lab", "web_app": {"url": f"{webapp_url}/desmos"}}],
                                [{"text": "🌐 В браузере", "url": f"{webapp_url}/desmos"}]
                            ]
                        }
                        await send_message(client, token, chat_id, desmos_text, desmos_kb)

                    elif lower_text.startswith("/tutor") or "репетитор" in lower_text or "tutor" in lower_text:
                        tutor_text = (
                            "🤖 *AI SAT Репетитор*\n\n"
                            "Твой персональный наставник объяснит любую задачу, разберет ошибки и научит тактике.\n"
                            "Открой AI Репетитора нажатием на кнопку 👇"
                        )
                        tutor_kb = {
                            "inline_keyboard": [
                                [{"text": "🤖 Открыть AI Репетитора", "web_app": {"url": f"{webapp_url}/tutor"}}],
                                [{"text": "🌐 В браузере", "url": f"{webapp_url}/tutor"}]
                            ]
                        }
                        await send_message(client, token, chat_id, tutor_text, tutor_kb)

                    elif lower_text.startswith("/diagnostic") or "диагностик" in lower_text:
                        diag_text = (
                            "🎯 *Диагностический тест SAT MASTER*\n\n"
                            "40 вопросов для точного определения текущего уровня (Math + R&W).\n"
                            "Пройди диагностику, чтобы выявить слабые места и получить персональный план."
                        )
                        diag_kb = {
                            "inline_keyboard": [
                                [{"text": "🎯 Начать диагностику", "web_app": {"url": f"{webapp_url}/diagnostic"}}]
                            ]
                        }
                        await send_message(client, token, chat_id, diag_text, diag_kb)

                    elif lower_text.startswith("/help") or "помощь" in lower_text or "help" in lower_text:
                        help_text = (
                            "📚 *Возможности SAT MASTER:*\n\n"
                            "• /start — Запустить приложение и открыть меню\n"
                            "• /desmos — Встроенный калькулятор Desmos и 12 техник\n"
                            "• /tutor — Персональный AI SAT Тьютор\n"
                            "• /diagnostic — Калибровочный тест на 40 вопросов\n\n"
                            "💡 *Совет:* Внизу экрана всегда доступны быстрые кнопки запуска. "
                            "Также слева от поля ввода текста есть кнопка меню '🚀 SAT MASTER'!"
                        )
                        await send_message(client, token, chat_id, help_text, persistent_kb)

                    else:
                        reply = (
                            f"💡 Привет, {user_name}! Чтобы открыть тренажер или встроенный Desmos, "
                            f"нажми одну из кнопок внизу экрана или перейди по ссылке: {webapp_url}"
                        )
                        await send_message(client, token, chat_id, reply, persistent_kb)
            else:
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"Polling loop hiccup: {e}")
            await asyncio.sleep(3)


async def run_bot_24_7():
    """24/7 supervisor loop that automatically reconnects on any failure."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured in settings.")
        return

    webapp_url = os.getenv("TELEGRAM_WEBAPP_URL", settings.TELEGRAM_WEBAPP_URL or "https://recipes-untitled-varieties-wishing.trycloudflare.com")
    logger.info(f"Starting 24/7 SAT MASTER Telegram Bot with WebApp URL: {webapp_url}")

    consecutive_errors = 0
    while True:
        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                me_resp = await client.get(f"{TELEGRAM_API}{token}/getMe")
                me_data = me_resp.json()
                if not me_data.get("ok"):
                    logger.error(f"Telegram getMe failed: {me_data}")
                    await asyncio.sleep(10)
                    continue

                bot_user = me_data["result"]
                logger.info(f"Connected as @{bot_user.get('username')} ({bot_user.get('first_name')}). Configuring UI...")

                # Setup chat menu button and commands
                await setup_bot_interface(client, token, webapp_url)
                consecutive_errors = 0

                logger.info("Bot interface configured. Entering 24/7 polling loop...")
                await poll_updates(client, token, webapp_url)

        except asyncio.CancelledError:
            logger.info("Bot supervisor received cancellation signal.")
            break
        except Exception as e:
            consecutive_errors += 1
            backoff = min(30, 2 ** consecutive_errors)
            logger.error(f"Bot error ({e}). Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)


if __name__ == "__main__":
    try:
        asyncio.run(run_bot_24_7())
    except KeyboardInterrupt:
        logger.info("Bot shut down cleanly.")
