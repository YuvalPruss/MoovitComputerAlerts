import datetime
from enum import Enum

from typing import Dict, List


def from_moovit_time_to_date(moovit_time: int) -> str:
    real_epoch = moovit_time / 1000
    parsed_datetime = datetime.datetime.fromtimestamp(real_epoch)
    return parsed_datetime.strftime('%H:%M:%S')


class Action:
    def __init__(self,
                 raw_action: Dict,
                 action_title: str,
                 supplemental_data: Dict) -> None:
        self._raw_action = raw_action  # type: Dict
        self.title = action_title

        self.start_time = None  # type: int
        self.end_time = None  # type: int

    @property
    def action_time(self) -> int:
        """
        :return: The time in minutes to complete this action
        """
        return round((self.end_time - self.start_time) / 1000 / 60)


class NotUserDependableAction:
    def get_closest_step(self):
        raise NotImplementedError()


class WalkingAction(Action):
    def __init__(self,
                 raw_action: Dict,
                 action_title: str,
                 supplemental_data: Dict) -> None:
        super(WalkingAction, self).__init__(raw_action, action_title, supplemental_data)

        self.start_time = raw_action.get('time', {}).get('startTime')
        self.end_time = raw_action.get('time', {}).get('endTime')

        journey = raw_action.get('journey', {})
        self.origin = journey.get('origin', {}).get('latlon')
        self.dest = journey.get('dest', {}).get('latlon')


class Waiting(Action):
    def __init__(self, raw_action: Dict,
                 action_title: str,
                 supplemental_data: Dict) -> None:
        super(Waiting, self).__init__(raw_action, action_title, supplemental_data)

        self.start_time = raw_action.get('time', {}).get('startTime')
        self.end_time = raw_action.get('time', {}).get('endTime')


class LineTypes(Enum):
    TRAIN = 1
    BUS = 2


class Line:
    def __init__(self, line_details: Dict, supplemental_data: Dict) -> None:
        self._raw_line = line_details  # type: Dict
        self.line_id = line_details.get('lineId')  # type: int
        assert isinstance(self.line_id, int)
        self.start_time = line_details.get('time', {}).get('startTime')
        self.end_time = line_details.get('time', {}).get('endTime')

        self._supplemental_data = supplemental_data  # TODO remove this

        lines_groups = supplemental_data.get('lineGroupSummaryList', [])
        for line_group in lines_groups:
            line_summaries = line_group.get('lineSummaries', [])
            for line_summary in line_summaries:
                if line_summary.get('lineId') == self.line_id:
                    self.line_number = line_group.get('lineNumber')
                    self.line_type = line_group.get('type')


class PublicTransportAction(Action, NotUserDependableAction):
    def __init__(self, raw_action: Dict,
                 action_title: str,
                 supplemental_data: Dict) -> None:
        super(PublicTransportAction, self).__init__(raw_action, action_title, supplemental_data)

        self.lines = [Line(line, supplemental_data)
                      for line in raw_action.get('alternativeLines', [])]

    def get_line_numbers(self) -> List[str]:
        return [line.line_number for line in self.lines]

    def get_closest_step(self) -> Line:
        return min(self.lines, key=lambda line: line.start_time)


ROUTE_ACTIONS = {
    'bicycleLeg': ('Bicycle RIde', Action),
    'bicycleRentalLeg': ('Rental Bicycle Ride', Action),
    'carpoolRideLeg': ('Carpool', Action),
    'lineLeg': ('Public Transport Ride', PublicTransportAction),
    'lineWithAlternarivesLeg': ('Public Transport Ride', PublicTransportAction),
    'multiLineLeg': ('Public Transport Ride', PublicTransportAction),
    'pathwayWalkLeg': ('Walking', WalkingAction),
    'taxiLeg': ('Taxi Ride', Action),
    'waitToLineLeg': ('Bus Waiting', Waiting),
    'waitToMultiLineLeg': ('Bus Waiting', Waiting),
    'waitToTaxiLeg': ('Taxi Waiting', Waiting),
    'walkLeg': ('Walking', WalkingAction),
}
