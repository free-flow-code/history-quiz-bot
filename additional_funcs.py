import re
import sys


def create_questions_dict(filename: str) -> dict:
    try:
        with open(filename, 'r', encoding='KOI8-R') as file:
            content = file.read()
    except FileNotFoundError:
        sys.stdout.write('Файл не найден.')
        exit()

    cutted_text = content[content.find('Вопрос'):]
    splitted_texts = cutted_text.split('\n\n\n')
    cleared_texts = [clear_text for clear_text in splitted_texts if 'Вопрос' in clear_text]
    questions = {}
    question_index = 0

    for question_details in cleared_texts:
        question_index += 1
        question_start_index = question_details.find('\n')
        question_end_index = question_details.find('Ответ:')
        answer_start_index = re.search('Ответ:\n', question_details).span()[1]
        answer_end_index = answer_start_index + question_details[answer_start_index:].find('\n\n')
        questions.update(
            {
                str(question_index): {
                    'question': question_details[question_start_index:question_end_index].replace('\n', ''),
                    'answer': question_details[answer_start_index:answer_end_index].replace('\n', '')
                }
            }
        )

    return questions
