import os
from typing import Final

from typing import Dict
from telegram.ext import MessageHandler, filters
from .ollama import OllamaClient
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from .texts import (
	START_TEXT, 
	HELP_TEXT, 
	RULES_TEXT, 
	DICE_RULES_TEXT,
	COMBAT_RULES_TEXT_PART1,
	COMBAT_RULES_TEXT_PART2,
	COMBAT_RULES_TEXT_PART3,
	COMBAT_RULES_TEXT_PART4,
	STATS_TEXT_PART1,
	STATS_TEXT_PART2,
	GLOSSARY_TEXT_PART1,
	GLOSSARY_TEXT_PART2
)


ollama_client = OllamaClient()

def load_env() -> None:
	load_dotenv()


def get_bot_token() -> str:
	load_env()
	bot_token: Final[str | None] = os.getenv("TELEGRAM_BOT_TOKEN")
	if not bot_token:
		raise RuntimeError(
			"TELEGRAM_BOT_TOKEN is not set. Create a .env file or set the environment variable."
		)
	return bot_token

user_sessions: Dict[int, Dict[str, str]] = {}

class UserSession:
    """Управляет состоянием сессии пользователя"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.current_section = "rules"  # по умолчанию раздел "Основные правила"
        self.section_content = RULES_TEXT
    
    @staticmethod
    def get_or_create(user_id: int) -> "UserSession":
        """Получить или создать сессию пользователя"""
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                "section": "rules",
                "content": RULES_TEXT
            }
        return user_sessions.get(user_id)
    
    def set_section(self, section: str, content: str) -> None:
        """Установить текущий раздел"""
        user_sessions[self.user_id] = {
            "section": section,
            "content": content
        }
    
    def get_current_section(self) -> tuple[str, str]:
        """Получить название и содержимое текущего раздела"""
        session = user_sessions.get(self.user_id, {
            "section": "rules",
            "content": RULES_TEXT
        })
        return session.get("section", "rules"), session.get("content", RULES_TEXT)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	"""Обработчик обычных текстовых сообщений через Ollama"""
	if not update.message or not update.message.text:
		return

	user_id = update.effective_user.id
	# Получаем текущий раздел пользователя
	user_message = update.message.text

	section_name, section_content = UserSession(user_id).get_current_section()

	# Определяем использовать ли RAG
	use_rag = section_name in ["races", "spells"]
	rag_section_type = section_name if use_rag else ""

	await update.message.chat.send_action("typing")

	response = ollama_client.generate_response(
		user_message=user_message,
		section_name=section_name,
		section_content=section_content,
		use_rag=use_rag,
		rag_section_type=rag_section_type
	)

	if response:
		await update.message.reply_text(response, parse_mode=ParseMode.HTML)
	else:
		await update.message.reply_text(
			"❌ Не удалось получить ответ. Проверь подключение к Ollama."
		)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(START_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("rules", RULES_TEXT)
		await update.message.reply_text(RULES_TEXT, parse_mode=ParseMode.HTML)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(START_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("rules", RULES_TEXT)
		await update.message.reply_text(RULES_TEXT, parse_mode=ParseMode.HTML)


async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("dice", DICE_RULES_TEXT)
		await update.message.reply_text(DICE_RULES_TEXT, parse_mode=ParseMode.HTML)


async def cmd_combat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("combat", COMBAT_RULES_TEXT_PART1 + COMBAT_RULES_TEXT_PART2 + COMBAT_RULES_TEXT_PART3 + COMBAT_RULES_TEXT_PART4)
		# Split large text into multiple messages
		combat_parts = [
			COMBAT_RULES_TEXT_PART1,
			COMBAT_RULES_TEXT_PART2,
			COMBAT_RULES_TEXT_PART3,
			COMBAT_RULES_TEXT_PART4
		]
		
		for part in combat_parts:
			await update.message.reply_text(part, parse_mode=ParseMode.HTML)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("stats", STATS_TEXT_PART1 + STATS_TEXT_PART2)
		# Split large text into multiple messages
		combat_parts = [
			STATS_TEXT_PART1,
			STATS_TEXT_PART2,
		]
		
		for part in combat_parts:
			await update.message.reply_text(part, parse_mode=ParseMode.HTML)

async def cmd_glossary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message and update.effective_user:
		user_id = update.effective_user.id
		# Сохраняем текущий раздел пользователя
		session = UserSession(user_id)
		session.set_section("glossary", GLOSSARY_TEXT_PART1 + GLOSSARY_TEXT_PART2)
		# Split large text into multiple messages
		glossary_parts = [
			GLOSSARY_TEXT_PART1,
			GLOSSARY_TEXT_PART2,
		]
		
		for part in glossary_parts:
			await update.message.reply_text(part, parse_mode=ParseMode.HTML)
	app.run_polling()

def main() -> None:
	token = get_bot_token()
	app = ApplicationBuilder().token(token).build()

	# Register handlers for D&D helper bot
	app.add_handler(CommandHandler("start", cmd_start))
	app.add_handler(CommandHandler("help", cmd_help))
	app.add_handler(CommandHandler("rules", cmd_rules))
	app.add_handler(CommandHandler("dice", cmd_dice))
	app.add_handler(CommandHandler("combat", cmd_combat))
	app.add_handler(CommandHandler("stats", cmd_stats))
	app.add_handler(CommandHandler("glossary", cmd_glossary))

	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

	print("🎲 D&D Helper Bot is starting... Press Ctrl+C to stop.")
	app.run_polling()


if __name__ == "__main__":
	main()
