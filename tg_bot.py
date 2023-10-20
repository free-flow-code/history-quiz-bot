import redis
import random
from environs import Env
from urllib.parse import urlparse
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from additional_funcs import create_questions_dict, is_correct_answer
import logging

logger = logging.getLogger(__name__)
env = Env()
env.read_env()
QUESTIONS = create_questions_dict(env.str('FILENAME'))
CHOOSING, TYPING_REPLY = range(2)


def init_reply_markup():
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    return ReplyKeyboardMarkup(keyboard)


def send_message(update: Update, reply_markup: ReplyKeyboardMarkup, message: str):
    update.message.reply_text(
        text=message,
        reply_markup=reply_markup
    )


def init_redis(update, reply_markup):
    redis_uri = urlparse(env.str('REDIS_URI'))
    try:
        r = redis.StrictRedis(
            host=redis_uri.hostname,
            port=int(redis_uri.port),
            password=redis_uri.password,
            charset='utf-8',
            decode_responses=True
        )
        r.ping()
        return r
    except redis.exceptions.ConnectionError:
        message = 'Сервис временно не доступен. Попробуйте позже.'
        send_message(update, reply_markup, message)


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    reply_markup = init_reply_markup()

    update.message.reply_markdown_v2(
        fr'Здравствуйте {user.mention_markdown_v2()}\! Есть три кнопки. Какую нажмете?',
        reply_markup=reply_markup,
    )

    return CHOOSING


def handle_new_question_request(update: Update, context: CallbackContext):
    reply_markup = init_reply_markup()
    r = init_redis(update, reply_markup)

    if not r:
        return CHOOSING

    random_question = random.choice(list(QUESTIONS.items()))
    r.set(str(update.message.from_user.id), random_question[0], 600)
    message = random_question[1]['question']
    send_message(update, reply_markup, message)

    return TYPING_REPLY


def handle_solution_attempt(update: Update, context: CallbackContext):
    reply_markup = init_reply_markup()
    r = init_redis(update, reply_markup)

    if not r:
        return TYPING_REPLY

    if not r.get(str(update.message.from_user.id)):
        message = 'Ответ остался без вопроса. Получите новый вопрос.'
        send_message(update, reply_markup, message)
        return CHOOSING

    answer_text = QUESTIONS[f'{r.get(str(update.message.from_user.id))}']['answer']

    if not is_correct_answer(answer_text, update.message.text):
        message = 'Неправильно… Попробуешь ещё раз?'
        send_message(update, reply_markup, message)
        return TYPING_REPLY

    r.delete(str(update.message.from_user.id))
    message = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
    send_message(update, reply_markup, message)
    return CHOOSING


def give_up(update: Update, context: CallbackContext):
    reply_markup = init_reply_markup()
    r = init_redis(update, reply_markup)
    random_question = random.choice(list(QUESTIONS.items()))

    if not r:
        return TYPING_REPLY

    if not r.get(str(update.message.from_user.id)):
        message = 'Получите сначала вопрос. Еще рано сдаваться)'
        send_message(update, reply_markup, message)
        return CHOOSING

    answer_text = QUESTIONS[f'{r.get(str(update.message.from_user.id))}']['answer']
    r.set(str(update.message.from_user.id), random_question[0], 600)
    message = f'Правильный ответ:\n{answer_text}\n\n\n'\
              f'Попробуйте ответить на этот вопрос:\n{random_question[1]["question"]}'
    send_message(update, reply_markup, message)
    return TYPING_REPLY


def cancel(bot, update):
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def error(bot, update, err):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, err)


def main():
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
        dp = updater.dispatcher
        handlers = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                MessageHandler(Filters.regex(r'Новый вопрос'), handle_new_question_request),
                MessageHandler(Filters.regex(r'Сдаться'), give_up),
                MessageHandler(Filters.text, handle_solution_attempt)
            ],
            states={
                CHOOSING: [
                    MessageHandler(Filters.regex(r'Новый вопрос'), handle_new_question_request),
                    MessageHandler(Filters.regex(r'Сдаться'), give_up),
                    MessageHandler(Filters.text, handle_solution_attempt)
                ],
                TYPING_REPLY: [
                    MessageHandler(Filters.regex(r'Сдаться'), give_up),
                    MessageHandler(Filters.text, handle_solution_attempt)
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        dp.add_handler(handlers)
        dp.add_error_handler(error)
        updater.start_polling()
    except Exception as err:
        logging.exception(err)


if __name__ == '__main__':
    main()
