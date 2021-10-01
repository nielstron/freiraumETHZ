from typing import List
from parse_buildings import Building, buildings
from dataclasses import dataclass, asdict
import pyphoton

@dataclass
class LocatedBuilding(Building):
    lat: float
    lon: float

def locate_buildings(buildings: List[Building]):
    phclient = pyphoton.Photon(host="https://photon.komoot.io")
    located_buildings = []
    for b in buildings:
        location = phclient.query(
            f"{b.street}, {b.city}",
            limit=1
        )
        located_buildings.append(
            LocatedBuilding(lat=location.latitude, lon=location.longitude, **asdict(b))
        )

if __name__ == '__main__':
    buildings = buildings()
    located_buildings = locate_buildings(buildings)
    for lb in located_buildings:
        print(lb)

