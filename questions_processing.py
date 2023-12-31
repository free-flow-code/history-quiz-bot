import re


def create_questions_dict(filename: str) -> dict:
    with open(filename, 'r', encoding='KOI8-R') as file:
        content = file.read()

    cutted_text = content[content.find('Вопрос'):]
    splitted_texts = cutted_text.split('\n\n\n')
    cleared_texts = [clear_text for clear_text in splitted_texts if 'Вопрос' in clear_text]
    questions = {}

    for question_index, question_details in enumerate(cleared_texts):
        question_start_index = question_details.find('\n')
        question_end_index = question_details.find('Ответ:')
        answer_start_index = re.search('Ответ:\n', question_details).span()[1]
        answer_end_index = answer_start_index + question_details[answer_start_index:].find('\n\n')
        questions.update(
            {
                str(question_index): {
                    'question': question_details[question_start_index:question_end_index].replace('\n', ' '),
                    'answer': question_details[answer_start_index:answer_end_index].replace('\n', '')
                }
            }
        )

    return questions


def is_correct_answer(answer_text, user_answer):
    correct_answer = re.split(r'[.(]', answer_text)[0]
    return user_answer.lower() == correct_answer.lower()
