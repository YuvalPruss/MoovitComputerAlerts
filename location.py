from typing import Dict

class Location:
    def __init__(self, location_details: Dict) -> None:
        self.id = location_details.get('id')
        self.title = location_details.get('title')
        sub_title = location_details.get('subTitle', [])
        self.sub_title = sub_title[0].get('text') if len(sub_title) > 0 else None
        actual_location = location_details.get('latLon', {})
        self.latitude = actual_location.get('latitude')
        self.longitude = actual_location.get('longitude')
        self.type = actual_location.get('type')

    @property
    def location_name(self) -> str:
        return ', '.join(filter(None, (self.title, self.sub_title)))

    @property
    def caption(self) -> str:
        return self.title.replace(' ', '+')
