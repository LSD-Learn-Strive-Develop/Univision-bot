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
    faculties = db.faculties.find({})
    text = 'Факультуты:\n'
    for faculty in faculties:
        text += faculty['faculty'] + '\n'

    await msg.answer(text)
    

@commands_router.message(Command('add'))
async def add_faculty_command(msg: Message, command: CommandObject) -> None:
    rows = command.args.split('\n')
    for i in range(len(rows)):
        db.faculties.insert_one({'faculty': rows[i], 'item': i})

    await msg.answer('Факультет добавлен')


@commands_router.message(Command('add_squads'))
async def add_faculty_command(msg: Message, command: CommandObject) -> None:
    rows = command.args.split('\n')
    for i in range(len(rows)):
        db.users.update_one({'mail': rows[i].lower()}, {'$set': {'squads': True}})

    await msg.answer('Отряды добавлены')


@commands_router.message(Command('del'))
async def del_faculty_command(msg: Message, command: CommandObject) -> None:
    db.faculties.delete_one({'faculty': command.args})
    await msg.answer('Факультет удален')


@commands_router.message(Command('del_all'))
async def del_faculty_command(msg: Message, command: CommandObject) -> None:
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
            'kio': 'kio' if 'kio' in user else '', 
            'squads': 'squads' if 'squads' in user else ''
        }

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

        for voice in data['voices']:
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
        
        for i in range(min(8, len(voices_from_faculty[faculty]))):
            voices_from_faculty_norm[faculty][sorted_keys[i]] = scores[i]
    
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

    columns = ['chat_id', 'От кого', '1', '2', '3', 'mail', 'kio', 'squads']
    export_data = []
    for data in all_data:
        export_data.append([
            data['tg_id'],
            data['from'],
            data['voices'][0],
            data['voices'][1],
            data['voices'][2],
            data['mail'],
            data['kio'],
            data['squads'],
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
    mail = command.args

    user = db.users.find_one({'mail': mail})

    if user:
        await msg.answer(str(user))
    else:
        await msg.answer('Такого пользователя нет в базе')


@commands_router.message(Command('del_user'))
async def del_user_command(msg: Message, command: CommandObject) -> None:
    mail = command.args

    db.users.delete_one({'mail': mail})
    # db.users.insert_one({'chat_id': msg.from_user.id, 'st_main': mail})

    await msg.answer('Удалён')


@commands_router.message(Command('del_user_all'))
async def del_user_all_command(msg: Message, command: CommandObject) -> None:
    mail = command.args

    db.users.delete_one({'mail': mail})

    await msg.answer('Удалён')