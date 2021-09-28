import requests
from bs4 import BeautifulSoup as bs
import re
from enum import Enum

# URL for fetching list of available rooms
"""
room_list = "http://www.rauminfo.ethz.ch/Rauminfo/Index.do?hidden=&gebaeude=-&showAll=alle+R%C3%A4ume+anzeigen&geschoss=-&leitzahl=-"
r1 = requests.get(room_list)
print(r1.text, file=open("room_list.html", "w"))
"""
from urllib.parse import urlparse, parse_qs

site = open("room_list.html").read()
soup = bs(site)
table = soup.find_all("table")[5]
rooms = []
for rowc, row in enumerate(table.find_all("tr", recursive=False), start=-1):
    if rowc < 0:
        continue
    roomtd = row.find("td")
    rooma = roomtd.find("a")
    room_name = rooma.text
    room_url = rooma.attrs["href"]
    parsed_url = urlparse(room_url)
    room_params = {key : value[0] for key, value in parse_qs(parsed_url.query).items()}
    rooms.append(
        (room_name, room_params)
    )
print(rooms)


# fetch very room specific information
#r = sess.get("http://www.rauminfo.ethz.ch/RauminfoPre.do?region=Z&areal=Z&gebaeude=CAB&geschoss=G&raumNr=11")

# fetch room occupancy
r2 = requests.post(
    "http://www.rauminfo.ethz.ch/Rauminfo/Rauminfo.do",
    data={
        "region": "Z",
        "areal": "Z",
        "gebaeude": "CAB",
        "geschoss": "G",
        "raumNr": "11",
        "rektoratInListe": "true",
        "raumInRaumgruppe": "true",
        #"checkUsage": "checkUsage",
        "tag": "10",
        "monat": "Sep",
        "jahr": "2021",
        "checkUsage": "anzeigen",
    }
)
print(r2.text, file=open("room_occupancy.html", "w"))
soup = bs(r2.text)
site = open("room_occupancy.html").read()
soup = bs(site)

for match in re.finditer(r"(?P<week_begin>\d\d\.\d\d\.\d\d\d\d)&nbsp;bis&nbsp;(?P<week_end>\d\d\.\d\d\.\d\d\d\d)", site):
    week_begin = match.group("week_begin")
    week_end = match.group("week_end")

tables = soup.find_all("table")
occupancy_table = tables[1]

class occupancy(Enum):
    CLOSED = 0
    FREE = 1
    OCCUPIED = 2

color_codes = {
    "#cccccc": occupancy.CLOSED,
    "#006799": occupancy.OCCUPIED,
    "#99cc99": occupancy.FREE,
}

# adjusted from https://stackoverflow.com/questions/48393253/how-to-parse-table-with-rowspan-and-colspan
from itertools import product

def table_to_2d(table_tag, value_f=lambda x: x.get_text()):
    """
    parses an html table into a 2D matrix, filling appropriate fields based on
    the result of passing the td tag to value_f
    """
    rowspans = []  # track pending rowspans
    rows = table_tag.find_all('tr')

    # first scan, see how many columns we need
    colcount = 0
    for r, row in enumerate(rows):
        cells = row.find_all(['td', 'th'], recursive=False)
        # count columns (including spanned).
        # add active rowspans from preceding rows
        # we *ignore* the colspan value on the last cell, to prevent
        # creating 'phantom' columns with no actual cells, only extended
        # colspans. This is achieved by hardcoding the last cell width as 1. 
        # a colspan of 0 means “fill until the end” but can really only apply
        # to the last cell; ignore it elsewhere. 
        colcount = max(
            colcount,
            sum(int(c.get('colspan', 1)) or 1 for c in cells[:-1]) + len(cells[-1:]) + len(rowspans))
        # update rowspan bookkeeping; 0 is a span to the bottom. 
        rowspans += [int(c.get('rowspan', 1)) or len(rows) - r for c in cells]
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
        for col, cell in enumerate(row_elem.find_all(['td', 'th'], recursive=False)):
            # adjust for preceding row and colspans
            col += span_offset
            while rowspans.get(col, 0):
                span_offset += 1
                col += 1

            # fill table data
            rowspan = rowspans[col] = int(cell.get('rowspan', 1)) or len(rows) - row
            colspan = int(cell.get('colspan', 1)) or colcount - col
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

room_occupancy = table_to_2d(occupancy_table, lambda x: x.attrs["bgcolor"])
for row in room_occupancy:
    print(row)
