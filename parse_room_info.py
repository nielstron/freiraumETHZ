import requests
from bs4 import BeautifulSoup
from parse_occupancy import Room
from dataclasses import dataclass, asdict
from typing import Dict
import pickle
from pathlib import Path

ROOM_URL = "http://www.rauminfo.ethz.ch/RauminfoPre.do?region={}&areal={}&gebaeude={}&geschoss={}&raumNr={}"


def room_info(room: Room, cache=Path(".cache")) -> Dict[str, str]:
    if cache:
        try:
            with cache.joinpath(
                "".join(map(str, asdict(room).values())) + "_info"
            ).open("rb") as room_cache_file:
                rcf: Dict[str, str] = pickle.load(room_cache_file)
                return rcf
        except (FileNotFoundError, EOFError):
            pass
    r1 = requests.get(
        ROOM_URL.format(
            room.region, room.areal, room.gebaeude, room.geschoss, room.raumNr
        )
    )

    site = r1.text
    soup = BeautifulSoup(site, features="lxml")
    table = soup.find_all("table")[-1]
    specs = {}
    for row in table.find_all("tr", recursive=False)[1:]:
        spec_name = row.find_all("td")[0].find("b").text.strip()
        spec_val = row.find_all("td")[2].text.strip()
        specs[spec_name] = spec_val
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        with cache.joinpath("".join(map(str, asdict(room).values())) + "_info").open(
            "wb"
        ) as room_cache_file:
            pickle.dump(specs, room_cache_file)
    return specs


if __name__ == "__main__":
    print(room_info(Room("Z", "Z", "CAB", "G", "11")))
