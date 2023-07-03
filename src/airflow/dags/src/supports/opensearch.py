import json
import requests
from datetime import datetime

import pandas as pd


class OpenSearchRequest:
    def __init__(self, url, index):
        self._url = f"{url}/{index}/_search?scroll=1m"
        self._scroll_url = f"{url}/_search/scroll"
        self._scroll_id = None  # To Do : Delete Scroll Id After Use
        self._headers = {"Content-Type": "application/json"}
        self.query = None
        self.results = []
        self.start_datetime, self.end_datetime = None, None

    def set_datetime_range_query(
        self, start_str_datetime: str, end_str_datetime: str, size: int
    ):
        self.query = {
            "query": {
                "range": {
                    "datetime": {
                        "gte": self.__set_datetime(start_str_datetime),
                        "lt": self.__set_datetime(end_str_datetime),
                    }
                }
            },
            "size": size,
        }

    def __set_datetime(self, str_datetime):
        return datetime.strptime(str_datetime, "%Y-%m-%d %H:%M:%S").isoformat()

    def get_query_result_scroll_api(self):
        _res = self.get_query_result()

        if _res.status_code != 200:
            raise Exception("Status Code is not 200")

        _res_json = _res.json()
        self._scroll_id = _res_json["_scroll_id"]
        _hits = _res_json["hits"]["hits"]

        while _hits:
            self.results += [_hit["_source"] for _hit in _hits]
            _res = requests.post(
                self._scroll_url,
                headers=self._headers,
                data=json.dumps({"scroll": "1m", "scroll_id": self._scroll_id}),
            )
            _res_json = _res.json()
            try:
                _hits = _res_json["hits"]["hits"]
            except:
                break

        return pd.DataFrame(self.results)

    def get_query_result(self):
        return requests.post(
            self._url,
            headers=self._headers,
            data=json.dumps(self.query),
        )
