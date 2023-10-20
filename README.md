## Бот для викторин на тему истории

- [Описание](#description)
- [Как установить](#install)
- [Запуск ботов](#start)
- [Ссылки на ботов](#links)
- [Пример работы ботов](#example)

### Описание <a name="description"></a>
Меню бота состоит из 3х кнопок: "Новый вопрос", "Сдаться", "Мой счет".
При нажатии на «Новый вопрос» пользователь просто получает новый вопрос.
Затем он проверяет ответы от пользователя на правильность. Если ответ не верный, он предложит
попробовать еще раз. При нажатии на кнопку «Сдаться» бот присылает пользователю
ответ на вопрос и следующим сообщением присылает следующий вопрос.
В качестве бызы данных используется Redis.

Вопросы и ответы должны храниться в текстовом файле и иметь определенную структуру:

```
Вопрос:
Текст вопроса. Между вопросом и ответом интервал в виде пустой строки.

Ответ:
Текст ответа. При проверке правильности бот учитывает только текст до первой точки
или открывающейся скобки. Все остальное будет считаться за пояснение и выведено при
нажатии на кнопку "Сдаться".


Вопрос:
Текст следующего вопроса. Между вопросами интервал должен составлять 2 пустых строки.

Ответ:
Текст ответа. И так далее... 
```
Путь к файлу с вопросами следует указать в переменной окружения `FILENAME`

Бот состоит из трех скриптов:

- **tg_bot.py** - бот для Telegram.

- **vk_bot.py** - бот для Вконтакте.

- **additional_funcs.py** - функции парсинга файла с вопросами/ответами и проверки
правильности ответа.

### Как установить <a name="install"></a>

Python не ниже версии 3.10 должен быть уже установлен. 
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```
pip install -r requirements.txt
```
Создайте телеграм бота с помощью [BotFather](https://t.me/BotFather), который выдаст
вам токен вида:

`5798143041:AXGbv_HjqQijxGjk4zbYBe5u8GiJhyDtAsd`

Создайте группу ВК и получите токен в Сообщество - Управление - Работа с API.

Для работы с базой данных Redis ваш uri должен иметь следующий вид:

`[CONNECTION_METHOD]://[USERNAME]:[PASSWORD]@[HOSTNAME]:[PORT]/[DATABASE]`

Например:

`redis://my_name:some_password@cloud.redislabs.com:15070/0`

Затем в директории с программой создайте `.env` файл:

```
TG_TOKEN='токен telegram бота'
VK_TOKEN='токен группы вк'
FILENAME='путь к файлу с вопросами/ответами'
REDIS_URI='ваш redis uri'
```

### Запуск ботов <a name="start"></a>
Все готово, теперь можно запускать ботов:

```
python telegram_bot.py
```
или
```
python vk_bot.py
```

### Ссылки на ботов <a name="links"></a>

**Telegram бота** можно потыкать [здесь](https://t.me/hhistory_quiz_bot).

**Vk бот** находится [тут](https://vk.com/public223056865).

### Пример работы ботов <a name="example"></a>

Пример бота для Telegram:

![](https://dvmn.org/filer/canonical/1569215494/324/)

Пример бота для Вконтакте:

![](https://dvmn.org/filer/canonical/1569215498/325/)