from typing import List
from parse_buildings import Building, all_buildings
from dataclasses import dataclass, asdict
import pyphoton
from cache import cached


@dataclass
class LocatedBuilding(Building):
    lat: float
    lon: float

@cached("LOCATED_BUILDING_LIST")
def locate_buildings(buildings: List[Building], cache=Path(".cache")):
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
    return located_buildings

if __name__ == '__main__':
    buildings = all_buildings()
    located_buildings = locate_buildings(buildings)
    for lb in located_buildings:
        print(lb)

