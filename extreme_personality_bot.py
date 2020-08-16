# ---------------------------------------------------------------------------------------------------------------------------------------- #
#                                                                  Import                                                                  #
# ---------------------------------------------------------------------------------------------------------------------------------------- #

# https://github.com/python-telegram-bot/python-telegram-bot/wiki

import logging, json
from datetime import datetime
from uuid import uuid4
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultCachedPhoto, InlineQueryResultArticle, InputTextMessageContent, ChatAction, ParseMode
from telegram.ext import Updater, PicklePersistence, CommandHandler, CallbackQueryHandler, InlineQueryHandler
from telegram.ext.dispatcher import run_async

# ---------------------------------------------------------------------------------------------------------------------------------------- #
#                                                               Konfiguration                                                              #
# ---------------------------------------------------------------------------------------------------------------------------------------- #

with open("text_lines.json", encoding = "utf-8-sig") as f:
	try:
		text_lines = json.load(f)
	except json.decoder.JSONDecodeError:
		#logging.error("Config-Datei konnte nicht dekodiert werden.", exc_info = True)
		raise

# ---------------------------------------------------------------------------------------------------------------------------------------- #
#                                                            Ergebnisberechnung                                                            #
# ---------------------------------------------------------------------------------------------------------------------------------------- #

'''
	Exemplary Data Structure:
	{
		2324: {
			"delete": 60,
			"results": [
				{
					"dt": <dt_obj>,
					"portions": [0.6, 0.382, ...]
				},
				...
			]
		},
		...
	}
'''
#TODO: muss persistent gemacht werden
results = {}

#dict Lesen und Schreiben sowie list.append und list.extend sind multithreading-safe
@run_async #Ist der Decorator hier überhaupt relevant?
def calculate_results():
	userid = 2374

	if userid not in results:
		results[userid] = {"delete": 60, "results": []}
	
	results[userid]["results"].append({"dt": datetime.now(), "portions": []})

# ---------------------------------------------------------------------------------------------------------------------------------------- #
#                                                           Telegram-Bot Befehle                                                           #
# ---------------------------------------------------------------------------------------------------------------------------------------- #

@run_async
def start(update, context):
	keyboard = [[InlineKeyboardButton(text_lines["start"]["continue"], callback_data = "0-0")]]
	context.bot.send_message(update.effective_chat.id, text_lines["start"]["title"], reply_markup = InlineKeyboardMarkup(keyboard))
	#context.bot.send_message(update.effective_chat.id, "_Gebt \"/\" ein und man zeigt euch, welche Befehle ich verstehe\._", ParseMode.MARKDOWN_V2)

def show_results(update, context):
	'''
	from io import BytesIO
	from PIL import Image, ImageDraw, ImageFont

	context.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_PHOTO, 10)
	bio = BytesIO()
	bio.name = "test.jpg"
	image = Image.new("YCbCr", (800, 1000), (0xFF, 0, 0)) #https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes #(0xFF,) * 3
	#TODO: Generate Picture
	#image.save("result.jpg")
	image.save(bio)
	bio.seek(0)
	context.bot.send_photo(update.effective_chat.id, bio)
	'''

@run_async
def show_saved_data(update, context):
	context.bot.send_message(update.effective_chat.id, json.dumps(results[update.effective_chat.id], ensure_ascii = False, indent = 4))

def delete_saved_data(update, context):
	pass

@run_async
def keyboardquery(update, context):
	context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING, 5)
	query = update.callback_query
	query.answer()

	question, answer = map(lambda n: int(n, 16), query.data.split("-"))
	keyboard = []
	print("Frage beantwortet:", query.data)

	if question + 1 < len(text_lines["questions"]):
		message = text_lines["questions"][question]["title"]
		i = 0
		for row in text_lines["questions"][question]["options"]:
			row_keyboard = []
			for cell in row:
				row_keyboard.append(InlineKeyboardButton(cell, callback_data = "{:X}-{:X}".format(question + 1, i)))
				i += 1
			keyboard.append(row_keyboard)
		#keyboard = [map(lambda y: InlineKeyboardButton(y, callback_data = "{:X}-{:X}".format(question, i))) for x in text_lines["questions"][question]["options"]]
	else:
		print("My time has come.")
		message = text_lines["end"]["title"]
		keyboard = [[InlineKeyboardButton("share", switch_inline_query = "share")]]
		#query.edit_message_text(message, reply_markup = InlineKeyboardMarkup(keyboard))
	
	#Answer
	query.edit_message_text(message, reply_markup = InlineKeyboardMarkup(keyboard))

@run_async
def inlinequery(update, context):
	print("Received Inline Query from <{}> in Chat <{}> with query <{}>".format(update.inline_query.from_user.username, 1, update.inline_query.query))
	if update.inline_query.query == "share" and True: #TODO: username in [...]
		#update.inline_query.answer([InlineQueryResultCachedPhoto(update.inline_query.id, uuid4(), "@" + update.inline_query.from_user.username + "'s Ergebnisse")], 30, True, None, "Test machen ➤", "cool")
		id = uuid4().hex
		print(id)
		result = [InlineQueryResultArticle(id, "@" + update.inline_query.from_user.username + "'s Ergebnisse", InputTextMessageContent("Beschreibung"))]
		update.inline_query.answer(result, 600, True) #https://python-telegram-bot.readthedocs.io/en/stable/telegram.bot.html#telegram.Bot.answer_inline_query
	else:
		update.inline_query.answer([], 30, True, None, "Test machen ➤", "a") #parameter: only [A-Za-z0-9_-] and len in 1-64

@run_async
def settings(update, context):
	keyboard = [[]]
	context.bot.send_message(update.effective_chat.id, text_lines["settings"]["title"], reply_markup = InlineKeyboardMarkup(keyboard))

@run_async
def help(update, context):
	context.bot.send_message(update.effective_chat.id, text_lines["help"])
	#https://stackoverflow.com/questions/15114616/remove-or-edit-entry-saved-with-python-pickle

# ---------------------------------------------------------------------------------------------------------------------------------------- #
#                                                         Starten des Telegram-Bots                                                        #
# ---------------------------------------------------------------------------------------------------------------------------------------- #

with open("config.json") as f:
	json_raw = json.load(f)
	token = json_raw["token"]
	whitelist = json_raw["whitelist"]

if token:
	updater = Updater(token, persistence = PicklePersistence("persistence.p"), use_context = True)
else:
	print("Du solltest in die Datei \"config.json\" deinen Telegram-Bot-Token legen.")
	exit()

updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CallbackQueryHandler(keyboardquery))
updater.dispatcher.add_handler(InlineQueryHandler(inlinequery))
updater.dispatcher.add_handler(CommandHandler("settings", settings))
updater.dispatcher.add_handler(CommandHandler("help", help))

updater.dispatcher.add_handler(CommandHandler("reload_text_lines", settings))

print("Ready!")

updater.start_polling()
updater.idle()