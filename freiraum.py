from parse_room_list import all_rooms
from parse_occupancy import room_occupancy, Occupancy
from datetime import datetime
from logging import getLogger, WARNING
from typing import Iterable
import argparse

__LOGGER__ = getLogger(__file__)
__LOGGER__.setLevel(WARNING)

def main(buildings: Iterable[str]):
    rooms = all_rooms()
    now = datetime.now()
    for r in rooms:
        # basic filter for rooms in buildings I am interested in
        if not buildings or r.gebaeude in buildings:
            occ = room_occupancy(r)
            for o in occ:
                if o.state == Occupancy.FREE and o.begin <= now <= o.end:
                    print(f"{r.name} is free until {o.end}")
                    break
            __LOGGER__.info(f"Checked {r.name}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Finds free rooms in ETHZ buildings.')
    parser.add_argument('buildings', metavar='buildings', type=str, nargs='*',
                        help='Buildings to scan for, omit to scan all.')
    args = parser.parse_args()
    main(set(args.buildings))
