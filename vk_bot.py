import sys
import random
import redis as r
import vk_api as vk
from urllib.parse import urlparse
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from questions_processing import create_questions_dict, is_correct_answer
from environs import Env
import logging


def init_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    return keyboard


def send_message(event, vk_api, keyboard, message):
    vk_api.messages.send(
        user_id=event.user_id,
        message=message,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def send_new_question(event, vk_api, redis, questions):
    keyboard = init_keyboard()

    if not redis:
        return

    random_question = random.choice(list(questions.items()))
    redis.set(str(event.user_id), random_question[0], 600)
    message = random_question[1]['question']
    send_message(event, vk_api, keyboard, message)


def new_messages_handler(event, vk_api, redis, questions):
    keyboard = init_keyboard()

    if not redis:
        return

    match event.text:
        case 'Новый вопрос':
            send_new_question(event, vk_api, redis, questions)

        case 'Сдаться':
            if not redis.get(str(event.user_id)):
                message = 'Получите сначала вопрос. Еще рано сдаваться)'
                send_message(event, vk_api, keyboard, message)
            else:
                answer_text = questions[f'{redis.get(str(event.user_id))}']['answer']
                message = f'Правильный ответ:\n{answer_text}\n\n\n'
                send_message(event, vk_api, keyboard, message)
                send_new_question(event, vk_api, redis, questions)
        case 'Мой счет':
            pass

        case _:
            if not redis.get(str(event.user_id)):
                message = 'Ответ остался без вопроса. Получите новый вопрос.'
                send_message(event, vk_api, keyboard, message)
            else:
                answer_text = questions[f'{redis.get(str(event.user_id))}']['answer']
                if not is_correct_answer(answer_text, event.text):
                    message = 'Неправильно… Попробуешь ещё раз?'
                    send_message(event, vk_api, keyboard, message)
                else:
                    redis.delete(str(event.user_id))
                    message = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
                    send_message(event, vk_api, keyboard, message)


def main():
    env = Env()
    env.read_env()

    try:
        questions = create_questions_dict(env.str('FILENAME'))
    except FileNotFoundError:
        sys.stdout.write('Файл не найден.')
        exit()

    vk_token = env.str('VK_TOKEN')
    redis_uri = urlparse(env.str('REDIS_URI'))
    redis = r.StrictRedis(
        host=redis_uri.hostname,
        port=int(redis_uri.port),
        password=redis_uri.password,
        charset='utf-8',
        decode_responses=True
    )

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        filename="vk_bot.log",
        filemode="w"
    )
    logging.info('Бот запущен')

    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                new_messages_handler(event, vk_api, redis, questions)
    except Exception as err:
        logging.exception(err)


if __name__ == "__main__":
    main()
