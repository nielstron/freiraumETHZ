from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from parse_occupancy import Room
from pathlib import Path
import pickle
from typing import List

ROOM_LIST_URL = "http://www.rauminfo.ethz.ch/Rauminfo/Index.do?hidden=&gebaeude=-&showAll=alle+R%C3%A4ume+anzeigen&geschoss=-&leitzahl=-"

def all_rooms(cache=Path(".cache")):
    if cache:
        try:
            with cache.joinpath("ROOM_LIST").open("rb") as room_cache_file:
                rlf: List[Room] = pickle.load(room_cache_file)
                return rlf
        except (FileNotFoundError, EOFError):
            pass
    r1 = requests.get(ROOM_LIST_URL)

    site = r1.text
    #site = open("room_list.html").read()
    soup = BeautifulSoup(site, features="lxml")
    table = soup.find_all("table")[5]
    rooms = []
    for row in table.find_all("tr", recursive=False)[1:]:
        rooma = row.find("td").find("a")
        room_name = rooma.text
        room_url = rooma.attrs["href"]
        parsed_url = urlparse(room_url)
        room_params = {key: value[0] for key, value in parse_qs(parsed_url.query).items()}
        rooms.append(Room(name=room_name, **room_params))
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        with cache.joinpath("ROOM_LIST").open("wb") as room_cache_file:
            rlf = rooms
            pickle.dump(rlf, room_cache_file)
    return rooms

if __name__ == '__main__':
    print(all_rooms())