import logging
import pandas as pd

from aiogram import Router
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, FSInputFile
from aiogram_dialog import DialogManager
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner

from bot.config_data.config import db, admins
from bot.handlers.other import start_logic

commands_router = Router()
text_not_permissions = 'У вас нет прав на это действие'


@commands_router.message(CommandStart())
async def process_start_command(
    msg: Message,
    state: FSMContext, 
    i18n: TranslatorRunner,
    dialog_manager: DialogManager
) -> None:
    # await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)
    await start_logic(msg, state, i18n)


@commands_router.message(Command('show'))
async def show_command(msg: Message) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return
    
    faculties = db.faculties.find({})
    text = 'Факультуты:\n'
    for faculty in faculties:
        text += faculty['faculty'] + '\n'

    await msg.answer(text)
    

@commands_router.message(Command('add'))
async def add_faculty_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return
    
    rows = command.args.split('\n')
    for i in range(len(rows)):
        db.faculties.insert_one({'faculty': rows[i], 'item': i})

    await msg.answer('Факультет добавлен')


@commands_router.message(Command('add_squads'))
async def add_faculty_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return
    
    rows = command.args.split('\n')
    for i in range(len(rows)):
        db.users.update_one({'mail': rows[i].lower()}, {'$set': {'squads': True}})

    await msg.answer('Отряды добавлены')


@commands_router.message(Command('del_squads'))
async def del_squads_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return
    
    mail = command.args.split('\n')
    for m in mail:
        db.users.update_one({'mail': m}, {'$unset': {'squads': True}})
    await msg.answer('Отряды удалены')


@commands_router.message(Command('del'))
async def del_faculty_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return
    
    db.faculties.delete_one({'faculty': command.args})
    await msg.answer('Факультет удален')


@commands_router.message(Command('del_all'))
async def del_faculty_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    db.faculties.delete_many({})
    await msg.answer('Факультеты удалены')


@commands_router.message(Command('event_start'))
async def event_start_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    number = int(command.args)

    db.info.update_one(
        {'active_event': 0},
        {'$set': {'active_event': number}}
    )
    await msg.answer('Голосование запущено')


@commands_router.message(Command('event_stop'))
async def event_stop_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    number = int(command.args)
    logging.info(number)

    db.info.update_one(
        {'active_event': number},
        {'$set': {'active_event': 0}}
    )
    await msg.answer('Голосование остановлено')


@commands_router.message(Command('replace_name'))
async def event_stop_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    last_name, new_name = command.args.split('\n')

    db.users.update_many(
        {'faculty': last_name},
        {'$set': {'faculty': new_name}}
    )
    await msg.answer('Имя заменено')


@commands_router.message(Command('add_kio'))
async def add_kio_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    mail = command.args.split('\n')
    for m in mail:
        db.users.update_one({'mail': m}, {'$set': {'kio': True}})
    await msg.answer('КИО добавлены')


@commands_router.message(Command('del_kio'))
async def del_kio_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    mail = command.args.split('\n')
    for m in mail:
        db.users.update_one({'mail': m}, {'$unset': {'kio': True}})
    await msg.answer('КИО удалены')


@commands_router.message(Command('drop_users'))
async def drop_users_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    db.users.delete_many({})
    await msg.answer('Пользователи удалены')


@commands_router.message(Command('get_result'))
async def get_result_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    number_event = command.args
    
    filename = 'result_' + number_event + '.xlsx'
    
    all_data = []
    for user in db.users.find({ 'event_' + number_event + '.0': {'$exists': True}}):
        voice_obj = {
            'tg_id': user['tg_id'],
            'from': user['faculty'] if 'faculty' in user else 'Сотрудник',
            'voices': [], 
            'mail': user['mail'],
        }
        if 'kio' in user:
            voice_obj['kio'] = True
        if 'squads' in user:
            voice_obj['squads'] = True

        for i in range(3):
            try:
                voice_obj['voices'].append(user['event_' + number_event][i])
            except Exception as e:
                voice_obj['voices'].append('')

        all_data.append(voice_obj)

    # Подсчет по всем факультетам
    voices_from_faculty = {}
    for data in all_data:
        if data['from'] not in voices_from_faculty:
            voices_from_faculty[data['from']] = {}

        if data['from'] == 'Юриспруденция':
            print(data['voices'])
        for voice in data['voices']:
            if data['from'] == 'Юриспруденция' and voice == 'Журналистика':
                print('ok')
            if voice != '':
                if voice in voices_from_faculty[data['from']]:
                    voices_from_faculty[data['from']][voice] += 1
                else:
                    voices_from_faculty[data['from']][voice] = 1
    
    print(voices_from_faculty)
    
    # Нормализация голосов по 10 бальной шкале
    voices_from_faculty_norm = {}
    for faculty in voices_from_faculty.keys():
        voices_from_faculty_norm[faculty] = {}

        sorted_keys = sorted(voices_from_faculty[faculty].keys(), key=lambda k: voices_from_faculty[faculty][k], reverse=True)
        print(sorted_keys)
        scores = [10, 8, 6, 5, 4, 3, 2, 1]
        i = 0
        j = 0
        while j < len(sorted_keys):
            if j != 0 and voices_from_faculty[faculty][sorted_keys[j]] == voices_from_faculty[faculty][sorted_keys[j - 1]]:
                voices_from_faculty_norm[faculty][sorted_keys[j]] = scores[i - 1]
            else:
                if i >= len(scores):
                    break
                voices_from_faculty_norm[faculty][sorted_keys[j]] = scores[i]
                i += 1
            j += 1
        
        # for i in range(min(8, len(voices_from_faculty[faculty]))):
        #     voices_from_faculty_norm[faculty][sorted_keys[i]] = scores[i]
    
    print(voices_from_faculty_norm)

    # Суммируем по всем факультетам
    voices_sum = {}
    for k, v in voices_from_faculty_norm.items():
        for k1, v1 in v.items():
            if k1 in voices_sum:
                voices_sum[k1] += v1
            else:
                voices_sum[k1] = v1
    
    print(voices_sum)
    sorted_sum = sorted_keys = sorted(voices_sum.keys(), key=lambda k: voices_sum[k], reverse=True)
    for k in sorted_sum:
        print(k, voices_sum[k])

    columns = ['chat_id', 'От кого', '1', '2', '3', 'mail']
    export_data = []
    for data in all_data:
        from_column = data['from']
        if 'kio' in data:
            from_column = 'КИО'
        elif 'squads' in data:
            from_column = 'Отряды'

        export_data.append([
            data['tg_id'],
            from_column,
            data['voices'][0],
            data['voices'][1],
            data['voices'][2],
            data['mail']
        ])
    
    export_data.append([])
    for faculty in sorted_sum:
        export_data.append([faculty, voices_sum[faculty]])

    df = pd.DataFrame(export_data, columns=columns)
    df.to_excel(filename, index=False, )

    result_file = FSInputFile(filename)
    await msg.answer_document(result_file)


@commands_router.message(Command('check_user'))
async def check_user_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    mail = command.args

    user = db.users.find_one({'mail': mail})

    if user:
        await msg.answer(str(user))
    else:
        await msg.answer('Такого пользователя нет в базе')


@commands_router.message(Command('del_user_data'))
async def del_user_data_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    mail = command.args

    db.users.delete_one({'mail': mail})

    await msg.answer('Удалён')


@commands_router.message(Command('del_user_vote'))
async def del_user_vote_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return
        
    mail = command.args

    # Получаем все поля пользователя
    user = db.users.find_one({'mail': mail})
    if user:
        # Создаем объект для удаления всех полей, начинающихся с event_
        unset_fields = {}
        for field in user.keys():
            if field.startswith('event_'):
                unset_fields[field] = True
        
        if unset_fields:
            db.users.update_one({'mail': mail}, {'$unset': unset_fields})
            await msg.answer('Все поля голосования удалены')
        else:
            await msg.answer('У пользователя нет полей голосования')
    else:
        await msg.answer('Пользователь не найден')


@commands_router.message(Command('del_all_votes'))
async def del_all_votes_command(msg: Message) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return

    # Получаем всех пользователей
    users = db.users.find({})
    
    # Собираем все уникальные поля, начинающиеся с event_
    event_fields = set()
    for user in users:
        for field in user.keys():
            if field.startswith('event_'):
                event_fields.add(field)
    
    if event_fields:
        # Создаем объект для удаления всех полей
        unset_fields = {field: True for field in event_fields}
        
        # Удаляем поля у всех пользователей
        result = db.users.update_many({}, {'$unset': unset_fields})
        await msg.answer(f'Удалено {result.modified_count} полей голосования у всех пользователей')
    else:
        await msg.answer('Поля голосования не найдены у пользователей')


@commands_router.message(Command('add_user'))
async def add_user_command(msg: Message, command: CommandObject) -> None:
    if msg.from_user.id not in admins:
        await msg.answer(text_not_permissions)
        return
    
    if not command.args:
        await msg.answer('Пожалуйста, укажите данные в формате:\nфакультет\nпочта')
        return

    try:
        faculty, mail = command.args.split('\n')
        
        # Создаем нового пользователя
        new_user = {
            'faculty': faculty.strip(),
            'mail': mail.strip()
        }
        
        # Проверяем, существует ли уже пользователь с такой почтой
        existing_user = db.users.find_one({'mail': mail.strip()})
        if existing_user:
            await msg.answer('Пользователь с такой почтой уже существует')
            return
        
        # Добавляем пользователя в базу данных
        result = db.users.insert_one(new_user)
        
        if result.inserted_id:
            await msg.answer('Пользователь успешно добавлен')
        else:
            await msg.answer('Ошибка при добавлении пользователя')
            
    except ValueError:
        await msg.answer('Неверный формат данных. Используйте формат:\nфакультет\nпочта')