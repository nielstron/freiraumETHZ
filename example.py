from freiraum.parse_room_list import all_rooms
from freiraum.parse_occupancy import room_occupancy, Occupancy
from datetime import datetime
from logging import getLogger, WARNING

__LOGGER__ = getLogger(__file__)
__LOGGER__.setLevel(WARNING)

# Put buildings that you want to filter for here
FILTER = {
    "CAB",
    "HG"
}

if __name__ == '__main__':
    rooms = all_rooms()
    now = datetime.now()
    for r in rooms:
        # basic filter for rooms in buildings I am interested in
        if r.gebaeude in FILTER:
            occ = room_occupancy(r)
            for o in occ:
                if o.state == Occupancy.FREE and o.begin <= now <= o.end:
                    print(f"{r.name} is free until {o.end}")
                    break
            __LOGGER__.info(f"Checked {r.name}")
