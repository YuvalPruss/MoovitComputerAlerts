from typing import Optional

from moovit_crawler import MoovitCrawler
from utils.message_manager import MessageManager
from location import Location
from route import Route


MAX_NOT_USER_DEPENDABLE_ACTIONS = 1


def choose_location(destination_location: str,
                    moovit_crawler: MoovitCrawler,
                    received_location_from: Optional[str]=None) -> Location:
    if not received_location_from:
        received_location_from = input(f'Enter {destination_location} location: ')

    location_from_suggestions = \
        moovit_crawler.get_location_suggestions(received_location_from)

    p_location_from_suggestions = list(map(lambda l: Location(l),
                                           location_from_suggestions))

    if len(p_location_from_suggestions) == 1:
        return p_location_from_suggestions[0]

    for index, suggested_from_location in enumerate(
            p_location_from_suggestions):
        print(f'[{index}] {suggested_from_location.location_name}')

    selected_index = input('Enter the location number: ')
    while (not selected_index.isdigit() or
           int(selected_index) not in range(len(p_location_from_suggestions))):
        selected_index = input('Wring number! Enter again: ')

    return p_location_from_suggestions[int(selected_index)]


if __name__ == '__main__':
    moovit_crawler = MoovitCrawler()

    origin_location = choose_location('origin', moovit_crawler)
    dest_location = choose_location('dest', moovit_crawler)


    results = moovit_crawler.search_route(origin_location, dest_location)
    routes = [Route(result) for result in results]

    clean_routes = []
    for route in routes:
        if (not route.is_empty_route() and
                route.not_user_dependable_counter() <= MAX_NOT_USER_DEPENDABLE_ACTIONS):
            clean_routes.append(route)

    message_manager = MessageManager()
    alerts = [route.get_alert() for route in clean_routes]

    for route in clean_routes:
        print(route)
        print('-'*100)

    for alert in alerts:
        message_manager.show_message(alert.title, alert.message)
