import os
from logic import DB_Manager
from config1 import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

manager = DB_Manager(DATABASE)
bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove() 

cancel_button = "Отмена 🚫"

PHOTO_FOLDER = "project_photos"
os.makedirs(PHOTO_FOLDER, exist_ok=True)

def cansel(message):
    """Функция отмены текущего действия"""
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)

# Функция, если у пользователя нет проектов
def no_projects(message):
    bot.send_message(message.chat.id, 'У тебя пока нет проектов!\nМожешь добавить их с помощью команды /new_project')

# Генерация инлайн-клавиатуры
def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup(row_width=1)
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup

# Генерация reply-клавиатуры (одноразовой)
def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup
attributes_of_projects = {
    'Имя проекта': ["Введите новое имя проекта", "project_name"],
    "Описание": ["Введите новое описание проекта", "description"],
    "Ссылка": ["Введите новую ссылку на проект", "url"],
    "Статус": ["Выберите новый статус задачи", "status_id"]
}
def get_status_keyboard(statuses):
    keyboard = InlineKeyboardMarkup()
    for status_id, status_name in statuses:
        keyboard.add(InlineKeyboardButton(text=status_name, callback_data=f"status_{status_id}"))
    return keyboard

def save_photo(file_id, file_name):
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = os.path.join(PHOTO_FOLDER, file_name)
    with open(file_path, "wb") as new_file:
        new_file.write(downloaded_file)
    return file_path

@bot.message_handler(commands=['add_photo'])
def add_photo_command(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        project_names = [x[2] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, к которому хочешь добавить фото:", reply_markup=gen_markup(project_names))
        bot.register_next_step_handler(message, request_photo, project_names=project_names)
    else:
        bot.send_message(message.chat.id, "У тебя пока нет проектов!")

def request_photo(message, project_names):
    project_name = message.text
    if project_name not in project_names:
        bot.send_message(message.chat.id, "Такого проекта нет, попробуй еще раз!", reply_markup=gen_markup(project_names))
        bot.register_next_step_handler(message, request_photo, project_names=project_names)
        return
    bot.send_message(message.chat.id, "Отправь фото проекта!")
    bot.register_next_step_handler(message, save_project_photo, project_name=project_name)

def save_project_photo(message, project_name):
    if not message.photo:
        bot.send_message(message.chat.id, "Это не фото! Попробуй снова!")
        bot.register_next_step_handler(message, save_project_photo, project_name=project_name)
        return
    file_id = message.photo[-1].file_id
    file_name = f"{project_name}_{message.from_user.id}.jpg"
    file_path = save_photo(file_id, file_name)
    manager.update_project_photo(project_name, message.from_user.id, file_path)
    bot.send_message(message.chat.id, "Фото успешно сохранено!")

# Получение информации о проекте
def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name) or 'Навыки пока не добавлены'
    photo_path = info[4] if len(info) > 4 else None
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        for project in projects:
            project_id = project[0]
            project_name = project[2]
            description = project[3]
            link = project[4]
            photo_path = project[6]
    status = manager.get_status_name(project[5]) if hasattr(manager, "get_status_name") else "Статус не найден"
    skills = manager.get_project_skills(project_id) if hasattr(manager, "get_project_skills") else []
    if isinstance(skills, list):
        skills = ', '.join(skills) if skills else "Навыки пока не добавлены"
    
    caption_text = (f"📌 <b>Название проекта:</b> {project_name}\n"
                            f"📖 <b>Описание:</b> {description}\n"
                            f"🔗 <b>Ссылка:</b> {link}\n"
                            f"⚡️ <b>Статус:</b> {status}\n"
                            f"🛠 <b>Навыки:</b> {skills}\n"
                            "────────────────────────\n\n")
    if photo_path:
        bot.send_photo(message.chat.id, open(photo_path, 'rb'), caption=caption_text, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, caption_text, parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, """
Привет! 🤖 Я бот-менеджер проектов!
Помогу тебе сохранить твои проекты и информацию о них! 🚀

Используй /info, чтобы узнать команды.
""", parse_mode='HTML')
    info(message)

    
@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, """
📌 <b>Доступные команды:</b>

/new_project - Добавить новый проект 🆕  
/projects - Посмотреть список проектов 📜  
/delete - Удалить проект ❌  
/skills - Добавить навык к проекту 🛠  
/update_projects - Обновить информацию о проекте 🔄  
/add_photo - Добавить фото к проекту 📷  

🔍 Ты можешь просто ввести имя проекта, и я покажу его информацию!  
""", parse_mode='HTML')

@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    bot.send_message(message.chat.id, "Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "Введите описание проекта:")
    bot.register_next_step_handler(message, description_project, data=data)

def description_project(message, data):
    data.append(message.text)  # Добавляем описание
    bot.send_message(message.chat.id, "Введите ссылку на проект:")
    bot.register_next_step_handler(message, link_project, data=data)

def link_project(message, data):
    data.append(message.text)
    statuses = [x[1] for x in manager.get_statuses()] 
    bot.send_message(message.chat.id, "Введите текущий статус проекта", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

def callback_project(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in [x[1] for x in manager.get_statuses()]:
        bot.send_message(message.chat.id, "Ты выбрал статус не из списка, попробуй еще раз!", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    
    manager.insert_project([tuple(data)])  # Теперь передается 5 значений
    bot.send_message(message.chat.id, "Проект сохранен!")



@bot.message_handler(commands=['skills'])
def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)


def skill_project(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, 'Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
        
    if skill not in skills:
        bot.send_message(message.chat.id, 'Видимо, ты выбрал навык. не из спика, попробуй еще раз!) Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    
    project_id = manager.get_project_id(project_name, user_id)
    skill_id = manager.get_skill_id(skill)  

    if project_id and skill_id:
        manager.insert_skill(project_id, skill_id)  
        bot.send_message(message.chat.id, f'Навык {skill} добавлен проекту {project_name}')
    else:
        bot.send_message(message.chat.id, "Ошибка: проект или навык не найдены.")


@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)

    if projects:
        for project in projects:
            project_id = project[0]
            project_name = project[2]
            description = project[3]
            link = project[4]
            photo_path = project[6]  # Получаем путь к фото из базы

            status = manager.get_status_name(project[5]) if hasattr(manager, "get_status_name") else "Статус не найден"
            skills = manager.get_project_skills(project_id) if hasattr(manager, "get_project_skills") else []
            if isinstance(skills, list):
                skills = ', '.join(skills) if skills else "Навыки пока не добавлены"

            caption_text = (f"📌 <b>Название проекта:</b> {project_name}\n"
                            f"📖 <b>Описание:</b> {description}\n"
                            f"🔗 <b>Ссылка:</b> {link}\n"
                            f"⚡️ <b>Статус:</b> {status}\n"
                            f"🛠 <b>Навыки:</b> {skills}\n"
                            "────────────────────────\n\n")

            # Если у проекта есть фото, отправляем его, иначе только текст
            if photo_path:
                bot.send_photo(message.chat.id, open(photo_path, 'rb'), caption=caption_text, parse_mode='HTML')
            else:
                bot.send_message(message.chat.id, caption_text, parse_mode='HTML')

        # markup = gen_inline_markup([x[2] for x in projects])  # Кнопки с проектами
        # bot.send_message(message.chat.id, "Выбери проект для взаимодействия:", reply_markup=markup)
    else:
        no_projects(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)

@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    
    if projects:
        text = "Выбери проект, который хочешь удалить:\n\n"
        text += "\n".join([f"📌 {x[2]}" for x in projects])
        project_names = [x[2] for x in projects]
        
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(project_names))
        bot.register_next_step_handler(message, delete_project, project_names=project_names)
    else:
        no_projects(message)

def delete_project(message, project_names):
    project_name = message.text
    user_id = message.from_user.id

    if project_name == cancel_button:
        cansel(message)
        return

    if project_name not in project_names:
        bot.send_message(message.chat.id, "❌ У тебя нет такого проекта! Попробуй еще раз.", reply_markup=gen_markup(project_names))
        bot.register_next_step_handler(message, delete_project, project_names=project_names)
        return

    # Получаем project_id перед удалением
    project_id = manager.get_project_id(project_name, user_id)
    if not project_id:
        bot.send_message(message.chat.id, "❌ Проект не найден! Возможно, он уже удален.")
        return

    # Удаляем проект
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f"✅ Проект <b>{project_name}</b> успешно удален!", parse_mode="HTML")

# @bot.message_handler(commands=['delete'])
# def delete_handler(message):           
#     user_id = message.from_user.id
#     projects = manager.get_projects(user_id)
#     if projects:
#         text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
#         projects = [x[2] for x in projects]
#         bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects))
#         bot.register_next_step_handler(message, delete_project, projects=projects)
#     else:
#         no_projects(message)

# def delete_project(message, projects):
#     project = message.text
#     user_id = message.from_user.id

#     if message.text == cancel_button:
#         cansel(message)
#         return
#     if project not in projects:
#         bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй выбрать еще раз!', reply_markup=gen_markup(projects))
#         bot.register_next_step_handler(message, delete_project, projects=projects)
#         return
#     project_id = manager.get_project_id(project)
#     manager.delete_project(user_id, project_id)
#     bot.send_message(message.chat.id, f'Проект {project} удален!')


@bot.message_handler(commands=['update_projects'])
def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, который хочешь изменить", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
    else:
        no_projects(message)

def update_project_step_2(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так!) Выбери проект, который хочешь изменить еще раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
        return
    bot.send_message(message.chat.id, "Выбери, что требуется изменить в проекте", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

def update_project_step_3(message, project_name):
    attribute = message.text
    reply_markup = None 
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся, попробуй еще раз!)", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup=gen_markup([x[1] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup = reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

def update_project_step_4(message, project_name, attribute): 
    update_info = message.text
    if attribute == "status_id":
        rows = manager.get_statuses()
        
        status_names = [x[1] for x in rows]  # Берем названия статусов

        if update_info in status_names:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
            return
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй еще раз!)", reply_markup=gen_markup(status_names))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)

    bot.send_message(message.chat.id, "Готово! Обновления внесены!)")



@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects =[ x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "Тебе нужна помощь?")
    info(message)

    
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()