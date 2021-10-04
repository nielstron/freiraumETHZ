from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import pickle
from typing import List

BUILDINGS_URL = "https://ethz.ch/services/en/service/rooms-and-buildings/building-orientation.html?_charset_=UTF-8&geb=&str=&zip=&city="

@dataclass
class Building:
    name: str
    street: str
    zip: str
    city: str

def all_buildings(cache=Path(".cache")):
    if cache:
        try:
            with cache.joinpath("BUILDING_LIST").open("rb") as building_cache_file:
                bcf: List[Building] = pickle.load(building_cache_file)
                return bcf
        except (FileNotFoundError, EOFError):
            pass

    r1 = requests.get(BUILDINGS_URL, headers={"User-Agent": "Spoof"})

    site = r1.text
    soup = BeautifulSoup(site, features="lxml")
    table = soup.find(name="table", attrs={"class":"result donthyphenate"})
    buildings = []
    for row in table.find_all("tr")[1:]:
        building = Building(
            *(map(lambda x: x.text.strip(), row.find_all("td")[:4]))
        )
        buildings.append(building)
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        with cache.joinpath("BUILDING_LIST").open("wb") as building_cache_file:
            rlf = buildings
            pickle.dump(rlf, building_cache_file)
    return buildings

if __name__ == "__main__":
    bu = all_buildings()
    for ts in bu:
        print(ts)
