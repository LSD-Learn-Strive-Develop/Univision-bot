import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, User, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from fluentogram import TranslatorHub

from bot.config_data.config import db, admins

logger = logging.getLogger(__name__)


class ActiveEventCallbackMiddleware(BaseMiddleware):
    def is_active(self) -> bool:
        info = db.info.find_one()

        return info['active_event'] != 0

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user: User = data.get('event_from_user')

        if user is None:
            return await handler(event, data)

        if self.is_active() or user.id in admins:
            logging.info('Middlwere inactive')
            return await handler(event, data)
        
        hub: TranslatorHub = data.get('_translator_hub')
        i18n = hub.get_translator_by_locale(locale=user.language_code)

        if isinstance(event, CallbackQuery):
            logging.info('Middlwere callback')
            await event.answer(i18n.message.voting_not_running(), show_alert=True)
            await event.message.delete()
        elif isinstance(event, Message):
            logging.info('Middlwere message')
            kb = [[KeyboardButton(text=i18n.button.vote())]]
            keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            await event.message.answer(i18n.message.voting_not_running(), reply_markup=keyboard)
        return