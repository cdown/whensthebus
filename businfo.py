#!/usr/bin/env python

import requests
import urllib
import json
import os


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
        print(parsed_url)
        r = requests.get(urllib.parse.urlunparse(parsed_url))
        r.raise_for_status()
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            raise ValueError(r.text)

    def live_bus_query(self, atco):
        path = "/uk/bus/stop/{}/live.json".format(atco)
        json = self._call_api(path)
        return json


def main():
    b = BusInfo(os.getenv("BI_APP_ID"), os.getenv("BI_APP_KEY"))
    print(b.live_bus_query("490004733D"))


if __name__ == "__main__":
    main()
