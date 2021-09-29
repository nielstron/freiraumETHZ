from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from parse_occupancy import Room

ROOM_LIST_URL = "http://www.rauminfo.ethz.ch/Rauminfo/Index.do?hidden=&gebaeude=-&showAll=alle+R%C3%A4ume+anzeigen&geschoss=-&leitzahl=-"

def all_rooms():
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
    return rooms

if __name__ == '__main__':
    print(all_rooms())