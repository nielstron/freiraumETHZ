# FreiRaum @ ETHZ

Find free rooms at ETHZ Campuses.

## Why

At ETHZ, study spaces are sparse _[citation needed]_, and hence it would be really useful to know
if there is not a normal seminar room close and unoccupied...
Well here it is, a tool that provides you with the closest
unoccupied room.

## How


ETHZ provides information on free rooms via http://www.rauminfo.ethz.ch .
This site is a terrible, terrible source of information and hardly machine readable..
but it can (and will) be scraped.

##### Current state

Make sure you have python3.9+ installed and installed all listed requirements.

Then, edit the variable `FILTER` in example.py to suit your needs. Finally run

```bash
python3 freiraum.py
```

##### Future vision:

The resulting information is fetched once a day and stored in a small relational database
that can be queried for unoccupied rooms.
