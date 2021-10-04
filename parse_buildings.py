from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from cache import cached

BUILDINGS_URL = "https://ethz.ch/services/en/service/rooms-and-buildings/building-orientation.html?_charset_=UTF-8&geb=&str=&zip=&city="

@dataclass
class Building:
    name: str
    street: str
    zip: str
    city: str

@cached("BUILDING_LIST")
def all_buildings():

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

    return buildings

if __name__ == "__main__":
    bu = all_buildings()
    for ts in bu:
        print(ts)
