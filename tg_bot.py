from environs import Env
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Здравствуйте {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def handle_text(update: Update, context: CallbackContext) -> None:
    """Handle the user message."""
    update.message.reply_text(update.message.text)


def main():
    env = Env()
    env.read_env()
    tg_token = env.str('TG_TOKEN')

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        filename="tg_bot.log",
        filemode="w"
    )
    logging.info('Бот запущен')

    try:
        updater = Updater(tg_token, use_context=True)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

        updater.start_polling()
    except Exception as err:
        logging.exception(err)


if __name__ == '__main__':
    main()
