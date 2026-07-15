# ==================== IMPORTS ====================
import asyncio
import logging
import sys
import re
from datetime import datetime
pythonfrom dotenv import load_dotenv
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import init_db, set_budget, get_budget, add_expense, get_total_spent


# ==================== SETTINGS ====================
load_dotenv()
TOKEN = getenv("TOKEN")
dp = Dispatcher(storage=MemoryStorage())


# ==================== STATES FOR /setup ====================
class BudgetSetup(StatesGroup):
    waiting_salary = State()
    waiting_save_amount = State()
    waiting_salary_date = State()
    waiting_currency = State()


# ==================== /start COMMAND ====================
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hi, {html.bold(message.from_user.full_name)}! Type /setup to configure your budget.")

@dp.message(BudgetSetup.waiting_currency)
async def setup_currency(message: Message, state: FSMContext):
    data = await state.get_data()
    set_budget(
        user_id=message.from_user.id,
        salary=data["salary"],
        save_amount=data["save_amount"],
        salary_date=data["salary_date"],
        currency=message.text
    )
    await message.answer("Budget set! Now just send me your expenses.")
    await state.clear()

# ==================== /setup COMMAND (budget setup) ====================
@dp.message(Command("setup"))
async def setup_start(message: Message, state: FSMContext):
    await message.answer("What's your salary?")
    await state.set_state(BudgetSetup.waiting_salary)

@dp.message(BudgetSetup.waiting_salary_date)
async def ask_currency(message: Message, state: FSMContext):
    await state.update_data(salary_date=message.text)
    await message.answer("In what currency do we calculate? (e.g. ₴, €, $)")
    await state.set_state(BudgetSetup.waiting_currency)


@dp.message(BudgetSetup.waiting_salary)
async def setup_salary(message: Message, state: FSMContext):
    await state.update_data(salary=float(message.text))
    await message.answer("How much do you want to save per month?")
    await state.set_state(BudgetSetup.waiting_save_amount)


@dp.message(BudgetSetup.waiting_save_amount)
async def setup_save_amount(message: Message, state: FSMContext):
    await state.update_data(save_amount=float(message.text))
    await message.answer("What date do you get paid? (e.g. 2026-08-01)")
    await state.set_state(BudgetSetup.waiting_salary_date)

# ==================== /status COMMAND ====================
@dp.message(Command("status"))
async def status_handler(message: Message):
    budget = get_budget(message.from_user.id)
    if not budget:
        await message.answer("Please set up your budget first via /setup")
        return

    salary, save_amount, salary_date, currency = budget
    spent = get_total_spent(message.from_user.id)
    available = salary - save_amount
    left = available - spent

    await message.answer(
        f"Income: {salary}{currency}\n"
        f"Saving: {save_amount}{currency}\n"
        f"Available to spend: {available}{currency}\n"
        f"Spent: {spent}{currency}\n"
        f"Left: {left}{currency}"
    )


# ==================== EXPENSE INPUT (any other message) ====================
@dp.message()
async def expense_handler(message: Message):
    match = re.match(r"(\d+)\s+(.+)", message.text)
    if match:
        amount = float(match.group(1))
        category = match.group(2)

        budget = get_budget(message.from_user.id)
        currency = budget[3] if budget else ""

        add_expense(
            user_id=message.from_user.id,
            amount=amount,
            category=category,
            date=str(datetime.now().date())
        )
        await message.answer(f"Logged: {amount}{currency} for {category}")
    else:
        await message.answer(f"Didn't get that. Send an amount and what you spent on, e.g.: 50 coffee")


# ==================== BOT STARTUP ====================
async def main() -> None:
    init_db()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
