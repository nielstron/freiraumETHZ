from freiraum.parse_room_list import all_rooms
from freiraum.parse_occupancy import room_occupancy, Occupancy
from datetime import datetime

if __name__ == '__main__':
    rooms = all_rooms()
    now = datetime.now()
    for r in rooms:
        occ = room_occupancy(r)
        for o in occ:
            if o.state == Occupancy.FREE and o.begin <= now <= o.end:
                print(f"{r.name} is free until {o.end}")
                break
        print(f"Checked {r.name}")
