#!/usr/bin/env python

import requests
import datetime
import urllib
import json
import os
import collections

DT_NOW = datetime.datetime.now()


class BusInfo(object):
    def __init__(self, app_id, app_key, api_base="http://transportapi.com/v3/"):
        self.app_id = app_id
        self.app_key = app_key
        self.api_base = api_base

    def _call_api(self, path, extra_query_params=None):
        parsed_url = urllib.parse.urlparse(self.api_base)
        query_params = {"app_id": self.app_id, "app_key": self.app_key}
        if extra_query_params:
            query_params.extend(extra_query_params)
        parsed_url = parsed_url._replace(
            query=urllib.parse.urlencode(query_params), path=parsed_url.path + path
        )

        r = requests.get(urllib.parse.urlunparse(parsed_url))
        r.raise_for_status()
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            raise ValueError(r.text)

    def live_bus_query(self, atco):
        route_to_time = {}

        path = "/uk/bus/stop/{}/live.json".format(atco)
        json = self._call_api(path)

        # route -> times
        departures = collections.defaultdict(list)

        for sub in json["departures"].values():
            for departure in sub:
                dep_name = "{} to {}".format(departure["line"], departure["direction"])
                departures[dep_name].append(timedelta_from_departure(departure))

        # Sort to show the minimum time first...
        for tds in departures.values():
            tds.sort()

        # ...then sort the lines to show the closest.
        departures = collections.OrderedDict(
            sorted([k, v] for k, v in departures.items())
        )

        return departures


def flatten(multi):
    for sub in multi:
        for item in sub:
            yield item


def human_timedelta(td):
    seconds = int(td.total_seconds())
    magnitudes = [("hr", 60 * 60), ("min", 60)]

    parts = []

    for magnitude_name, magnitude_remainder in magnitudes:
        if seconds > magnitude_remainder:
            magnitude_value, seconds = divmod(seconds, magnitude_remainder)
            parts.append("{} {}".format(magnitude_value, magnitude_name))

    return ", ".join(parts)


def timedelta_from_departure(departure):
    departure_time = datetime.datetime.strptime(
        "{} {}".format(
            departure["expected_departure_date"], departure["best_departure_estimate"]
        ),
        "%Y-%m-%d %H:%M",
    )
    return departure_time - DT_NOW


def main():
    b = BusInfo(os.getenv("BI_APP_ID"), os.getenv("BI_APP_KEY"))

    for route, times in b.live_bus_query("490004733D").items():
        print("{}: {}".format(route, ", ".join(human_timedelta(t) for t in times)))


if __name__ == "__main__":
    main()
