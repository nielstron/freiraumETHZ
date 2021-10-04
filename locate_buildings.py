from typing import List
from parse_buildings import Building, all_buildings
from dataclasses import dataclass, asdict
import pyphoton
from cache import cached
import logging

__LOGGER__ = logging.getLogger(__name__)


@dataclass
class LocatedBuilding(Building):
    lat: float
    lon: float

def locate_buildings(buildings: List[Building]):
    phclient = pyphoton.Photon(host="https://photon.komoot.io")
    located_buildings = []
    for b in buildings:
        __LOGGER__.info(f"Locating {b.name}")
        location = phclient.query(
            f"{b.street}, {b.city}",
            limit=1
        )
        if location:
            located_buildings.append(
                LocatedBuilding(lat=location.latitude, lon=location.longitude, **asdict(b))
            )
        else:
            __LOGGER__.warning(f"Did not find location of {b.name}")
    return located_buildings

@cached("LOCATED_BUILDING_LIST")
def all_located_buildings():
    return locate_buildings(all_buildings())

if __name__ == '__main__':
    located_buildings = all_located_buildings()
    for lb in located_buildings:
        print(lb)

