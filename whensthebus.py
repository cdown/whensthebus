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


DT_NOW = datetime.datetime.now()
DATE_STR_NOW = DT_NOW.strftime("%Y-%m-%d")

LiveBusSchedule = collections.namedtuple(
    "LiveBusSchedule", ["name", "departures"]
)


class BusInfo:
    """Functions that require API access, or process API data."""

    def __init__(
        self, app_id, app_key, api_base="http://transportapi.com/v3/"
    ):
        self.app_id = app_id
        self.app_key = app_key
        self.api_base = api_base
        self.log = logging.getLogger(type(self).__name__)

        if not self.app_id or not self.app_key:
            raise ValueError("Missing app credentials")

    def call_api(self, path, extra_query_params=None):
        """
        Call TransportAPI v3.

        path: A path, relative to api_base, to call.
        extra_query_params: Desired query params other than app_{id,key}.

        Returns a Python object parsed from the API's returned data.
        """

        parsed_url = urllib.parse.urlparse(self.api_base)
        query_params = {"app_id": self.app_id, "app_key": self.app_key}
        if extra_query_params:
            query_params.update(extra_query_params)
        parsed_url = parsed_url._replace(
            query=urllib.parse.urlencode(query_params),
            path=parsed_url.path + path,
        )

        req_obj = requests.get(urllib.parse.urlunparse(parsed_url))
        try:
            return req_obj.json()
        except json.decoder.JSONDecodeError as thrown_exc:
            raise ValueError(
                "Invalid JSON: {}".format(req_obj.text)
            ) from thrown_exc

    def live_bus_query(self, atco, queue_obj):
        """
        Get live buses for a single ATCO code.

        atco: The ATCO code to query.
        queue_obj: The queue to put the obtained data on to.

        This function doesn't return anything, as it's designed to be used in
        multiprocessing. As such, the data is put onto the specified queue.
        """

        path = "/uk/bus/stop/{}/live.json".format(atco)

        output = self.call_api(path)
        if "error" in output:
            raise ValueError(output["error"])

        # route -> times
        departures = collections.defaultdict(list)

        for sub in output["departures"].values():
            for departure in sub:
                dep_name = "{} to {}".format(
                    departure["line"], departure["direction"]
                )
                departures[dep_name].append(
                    timedelta_from_departure(departure)
                )

        # Sort to show the minimum time first...
        for tds in departures.values():
            tds.sort()

        # ...then sort the lines to show the closest.
        departures = collections.OrderedDict(
            sorted([(k, v) for k, v in departures.items()], key=lambda x: x[1])
        )

        queue_obj.put({atco: LiveBusSchedule(output["name"], departures)})

    def live_bus_query_multi(self, atcos, timeout):
        """
        Asynchronous wrapper around live_bus_query.

        atcos: The ATCOs to query.
        timeout: How long to wait for a single process.

        Returns: {atco: LiveBusSchedule}.
        """

        assert atcos, "BUG: no ATCOs?"

        queue_obj = multiprocessing.Queue()

        processes = [
            multiprocessing.Process(
                target=self.live_bus_query, args=(atco, queue_obj)
            )
            for atco in atcos
        ]

        for process in processes:
            process.start()

        results = {}

        while len(atcos) > len(results):
            try:
                result = queue_obj.get(block=True, timeout=timeout)
            except queue.Empty:
                # We'll handle this in the later check to check all ATCOs are
                # returned
                break
            else:
                results.update(result)

        if len(atcos) != len(results):
            self.log.error(
                "No results for ATCOs: %s",
                ", ".join(set(atcos) - set(results)),
            )

        for process in processes:
            process.terminate()

        return results


def human_timedelta(tdelta):
    """
    Outputs a timedelta to a human readable string. This is optimised for live
    transport, so the only magnitudes considered are hours and minutes. For
    values under 60 seconds, "Due" is returned.

    tdelta: The timedelta to humanise.

    Returns a string with the human-readable timedelta.
    """

    seconds = int(tdelta.total_seconds())
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
    """
    Given a departure, extract the relevant keys to work out how far away it is
    from the current time. If the date is unknown, assume it is today.

    departure: The departure to process.

    Returns a timedelta showing how far away this time is from now.
    """

    dep_date = departure["expected_departure_date"]
    if not dep_date:
        dep_date = DATE_STR_NOW

    to_parse = "{} {}".format(dep_date, departure["best_departure_estimate"])

    departure_time = datetime.datetime.strptime(to_parse, "%Y-%m-%d %H:%M")
    return departure_time - DT_NOW


def parse_args():
    """
    Take sys.argv and parse it with argparse's ArgumentParser.

    Returns the arguments already parsed into a Namespace.
    """

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
        help="maximum number of seconds to wait for data to be returned "
        "(default: %(default)s)",
        type=float,
        default=5.0,
    )
    return parser.parse_args()


def main():
    """
    Use BusInfo to query TransportAPI, then lay out the found bus times to
    stdout. Most of the specific formatting work is offloaded to other
    functions, but the actual printing and layout work happens here.
    """

    args = parse_args()

    bus = BusInfo(os.getenv("WTB_APP_ID"), os.getenv("WTB_APP_KEY"))

    results = bus.live_bus_query_multi(args.atco, args.timeout)

    for atco_idx, (atco, lbs) in enumerate(results.items()):
        print("{} ({}):".format(lbs.name, atco))

        for route, times in lbs.departures.items():
            print(
                "- {}: {}".format(
                    route, ", ".join(human_timedelta(t) for t in times)
                )
            )

        if atco_idx + 1 < len(results):
            print()


if __name__ == "__main__":
    main()
