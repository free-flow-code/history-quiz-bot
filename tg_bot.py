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


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_markdown_v2(
        fr'Здравствуйте {user.mention_markdown_v2()}\! Есть три кнопки. Какую нажмете?',
        reply_markup=reply_markup,
    )

    return CHOOSING


def handle_new_question_request(update: Update, context: CallbackContext):
    redis_uri = urlparse(env.str('REDIS_URI'))
    r = redis.StrictRedis(
        host=redis_uri.hostname,
        port=int(redis_uri.port),
        password=redis_uri.password,
        charset='utf-8',
        decode_responses=True
    )
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    random_question = random.choice(list(QUESTIONS.items()))

    try:
        r.set(str(update.message.from_user.id), random_question[0], 600)
    except redis.exceptions.ConnectionError:
        send_error_msg(update, reply_markup)
        return CHOOSING

    update.message.reply_text(
        text=random_question[1]['question'],
        reply_markup=reply_markup
    )

    return TYPING_REPLY


def handle_solution_attempt(update: Update, context: CallbackContext):
    redis_uri = urlparse(env.str('REDIS_URI'))
    r = redis.StrictRedis(
        host=redis_uri.hostname,
        port=int(redis_uri.port),
        password=redis_uri.password,
        charset='utf-8',
        decode_responses=True
    )
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    try:
        if not r.get(str(update.message.from_user.id)):
            update.message.reply_text(
                text='Ответ остался без вопроса. Получите новый вопрос.',
                reply_markup=reply_markup
            )
            return CHOOSING
        answer_text = QUESTIONS[f'{r.get(str(update.message.from_user.id))}']['answer']
    except redis.exceptions.ConnectionError:
        send_error_msg(update, reply_markup)
        return TYPING_REPLY

    if not is_correct_answer(answer_text, update.message.text):
        update.message.reply_text(
            text='Неправильно… Попробуешь ещё раз?',
            reply_markup=reply_markup
        )
        return TYPING_REPLY
    update.message.reply_text(
        text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
        reply_markup=reply_markup
    )
    return CHOOSING


def give_up(update: Update, context: CallbackContext):
    redis_uri = urlparse(env.str('REDIS_URI'))
    r = redis.StrictRedis(
        host=redis_uri.hostname,
        port=int(redis_uri.port),
        password=redis_uri.password,
        charset='utf-8',
        decode_responses=True
    )
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    random_question = random.choice(list(QUESTIONS.items()))

    try:
        if not r.get(str(update.message.from_user.id)):
            update.message.reply_text(
                text='Получите сначала вопрос. Еще рано сдаваться)',
                reply_markup=reply_markup
            )
            return CHOOSING
        answer_text = QUESTIONS[f'{r.get(str(update.message.from_user.id))}']['answer']
        r.set(str(update.message.from_user.id), random_question[0], 600)
    except redis.exceptions.ConnectionError:
        send_error_msg(update, reply_markup)
        return TYPING_REPLY

    update.message.reply_text(
        text=f'Правильный ответ:\n{answer_text}\n\n\n'
             f'Попробуйте ответить на этот вопрос:\n{random_question[1]["question"]}',
        reply_markup=reply_markup
    )
    return TYPING_REPLY


def cancel(bot, update):
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, err):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, err)


def send_error_msg(update: Update, reply_markup: ReplyKeyboardMarkup):
    update.message.reply_text(
        text='Сервис временно не доступен. Попробуйте позже.',
        reply_markup=reply_markup
    )


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
                MessageHandler(Filters.regex(r'Сдаться'), give_up)
            ],
            states={
                CHOOSING: [
                    MessageHandler(Filters.regex(r'Новый вопрос'), handle_new_question_request),
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
