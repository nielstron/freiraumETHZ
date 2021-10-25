from secrets import TELEGRAM_BOT_TOKEN
from telegram.ext import Updater, Dispatcher, CommandHandler, MessageHandler, Filters
import logging
import re
from datetime import datetime, date
from geopy.distance import geodesic
from typing import List
import math

from parse_buildings import all_buildings, Building
from locate_buildings import all_located_buildings, LocatedBuilding
from parse_room_list import all_rooms, Room
from parse_occupancy import room_occupancy, Occupancy
from parse_room_info import room_info


__LOGGER__ = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

occ_str = {
    Occupancy.FREE: "offen",
    Occupancy.CLOSED: "geschlossen",
    Occupancy.UNKNOWN: "vermutlich geschlossen",
}

def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi, frag mich nach freien Räumen in deiner Umgebung. Wo soll ich suchen? Sende mir eine Nachricht mit deinem Gebäude oder deinem Standort."
    )

def handle_room_message(update, context):
    try:
        message = update.message.text
        __LOGGER__.info(f"Received message: {message}")
        buildings = all_buildings()
        requested_buildings = {x.name for x in buildings if re.search(rf"\b{x.name.lower()}\b", message.lower()) is not None}
        __LOGGER__.info(f"Extracted buildings: {requested_buildings}")
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
                occ = room_occupancy(r,date=date.today())
                for o in occ:
                    if o.state in {Occupancy.FREE, Occupancy.UNKNOWN, Occupancy.CLOSED} and o.begin <= now <= o.end:
                        r_info = room_info(r)
                        context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"{r.name} ist frei und {occ_str[o.state]} bis {o.end:%H:%M} Uhr ({r_info['Raumtyp']} mit {r_info['Sitzplätze']} Sitzplätzen)"
                        )
                        count += 1
                        break
                __LOGGER__.info(f"Checked {r.name}")
        if count == 0:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Entschuldige, ich konnte leider keine freien Räume finden."
            )
    except Exception as e:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ein unerwarteter Fehler ist aufgetreten: {e}"
        )
        __LOGGER__.error("Unexpected error occured.", exc_info=e)



def handle_location(update, context):
    try:
        if update.message.location:
            location = update.message.location
            __LOGGER__.info(f"Received location: {location}")
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Okay, suche nach den 20 nächsten freien Räumen."
            )
            context.user_data["skip_first"] = 0
            context.user_data["location"] = location
            skip_first = 0
        else:
            # otherwise must have been a "more" request
            __LOGGER__.info(f"Received request for more buildings")
            location = context.user_data["location"]
            skip_first = context.user_data["skip_first"]
        buildings: List[LocatedBuilding] = all_located_buildings()
        building_dist = {b.name: geodesic(
            (b.lat, b.lon), (location["latitude"], location["longitude"])
        ).meters for b in buildings}
        rooms: List[Room] = all_rooms()
        # order rooms by distance to sent location
        rooms = sorted(rooms, key=lambda x: building_dist.get(x.gebaeude, math.inf))
        now = datetime.now()
        count = 0
        for r in rooms:
            # basic filter for rooms in buildings I am interested in
            occ = room_occupancy(r, date=date.today())
            for o in occ:
                if o.state in {Occupancy.FREE, Occupancy.UNKNOWN, Occupancy.CLOSED} and o.begin <= now <= o.end:
                    if skip_first > 0:
                        __LOGGER__.info(f"Skipped {r.name}")
                        skip_first -= 1
                    else:
                        r_info = room_info(r)
                        context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"{r.name} ist frei und {occ_str[o.state]} bis {o.end:%H:%M} Uhr und {int(building_dist[r.gebaeude])}m entfernt ({r_info['Raumtyp']} mit {r_info['Sitzplätze']} Sitzplätzen) "
                        )
                        count += 1
                    break
            __LOGGER__.info(f"Checked {r.name}")
            if count >= 20:
                break
        if count == 0:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Entschuldige, ich konnte leider keine freien Räume finden."
            )
        context.user_data["skip_first"] += count
    except Exception as e:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ein unerwarteter Fehler ist aufgetreten: {e}"
        )
        __LOGGER__.error("Unexpected error occured.", exc_info=e)


def building_location(update, context):
    try:
        message = update.message.text
        __LOGGER__.info(f"Received location request: {message}")
        buildings: List[Building] = all_buildings()
        found = False
        for b in buildings:
            if b.name.lower() in message.lower().split():
                __LOGGER__.info(f"found {b}")
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{b.name}\n{b.street},\n{b.zip} {b.city}",
                )
                found = True
                break
        if not found:
            __LOGGER__.info(f"Building not found")
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Entschuldige, ich konnte das Gebäude nicht finden",
            )
        else:
            located_buildings: List[LocatedBuilding] = all_located_buildings()
            for lb in located_buildings:
                if lb.name.lower() in message.split():
                    __LOGGER__.info(f"found {lb}")
                    context.bot.send_location(
                        chat_id=update.effective_chat.id,
                        latitude=lb.lat,
                        longitude=lb.lon,
                    )
                    return
    except Exception as e:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ein unerwarteter Fehler ist aufgetreten: {e}"
        )
        __LOGGER__.error("Unexpected error occured.", exc_info=e)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    updater = Updater(token=TELEGRAM_BOT_TOKEN)
    dispatcher: Dispatcher = updater.dispatcher

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    building_location_handler = CommandHandler("locate", building_location)
    dispatcher.add_handler(building_location_handler)

    more_location_handler = CommandHandler("more", handle_location)
    dispatcher.add_handler(more_location_handler)

    room_handler = MessageHandler(Filters.text & (~Filters.command), handle_room_message)
    dispatcher.add_handler(room_handler)

    location_handler = MessageHandler(Filters.location, handle_location)
    dispatcher.add_handler(location_handler)

    updater.start_polling()
