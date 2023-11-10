import json

import numpy as np


class Stadium:
    def __init__(self, name_options=None, state=None, data=None):
        if data is not None:
            self.from_json(data)
        else:
            self.name = self.generate_stadium_name(name_options)
            self.state = state

            self.fan_capacity = int(np.random.normal(40000, 2000, 1)[0])
            self.air_temperature = np.random.normal(70, 5, 1)[0]
            self.wind_speed = max(0, np.random.normal(5, 2, 1)[0])
            self.field_distances = [np.random.normal(335, 5, 1)[0], np.random.normal(400, 3.333, 1)[0], np.random.normal(335, 5, 1)[0]] # LCR

    def from_json(self, data):
        self.name = data['name']
        self.state = data['state']
        self.fan_capacity = data['fan_capacity']
        self.air_temperature = data['air_temperature']
        self.wind_speed = data['wind_speed']
        self.field_distances = [data['field_distances']['left'], data['field_distances']['center'], data['field_distances']['right']]

    def generate_stadium_name(self, names):
        possible_suffixes = ['Stadium', 'Park', 'Arena', 'Field', 'Coliseum', 'Center']
        suffix_probability = [0.3, 0.3, 0.04, 0.3, 0.03, 0.03]
        return np.random.choice(names, 1)[0] + " " + np.random.choice(possible_suffixes, 1, p=suffix_probability)[0]

    def to_json(self):
        dictionary = {
            "name": self.name,
            "state": self.state,
            "fan_capacity": self.fan_capacity,
            "air_temperature": self.air_temperature,
            "wind_speed": self.wind_speed,
            "field_distances": {
                "left": self.field_distances[0],
                "center": self.field_distances[1],
                "right": self.field_distances[2]
            }
        }
        return json.dumps(dictionary)
