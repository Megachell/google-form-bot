import logging

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import asyncio
import sqlite3

import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import token
from functions import insert_report, insert_name, get_name, get_names, no_report_today, get_statuses

logging.basicConfig(level = logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot)

user_cash = {} # This dict will contain users' status untill submission

async def ask(user_id):  # Ask specified user their staus
	if no_report_today(user_id):
		statuses = get_statuses()
		statuses_inline_kb = InlineKeyboardMarkup()
		for i in statuses:
			cb = 'status_'+i
			statuses_inline_kb.add(InlineKeyboardButton(i, callback_data = cb))
		statuses_inline_kb.add(InlineKeyboardButton('I will do it later', callback_data = 'status_cancel'))
		await bot.send_message(user_id, 'Today status?', reply_markup = statuses_inline_kb)

async def ask_all(): # Ask all users their status
	if datetime.now().weekday() not in [5,6]:
		conn = sqlite3.connect('IDS.db')
		cur = conn.cursor()
		q = "select ID from IDS"
		for i in cur.execute(q):
			await ask(i[0])
		conn.close()

# ----- Message handlers below ---------------

@dp.message_handler(commands=['start'])   # Start message hendler
async def welcome(message: types.Message):
	hello_message = "Pick your name:"
	names = get_names()                   
	names_inline_kb = InlineKeyboardMarkup() # Create keyboard with all possible names
	for i in names:
		cb = 'name_'+i
		names_inline_kb.add(InlineKeyboardButton(i, callback_data=cb))
	await message.answer(hello_message, reply_markup = names_inline_kb)

@dp.callback_query_handler(lambda c: c.data.startswith('status_'))   # status report handler
async def process_callback_status(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)
	if no_report_today(callback_query.from_user.id):
		status = callback_query.data.split('_')[1]
		if status != 'cancel':                                       # If user doesen't cancel report - ask if they want to add a comment
		    comment_inline_kb = InlineKeyboardMarkup()
		    comment_inline_kb.add(InlineKeyboardButton('Yes', callback_data = 'comment_yes'))
		    comment_inline_kb.add(InlineKeyboardButton('No', callback_data = 'comment_no'))
		    user_cash[callback_query.from_user.id] = status          # Put current status into user_cash dict, so status is accessable from another functions
		    await bot.send_message(callback_query.from_user.id, 'Add comment?', reply_markup = comment_inline_kb)
		else:
			await bot.send_message(callback_query.from_user.id, 'Ok')
	else:
		await bot.send_message(callback_query.from_user.id, 'Todays report already exists')

@dp.callback_query_handler(lambda c: c.data.startswith('comment_'))   # Comment handler
async def process_callback_comment(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    answer = callback_query.data.split('_')[1]
    if answer == 'no':
    	status = user_cash.pop(callback_query.from_user.id)
    	result = insert_report(get_name(callback_query.from_user.id), status) # Submit report if the answer is no
    	await bot.send_message(callback_query.from_user.id, result)
    else:
    	await bot.send_message(callback_query.from_user.id, 'Enter comment:') # Ask for comment if the answer is yes


@dp.callback_query_handler(lambda c: c.data.startswith('name_'))  # Name handler
async def process_callback_name(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    name = callback_query.data.split('_')[1]
    insert_name(callback_query.from_user.id, name)    # Submit the user to the database
    await bot.send_message(callback_query.from_user.id, 'Your name is {}. To change your choise press /start once again'.format(name))
    await ask(callback_query.from_user.id)

@dp.message_handler()  # Handles messages withot commands. This can only be a comment, so we just need to check if comment is awaited and submit the report.
async def echo(message: types.Message):
		if message['from']['id'] in user_cash.keys():
			status = user_cash.pop(message['from']['id'])
			comment = message.text
			result = insert_report(get_name(message['from']['id']), status, comment) # Submit report with comment
			await bot.send_message(message['from']['id'], result)
		else:
			await bot.send_message(message['from']['id'], 'You can only add comment befor submitting report')

# ----- Initialization part ------------

async def scheduler():   # Shedule ask_all() everyday at 15:00 GMT
    aioschedule.every().day.at("15:00").do(ask_all)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):  # Launch scheduler on startup
    asyncio.create_task(scheduler())

if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True,  on_startup=on_startup)