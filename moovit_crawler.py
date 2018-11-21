import json
import requests
import time
from typing import List, Dict, Optional
from utils.exceptions import MoovitAPIException
from location import Location
from bs4 import BeautifulSoup






class MoovitUrl:
    BASE_URL = 'https://moovit.com/'
    API_URL = BASE_URL + '/api'
    LOCATION_URL = API_URL + '/location'
    ROUTE_SEARCH_URL = API_URL + '/route/search'
    ROUTE_RESULTS = API_URL + '/route/result'


class MoovitCrawler:
    HEADERS = {} # TODO change the query
    MAX_RESULTS_EXTRACTORS_TRIES = 10

    def __init__(self) -> None:
        self.session = None  # type: requests.Session

    def _initiate_session(self) -> str:
        if not self.session:
            self.session = requests.Session()
            resp = self.session.get('https://moovit.com/')
            soup = BeautifulSoup(resp.content , 'html.parser')
            container = soup.select_one('script#rbzscr')
            id = container.get_attribute_list('src')
            respId = self.session.get('https://moovit.com' + id[0])
            soupId = BeautifulSoup(respId.content, 'html.parser')
            soupText = soupId.text
            print(soupText)
            return soupText[13:-2]


    def set_headers(self, rzbid:str) -> dict:
        if rzbid == "":
            rzbid = 'EA30RoO2Ems4sBH8EdUC+zOANAmB8pNMqd0VdbyuV0niFpwkM8hCeyYKQl1qtRfTxEtTj0DPXVrLRVX+ADHRYOUuCowmeGMdVzaGdJ7ZT3xzS5OhG+ZtPTHM9wNxYO811sZn5n7OkWvkCZFNvN7xrMH0qzsquT3Ne8RHQPLBB7/6W4o6hknLO1UfBQJNOyVu58hcGAZKX6JynzJOMh58gmSU5/dSry3U2c6Y45Sa3so='
            HEADERS = {
                'a  ccept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
                'moovit_app_type': 'WEB_TRIP_PLANNER',
                'moovit_client_version': '5.2.0.1/V567',
                'moovit_metro_id': '1',
                'moovit_user_key': 'F27187',
                'rbzid': rzbid,
                'referer': 'https://moovit.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
            }
        else:
            HEADERS = {
                'a  ccept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
                'moovit_app_type': 'WEB_TRIP_PLANNER',
                'moovit_client_version': '5.2.0.1/V567',
                'moovit_metro_id': '1',
                'moovit_user_key': 'F27187',
                'rbzid': rzbid,
                'referer': 'https://moovit.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
            }
        return HEADERS

    @staticmethod
    def _serialize_to_json(response: requests.Response) -> Dict:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            raise MoovitAPIException(
                'Failed to receive token from the API route calculator')

    def get_location_suggestions(self, searched_location: str) -> List:
        rzbid = self._initiate_session()
        query = {
            'latitude': '32081817',
            'longitude': '34781349',
            'query': searched_location,
        }
        HEADERS = self.set_headers(rzbid)
        response = self.session.get(MoovitUrl.LOCATION_URL,
                                    params=query,
                                    headers=HEADERS)
        json_response = self._serialize_to_json(response)
        return json_response.get('results', [])

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
        rzbid = self._initiate_session()
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
        HEADERS = self.set_headers(rzbid)
        response = self.session.get(MoovitUrl.ROUTE_SEARCH_URL,
                                    params=query,
                                    headers=HEADERS)

        json_response = self._serialize_to_json(response)
        token = json_response.get('token')

        if not token:
            raise MoovitAPIException('Failed to receive token from the API')

        return self._extract_route_results(token)
