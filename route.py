from prettytable import PrettyTable, ALL
from typing import Dict
from utils.message_manager import Alert

from action import (ROUTE_ACTIONS, PublicTransportAction, WalkingAction,
                    Waiting, from_moovit_time_to_date, NotUserDependableAction,
                    Line)


class Route:
    def __init__(self, route_details: Dict) -> None:
        self.actions = []
        self._raw_route = route_details

        itinerary = route_details.get('result', {}).get('itinerary', {})
        if not itinerary:
            return

        supplemental_data = route_details.get('supplementalData', {})

        for leg in itinerary.get('legs', []):
            for route_type in ROUTE_ACTIONS.keys():
                if leg[route_type] is not None:
                    action_title, ActionClass = ROUTE_ACTIONS[route_type]
                    action = ActionClass(leg[route_type],
                                         action_title,
                                         supplemental_data)
                    self.actions.append(action)

    def __str__(self) -> str:
        if not self.actions:
            return ''

        rows = []
        for action in self.actions:
            title = action.title

            try:
                start_time = from_moovit_time_to_date(action.start_time)
                end_time = from_moovit_time_to_date(action.end_time)
                description = f'{start_time}\n{end_time}'
            except TypeError:
                description = ''

            if isinstance(action, PublicTransportAction):
                lines_numbers = ', '.join(action.get_line_numbers())
                description += f'\n{lines_numbers}'
            if isinstance(action, WalkingAction):
                description += f'\n{action.action_time} minutes'
            if isinstance(action, Waiting):
                description += f'\n{action.action_time} minutes'

            rows.append([title, description])

        actions_table = PrettyTable(field_names=('Action', 'Details'),
                                    hrules=ALL, vrules=ALL)
        for row in rows:
            actions_table.add_row(row)

        return str(actions_table)

    def is_empty_route(self) -> bool:
        return len(self.actions) == 0

    def get_alert(self) -> Alert:
        time_differ = 0  # Time in seconds until the first relevant action

        for action in self.actions:
            if isinstance(action, WalkingAction):
                time_differ += action.action_time * 60
            elif (not isinstance(action, Waiting) and
                  isinstance(action, NotUserDependableAction)):
                closest_step = action.get_closest_step()
                arriving_time = from_moovit_time_to_date(closest_step.start_time)

                if isinstance(closest_step, Line):
                    return Alert(
                        title=f'Transport name: {closest_step.line_number}',
                        message=f'The line arrives at {arriving_time}'
                    )

    def not_user_dependable_counter(self) -> int:
        return len(list(filter(lambda action: isinstance(action, NotUserDependableAction), self.actions)))
