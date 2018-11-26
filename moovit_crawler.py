import json
import requests
import time
from typing import List, Dict, Optional
from utils.exceptions import MoovitAPIException
from location import Location
from bs4 import BeautifulSoup
import re

class MoovitUrl:
    BASE_URL = 'https://moovit.com/'
    BASE_URL_MISS = 'https://moovit.com'
    API_URL = BASE_URL + '/api'
    LOCATION_URL = API_URL + '/location'
    ROUTE_SEARCH_URL = API_URL + '/route/search'
    ROUTE_RESULTS = API_URL + '/route/result'


class MoovitCrawler:
    HEADERS = {'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
                'moovit_app_type': 'WEB_TRIP_PLANNER',
                'moovit_client_version': '5.2.0.1/V567',
                'moovit_metro_id': '1',
                'moovit_user_key': 'F27187',
                'referer': 'https://moovit.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'} # TODO change the query
    MAX_RESULTS_EXTRACTORS_TRIES = 10

    def __init__(self) -> None:
        self.session = None  # type: requests.Session

    def _initiate_session(self):
        if not self.session:
            self.session = requests.Session()
            resp = self.session.get(MoovitUrl.BASE_URL)
            return resp

    def get_rzbid(self) -> str:
        resp = self._initiate_session()
        content = BeautifulSoup(resp.content, 'html.parser')
        container = content.select_one('script#rbzscr')
        id = container.get_attribute_list('src')
        try:
            resp_id = self.session.get(MoovitUrl.BASE_URL_MISS + id[0])
        except ValueError as err:
            print("Check Youre Connection, No resp_id" + err)
        content_id = BeautifulSoup(resp_id.content, 'html.parser')
        content_text = content_id.text
        matches = re.findall(r'\"(.+?)\"', content_text)
        return matches[0]


    def get_headers(self)-> dict:
        new_dict = self.HEADERS
        try:
            rzbid = self.get_rzbid()
            new_val = {'rzbid': rzbid}
            new_dict.update(new_val)
            return new_dict
        except ValueError as err:
            print("Check Your'e Connection, No rzbid" + err)

    @staticmethod
    def _serialize_to_json(response: requests.Response) -> Dict:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            raise MoovitAPIException(
                'Failed to receive token from the API route calculator')

    def get_location_suggestions(self, searched_location: str) -> List:
        query = {
            'latitude': '32081817',
            'longitude': '34781349',
            'query': searched_location,
        }
        try:
            headers = self.get_headers()
            response = self.session.get(MoovitUrl.LOCATION_URL,
                                    params=query,
                                    headers=headers)
            json_response = self._serialize_to_json(response)
            return json_response.get('results', [])
        except ValueError as err:
            print("Check Your'e Connection, No headers" + err)


    @classmethod
    def _extract_route_results(cls, token: str) -> List:
        is_results_completed = False
        extract_tries = 0
        query = {'offset': '0', 'token': token}

        while not is_results_completed:
            response = requests.get(MoovitUrl.ROUTE_RESULTS,
                                    params=query,
                                    headers=cls.HEADERS)
            json_response = cls._serialize_to_json(response)

            if json_response.get('completed'):
                is_results_completed = True
                return json_response.get('results', [])

            extract_tries += 1
            if extract_tries > cls.MAX_RESULTS_EXTRACTORS_TRIES:
                # TODO log a possible problem here
                return []
            time.sleep(1)

    def _purify_search_results(cls, results: List) -> List:
        return [r for r in results if not r.get('result', {}).get('advertisment')]

    def search_route(self, location_from: Location,
                     location_to: Location) -> Optional[List]:
        travel_time = int(time.time() * 1000)  # TODO deal with changes
        travel_time = int((time.time() + 172800) * 1000)

        query = {
            'fromLocation_caption': location_from.caption,
            'fromLocation_id': location_from.id,
            'fromLocation_latitude': location_from.latitude,
            'fromLocation_longitude': location_from.longitude,
            'fromLocation_type': location_from.type,

            'toLocation_caption': location_to.caption,
            'toLocation_id': location_to.id,
            'toLocation_latitude': location_to.latitude,
            'toLocation_longitude': location_to.longitude,
            'toLocation_type': location_to.type,

            'isCurrentTime': 'false',  # TODO true for current time
            'routeTypes': '3,2,0,5,7',
            'time': '1540753200000',  # TODO use travel_time
            'timeType': '2',
            'tripPlanPref': '2',
        }
        headers = self.get_headers()
        response = self.session.get(MoovitUrl.ROUTE_SEARCH_URL,
                                    params=query,
                                    headers=headers)

        json_response = self._serialize_to_json(response)
        token = json_response.get('token')

        if not token:
            raise MoovitAPIException('Failed to receive token from the API')

        return self._extract_route_results(token)
