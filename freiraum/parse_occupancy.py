import requests
from dataclasses import dataclass, asdict
from typing import Optional, List, Tuple
from enum import Enum
from datetime import timedelta, date, datetime
import re
from bs4 import BeautifulSoup
from itertools import product


def table_to_2d(table_tag, value_f=lambda x: x.get_text()):
    """
    parses an html table into a 2D matrix, filling appropriate fields based on
    the result of passing the td tag to value_f
    > adjusted from https://stackoverflow.com/questions/48393253/how-to-parse-table-with-rowspan-and-colspan
    """
    rowspans = []  # track pending rowspans
    rows = table_tag.find_all("tr")

    # first scan, see how many columns we need
    colcount = 0
    for r, row in enumerate(rows):
        cells = row.find_all(["td", "th"], recursive=False)
        # count columns (including spanned).
        # add active rowspans from preceding rows
        # we *ignore* the colspan value on the last cell, to prevent
        # creating 'phantom' columns with no actual cells, only extended
        # colspans. This is achieved by hardcoding the last cell width as 1.
        # a colspan of 0 means “fill until the end” but can really only apply
        # to the last cell; ignore it elsewhere.
        colcount = max(
            colcount,
            sum(int(c.get("colspan", 1)) or 1 for c in cells[:-1])
            + len(cells[-1:])
            + len(rowspans),
        )
        # update rowspan bookkeeping; 0 is a span to the bottom.
        rowspans += [int(c.get("rowspan", 1)) or len(rows) - r for c in cells]
        rowspans = [s - 1 for s in rowspans if s > 1]
    # it doesn't matter if there are still rowspan numbers 'active'; no extra
    # rows to show in the table means the larger than 1 rowspan numbers in the
    # last table row are ignored.
    # build an empty matrix for all possible cells
    table = [[None] * colcount for _ in rows]

    # fill matrix from row data
    rowspans = {}  # track pending rowspans, column number mapping to count
    for row, row_elem in enumerate(rows):
        span_offset = 0  # how many columns are skipped due to row and colspans
        for col, cell in enumerate(row_elem.find_all(["td", "th"], recursive=False)):
            # adjust for preceding row and colspans
            col += span_offset
            while rowspans.get(col, 0):
                span_offset += 1
                col += 1

            # fill table data
            rowspan = rowspans[col] = int(cell.get("rowspan", 1)) or len(rows) - row
            colspan = int(cell.get("colspan", 1)) or colcount - col
            # next column is offset by the colspan
            span_offset += colspan - 1
            value = value_f(cell)
            for drow, dcol in product(range(rowspan), range(colspan)):
                try:
                    table[row + drow][col + dcol] = value
                    rowspans[col + dcol] = rowspan
                except IndexError:
                    # rowspan or colspan outside the confines of the table
                    pass

        # update rowspan bookkeeping
        rowspans = {c: s - 1 for c, s in rowspans.items() if s > 1}

    return table


MONTH_TO_DAY = {
    1: "Jan",
    2: "Feb",
    3: "Mär",
    4: "Apr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Okt",
    11: "Nov",
    12: "Dez",
}


@dataclass
class Room:
    region: str
    areal: str
    gebaeude: str
    geschoss: str
    raumNr: str
    rektoratInListe: str = "true"
    raumInRaumgruppe: str = "true"


@dataclass
class Class:
    title: str
    organization: Optional[str]


class Occupancy(Enum):
    CLOSED = "#cccccc"
    FREE = "#99cc99"
    OCCUPIED = "#006799"
    UNKNOWN = None
    INVALID = "#eeeeee"


@dataclass
class Timeslot:
    state: Occupancy
    begin: datetime
    end: datetime
    event: Optional[Class] = None


def parse_td(x: BeautifulSoup) -> (Optional[Class], Occupancy):
    # if the background color is invalid, the whole cell is part of the "frame"
    if not x.attrs["bgcolor"].startswith("#"):
        return (None, Occupancy.INVALID)
    # otherwise it encodes the occupancy
    occupancy = Occupancy(x.attrs["bgcolor"])

    # is there a title for this class?
    title_list = x.find_all(attrs={"color": "#ffffff"})
    if not title_list:
        # if not, the room is empty/closed/cell invalid
        return (None, occupancy)
    else:
        # otherwise find title and potentially organisation of class
        title = title_list[0].text.strip()
        organization_list = x.find_all(attrs={"color": "#dddddd"})
        organization = organization_list[0].text.strip() if organization_list else None
        return (Class(title, organization), occupancy)


def transpose(l):
    return list(map(list, zip(*l)))


def parse_date(date_string: str):
    (day, month, year) = tuple(map(int, date_string.split(".")))
    return datetime(day=day, month=month, year=year)


def room_occupancy(room: Room, date: date = date.today()):
    """
    For a room and date fetches and returns the occupancy of a room in the week of the date
    :param room:
    :param date:
    :return:
    """
    post_data = {
        "tag": str(date.day),
        "monat": MONTH_TO_DAY.get(date.month, "Unk"),
        "jahr": str(date.year),
        "checkUsage": "anzeigen",
        **asdict(room),
    }
    # fetch room occupancy
    r = requests.post(
        "http://www.rauminfo.ethz.ch/Rauminfo/Rauminfo.do", data=post_data
    )
    site = r.text
    print(site, file=open("room_occupancy.html", "w"))
    # extract the actual start of the week
    match = next(
        iter(
            re.finditer(
                r"(?P<week_begin>\d\d\.\d\d\.\d\d\d\d)&nbsp;bis&nbsp;(?P<week_end>\d\d\.\d\d\.\d\d\d\d)",
                site,
            )
        )
    )
    week_begin = parse_date(match.group("week_begin"))
    # week_end = parse_date(match.group("week_end"))

    # parse the occupancy table
    soup = BeautifulSoup(site)
    tables = soup.find_all("table")
    occupancy_table = tables[1]
    room_occupancy = table_to_2d(occupancy_table, parse_td)

    # the occupancy table has one row frame and tow cols frame (on the left)
    # the remainder is one slot per course, resolved in quarter-hours
    room_occupancy: List[List[Tuple[Optional[Class], Occupancy]]] = transpose(
        room_occupancy
    )
    timeslots = []
    for colc, col in enumerate(room_occupancy[2:]):
        cur_start_day = week_begin + timedelta(days=colc)
        # there is an unknown filling from the day before 22:00 to 7:00
        cur_event = Timeslot(
            state=Occupancy.UNKNOWN,
            begin=cur_start_day - timedelta(hours=2),
            end=cur_start_day + timedelta(hours=7),
        )
        for rowc, row in enumerate(col[1:]):
            cur_start_time_minutes = (
                cur_start_day + timedelta(hours=7) + rowc * timedelta(minutes=15)
            )
            cur_end_time_minutes = (
                cur_start_day + timedelta(hours=7) + (rowc + 1) * timedelta(minutes=15)
            )
            cur_event.end = cur_start_time_minutes
            if not (cur_event.event == row[0] and cur_event.state == row[1]):
                timeslots.append(cur_event)
                cur_event = Timeslot(
                    state=row[1],
                    event=row[0],
                    begin=cur_start_time_minutes,
                    end=cur_end_time_minutes,
                )
        timeslots.append(cur_event)
    return timeslots


if __name__ == "__main__":
    ro = room_occupancy(
        Room(
            region="Z",
            areal="Z",
            gebaeude="CAB",
            geschoss="G",
            raumNr="11",
        )
    )
    for ts in ro:
        print(ts)
