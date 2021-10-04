from secrets import TELEGRAM_BOT_TOKEN
from telegram.ext import Updater, Dispatcher, CommandHandler, MessageHandler, Filters
import logging
import re
from datetime import datetime

from parse_buildings import all_buildings
from parse_room_list import all_rooms
from parse_occupancy import room_occupancy, Occupancy

__LOGGER__ = logging.getLogger(__name__)
__LOGGER__.setLevel(logging.INFO)

def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi, frag mich nach freien Räumen in deiner Umgebung. Wo soll ich suchen?"
    )

def handle_rooms(update, context):
    message = update.message.text
    __LOGGER__.info(f"Received message: {message}")
    buildings = set(map(lambda x: x.name, all_buildings()))
    requested_buildings = {x for x in buildings if re.search(rf"\b{x}\b", message) is not None}
    __LOGGER__.info(f"Extracted buildings: {buildings}")
    if requested_buildings:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Okay, suche nach freien Räumen in den Gebäuden {', '.join(requested_buildings)}"
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Okay, suche nach freien Räumen."
        )
    rooms = all_rooms()
    now = datetime.now()
    count = 0
    for r in rooms:
        # basic filter for rooms in buildings I am interested in
        if not requested_buildings or r.gebaeude in requested_buildings:
            occ = room_occupancy(r)
            for o in occ:
                if o.state == Occupancy.FREE and o.begin <= now <= o.end:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"{r.name} ist frei bis {o.end}"
                    )
                    count += 1
                    break
            __LOGGER__.info(f"Checked {r.name}")
    if count == 0:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Entschuldige, ich konnte leider keine freien Räume finden."
        )




if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    updater = Updater(token=TELEGRAM_BOT_TOKEN)
    dispatcher: Dispatcher = updater.dispatcher

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    room_handler = MessageHandler(Filters.text & (~Filters.command), handle_rooms)
    dispatcher.add_handler(room_handler)

    updater.start_polling()