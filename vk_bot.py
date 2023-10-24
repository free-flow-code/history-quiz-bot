import sys
import random
import vk_api as vk
from urllib.parse import urlparse
from redis_funcs import init_redis
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from question_processing_funcs import create_questions_dict, is_correct_answer
from environs import Env
import logging

env = Env()
env.read_env()

try:
    QUESTIONS = create_questions_dict(env.str('FILENAME'))
except FileNotFoundError:
    sys.stdout.write('Файл не найден.')
    exit()


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


def send_new_question(event, vk_api):
    keyboard = init_keyboard()

    if not redis:
        return

    random_question = random.choice(list(QUESTIONS.items()))
    redis.set(str(event.user_id), random_question[0], 600)
    message = random_question[1]['question']
    send_message(event, vk_api, keyboard, message)


def echo(event, vk_api):
    keyboard = init_keyboard()

    if not redis:
        return

    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        match event.text:
            case 'Новый вопрос':
                send_new_question(event, vk_api)
            case 'Сдаться':
                if not redis.get(str(event.user_id)):
                    message = 'Получите сначала вопрос. Еще рано сдаваться)'
                    send_message(event, vk_api, keyboard, message)
                else:
                    answer_text = QUESTIONS[f'{redis.get(str(event.user_id))}']['answer']
                    message = f'Правильный ответ:\n{answer_text}\n\n\n'
                    send_message(event, vk_api, keyboard, message)
                    send_new_question(event, vk_api)
            case 'Мой счет':
                pass
            case _:
                if not redis.get(str(event.user_id)):
                    message = 'Ответ остался без вопроса. Получите новый вопрос.'
                    send_message(event, vk_api, keyboard, message)
                else:
                    answer_text = QUESTIONS[f'{redis.get(str(event.user_id))}']['answer']
                    if not is_correct_answer(answer_text, event.text):
                        message = 'Неправильно… Попробуешь ещё раз?'
                        send_message(event, vk_api, keyboard, message)
                    else:
                        redis.delete(str(event.user_id))
                        message = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
                        send_message(event, vk_api, keyboard, message)


if __name__ == "__main__":
    vk_token = env.str('VK_TOKEN')
    redis_uri = urlparse(env.str('REDIS_URI'))

    redis = init_redis(redis_uri)

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
                echo(event, vk_api)
    except Exception as err:
        logging.exception(err)
