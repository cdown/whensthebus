#!/usr/bin/env python

"""Get live UK bus times in your terminal or in a libnotify popup"""

import argparse
import datetime
import urllib
import json
import os
import queue
import collections
import multiprocessing
import logging

import requests

log = logging.getLogger(__name__)

DT_NOW = datetime.datetime.now()
DATE_STR_NOW = DT_NOW.strftime("%Y-%m-%d")

LiveBusSchedule = collections.namedtuple("LiveBusSchedule", ["name", "departures"])


class BusInfo(object):
    def __init__(self, app_id, app_key, api_base="http://transportapi.com/v3/"):
        self.app_id = app_id
        self.app_key = app_key
        self.api_base = api_base

        if not self.app_id or not self.app_key:
            raise ValueError("Missing app credentials")

    def call_api(self, path, extra_query_params=None):
        parsed_url = urllib.parse.urlparse(self.api_base)
        query_params = {"app_id": self.app_id, "app_key": self.app_key}
        if extra_query_params:
            query_params.update(extra_query_params)
        parsed_url = parsed_url._replace(
            query=urllib.parse.urlencode(query_params), path=parsed_url.path + path
        )

        r = requests.get(urllib.parse.urlunparse(parsed_url))
        try:
            return r.json()
        except json.decoder.JSONDecodeError as thrown_exc:
            raise ValueError(r.text) from thrown_exc

    def live_bus_query(self, atco, queue_obj):
        path = "/uk/bus/stop/{}/live.json".format(atco)

        output = self.call_api(path)
        if "error" in output:
            raise ValueError(output["error"])

        # route -> times
        departures = collections.defaultdict(list)

        for sub in output["departures"].values():
            for departure in sub:
                dep_name = "{} to {}".format(departure["line"], departure["direction"])
                departures[dep_name].append(timedelta_from_departure(departure))

        # Sort to show the minimum time first...
        for tds in departures.values():
            tds.sort()

        # ...then sort the lines to show the closest.
        departures = collections.OrderedDict(
            sorted([(k, v) for k, v in departures.items()], key=lambda x: x[1])
        )

        queue_obj.put({atco: LiveBusSchedule(output["name"], departures)})

    def live_bus_query_multi(self, atcos, timeout):
        assert atcos, "BUG: no ATCOs?"

        q = multiprocessing.Queue()

        threads = [
            multiprocessing.Process(target=self.live_bus_query, args=(atco, q))
            for atco in atcos
        ]

        for t in threads:
            t.start()

        results = {}

        while len(atcos) > len(results):
            try:
                result = q.get(block=True, timeout=timeout)
            except queue.Empty:
                # We'll handle this in the later check to check all ATCOs are
                # returned
                break
            else:
                results.update(result)

        if len(atcos) != len(results):
            log.error("No results for ATCOs: %s", ", ".join(set(atcos) - set(results)))

        for t in threads:
            t.terminate()

        return results


def human_timedelta(td):
    seconds = int(td.total_seconds())
    magnitudes = [("hr", 60 * 60), ("min", 60)]

    parts = []

    for magnitude_name, magnitude_remainder in magnitudes:
        if seconds > magnitude_remainder:
            magnitude_value, seconds = divmod(seconds, magnitude_remainder)
            parts.append("{} {}".format(magnitude_value, magnitude_name))

    if not parts:
        parts.append("Due")

    return " ".join(parts)


def timedelta_from_departure(departure):
    dep_date = departure["expected_departure_date"]
    if not dep_date:
        dep_date = DATE_STR_NOW

    to_parse = "{} {}".format(dep_date, departure["best_departure_estimate"])

    departure_time = datetime.datetime.strptime(to_parse, "%Y-%m-%d %H:%M")
    return departure_time - DT_NOW


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-a",
        "--atco",
        metavar="CODE",
        action="append",
        help="the ATCO codes to look up (eg. 490004733D)",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--timeout",
        action="append",
        help="maximum number of seconds to wait for data to be returned (default: %(default)s)",
        type=float,
        default=5.0,
    )
    return parser.parse_args()


def main():
    args = parse_args()

    b = BusInfo(os.getenv("WTB_APP_ID"), os.getenv("WTB_APP_KEY"))

    results = b.live_bus_query_multi(args.atco, args.timeout)

    for atco_idx, (atco, lbs) in enumerate(results.items()):
        print("{} ({}):".format(lbs.name, atco))

        for route, times in lbs.departures.items():
            print(
                "- {}: {}".format(route, ", ".join(human_timedelta(t) for t in times))
            )

        if atco_idx + 1 < len(results):
            print()


if __name__ == "__main__":
    main()
