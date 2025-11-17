import os
from typing import Final

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
	STATS_TEXT_PART2
)


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


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(START_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(RULES_TEXT, parse_mode=ParseMode.HTML)


async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
		await update.message.reply_text(DICE_RULES_TEXT, parse_mode=ParseMode.HTML)


async def cmd_combat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	if update.message:
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
	if update.message:
		# Split large text into multiple messages
		combat_parts = [
			STATS_TEXT_PART1,
			STATS_TEXT_PART2,
		]
		
		for part in combat_parts:
			await update.message.reply_text(part, parse_mode=ParseMode.HTML)


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

	print("🎲 D&D Helper Bot is starting... Press Ctrl+C to stop.")
	app.run_polling()


if __name__ == "__main__":
	main()
