
from scrapy.exporters import BaseItemExporter
import icalendar
from uuid import UUID, uuid5

from typing import Any
from io import BufferedWriter

from .items import Event

ns = UUID('b44256d5-dee8-4dee-9fd9-31451e47984e')

class ICalItemExporter(BaseItemExporter):
    # similar to the XML exporter
    def __init__(self, file: BufferedWriter, **kwargs: Any) -> None:
        super().__init__(dont_fail=True, **kwargs)
        self.file = file  # already-open file handle

        self.cal = icalendar.Calendar()
        self._kwargs.setdefault('ensure_ascii', not self.encoding)

    def start_exporting(self) -> None:
        self.cal.add('prodid', '-//communitybikewaysto.ca//verselogic.net//')
        self.cal.add('version', '2.0')
        self.cal.add('method', 'PUBLISH')
        self.cal.add('x-wr-calname', "Toronto Community Bikeways")

    def export_item(self, item: Event) -> None:
        e = icalendar.Event()

        e.add("summary", icalendar.vText(item['summary']))
        e.add('uid', icalendar.vText(str(uuid5(ns, item['url']))))
        e.add('url', icalendar.vText(item['url']))

        e.add("dtstart", icalendar.vDatetime(item['start_datetime']))
        e.add("dtend", icalendar.vDatetime(item['end_datetime']))
        e.add("dtstamp", icalendar.vDatetime(item['updated_at']))

        e.add("location", icalendar.vText(item['location']))

        e.add("description", icalendar.vText(item['description']))

        self.cal.add_component(e)


    def finish_exporting(self) -> None:
        self.cal.add_missing_timezones()
        self.cal.subcomponents = sorted(self.cal.subcomponents, key=lambda e: e.get("UID", '0'))  # stable ordering; sort top-level subcomponents by UID, components without a UID property sort first
        self.file.write(self.cal.to_ical(sorted=True))  # stable ordering; sort properties
