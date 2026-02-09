from sched import Event
from textwrap import dedent
import icalendar
from operator import attrgetter
from io import BytesIO
from datetime import datetime
from uuid import uuid5

def test_assumption_icalendar_sortable_keys() -> None:

    a = icalendar.Calendar()
    a.add('prodid', '-//author.example.com//')
    a.add('version', '2.0')
    a.add('method', 'PUBLISH')
    a.add('x-wr-calname', "Cal Name")

    assert a.to_ical() == b'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//author.example.com//\r\nMETHOD:PUBLISH\r\nX-WR-CALNAME:Cal Name\r\nEND:VCALENDAR\r\n'

    for component in "aZbYcWdXe":
        # create a hyper minimal event consisting only of a UID property, used as the sort key
        e = icalendar.Event()
        e.add("uid", icalendar.vText('uuid-'+component.upper()))
        a.add_component(e)

    baked_ical_file_content_unordered: str = a.to_ical().decode()

    # subcomponent items are sortable after insertion
    b = icalendar.Calendar.from_ical(baked_ical_file_content_unordered)
    b.subcomponents = sorted(b.subcomponents, key=lambda e: e.get("UID"))
    baked_ical_file_content_ordered: str = b.to_ical().decode()

    assert baked_ical_file_content_ordered == dedent(
        """
        BEGIN:VCALENDAR
        VERSION:2.0
        PRODID:-//author.example.com//
        METHOD:PUBLISH
        X-WR-CALNAME:Cal Name
        BEGIN:VEVENT
        UID:uuid-A
        END:VEVENT
        BEGIN:VEVENT
        UID:uuid-B
        END:VEVENT
        BEGIN:VEVENT
        UID:uuid-C
        END:VEVENT
        BEGIN:VEVENT
        UID:uuid-D
        END:VEVENT
        BEGIN:VEVENT
        UID:uuid-E
        END:VEVENT
        BEGIN:VEVENT
        UID:uuid-W
        END:VEVENT
        BEGIN:VEVENT
        UID:uuid-X
        END:VEVENT
        BEGIN:VEVENT
        UID:uuid-Y
        END:VEVENT
        BEGIN:VEVENT
        UID:uuid-Z
        END:VEVENT
        END:VCALENDAR
        """
    ).replace("\n", "\r\n").lstrip()


def test_ICalItemExporter_sorts() -> None:
    from communitybikeways.exporters import ICalItemExporter, ns
    from communitybikeways.items import Event

    writer_file = BytesIO()
    exporter = ICalItemExporter(writer_file)

    exporter.start_exporting()
    
    _fake_date = datetime.fromisoformat("2020-01-01T13:30:00Z")  # needed by exporter but unimportant

    expected_uids: list[str] = []

    for letter in "aZbYcWdXe":
        expected_uids.append(str(uuid5(ns, letter)))
        item = Event(
            summary = letter,
            url = letter,  # sort key is uuid5(url)
            start_datetime = _fake_date,
            end_datetime = _fake_date,
            updated_at = _fake_date,
            location = None,
            description = None,
        )
        exporter.export_item(item)
    exporter.finish_exporting()

    expected_uids_ordered = sorted(expected_uids)

    b = icalendar.Calendar.from_ical(writer_file.getvalue().decode())

    for (left, right) in zip(expected_uids_ordered, b.subcomponents):
        assert left == right.get('UID')
