import json

import numpy as np
import names

from data.stats import BattingStats, PitchingStats, FieldingStats

FIELDING_POSITIONS_NUMBERS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
FIELDING_POSITIONS_TEXT = ['N/A', 'P', 'C', '1B', '2B', 'SS', '3B', 'LF', 'CF', 'RF', 'DH']


def get_position_by_number(pos_number): # this function is kinda stupid but that way it's not hard coded
    return FIELDING_POSITIONS_TEXT[FIELDING_POSITIONS_NUMBERS.index(pos_number)]


def get_position_by_name(pos_name): # this one makes a little more sense
    return FIELDING_POSITIONS_NUMBERS[FIELDING_POSITIONS_TEXT.index(pos_name)]


class Player:
    def __init__(self, data=None):
        if data is not None:
            self.from_json(data)
        else:
            # cosmetic data
            self.gender = np.random.choice(['male', 'female'], 1, p=[0.8, 0.2])[0]
            self.first_name = names.get_first_name(gender=self.gender)
            self.last_name = names.get_last_name()
            self.full_name = self.first_name + " " + self.last_name
            self.age = int(max(np.random.normal(25, 5, 1)[0], 20))
            self.height_inches = int(np.round(np.random.normal(68, 4, 1))[0])
            self.weight_lbs = int(np.round(np.random.normal(180, 15, 1))[0])
            self.nationality = np.random.choice(['United States', 'Dominican Republic', 'Venezuela', 'Cuba', 'Puerto Rico', 'Mexico', 'Canada', 'Colombia', 'Panama', 'Japan', 'South Korea'], 1, p=[0.708, 0.115, 0.072, 0.023, 0.020, 0.017, 0.011, 0.010, 0.009, 0.008, 0.007])[0]

            # instrinsic data
            self.consistency = float(np.random.normal(0.5, 0.125, 1)[0])
            self.power = float(np.random.normal(0.5, 0.125, 1)[0])
            self.contact = float(np.random.normal(0.5, 0.125, 1)[0])
            self.crit_thinking_batting = float(np.random.normal(0.5, 0.125, 1)[0])
            self.crit_thinking_fielding = float(np.random.normal(0.5, 0.125, 1)[0])
            self.speed = float(np.random.normal(0.5, 0.125, 1)[0])
            self.throwing_power = float(np.random.normal(0.5, 0.125, 1)[0])
            self.pitching_control = float(np.random.normal(0.5, 0.125, 1)[0])
            self.pitching_spin = float(np.random.normal(0.5, 0.125, 1)[0])
            self.pitching_stamina = float(np.random.normal(0.5, 0.125, 1)[0])
            self.confidence = float(np.random.normal(0.5, 0.125, 1)[0])
            self.handedness = np.random.choice(['right', 'left', 'switch'], 1, p=[0.625, 0.25, 0.125])[0]
            self.injury_liability = float(np.random.normal(0.5, 0.125, 1)[0])
            self.charisma = float(np.random.normal(0.5, 0.125, 1)[0])

            # team traits
            self.position = 0
            self.team = ''
            self.jersey_number = 0

            # lifetime statistics
            self.batting = BattingStats()
            self.pitching = PitchingStats()
            self.fielding = FieldingStats()

    def set_team(self, jersey_number, team_name):
        self.team = team_name
        self.jersey_number = jersey_number

    def set_position(self, position):
        if isinstance(position, str):
            position = get_position_by_name(position)
        self.position = position

    def __repr__(self):
        return self.first_name + " " + self.last_name + " [" + get_position_by_number(self.position) + "] (#" + str(self.jersey_number) + ", " + self.team + ")"

    def from_json(self, data):
        self.gender = data['gender']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.full_name = data['full_name']
        self.age = data['age']
        self.height_inches = data['height_inches']
        self.weight_lbs = data['weight_lbs']
        self.nationality = data['nationality']

        # instrinsic data
        self.consistency = data['intrinsic']['consistency']
        self.power = data['intrinsic']['power']
        self.contact = data['intrinsic']['contact']
        self.crit_thinking_batting = data['intrinsic']['crit_thinking_batting']
        self.crit_thinking_fielding = data['intrinsic']['crit_thinking_fielding']
        self.speed = data['intrinsic']['speed']
        self.throwing_power = data['intrinsic']['throwing_power']
        self.pitching_control = data['intrinsic']['pitching_control']
        self.pitching_spin = data['intrinsic']['pitching_spin']
        self.pitching_stamina = data['intrinsic']['pitching_stamina']
        self.confidence = data['intrinsic']['confidence']
        self.handedness = data['intrinsic']['handedness']
        self.injury_liability = data['intrinsic']['injury_liability']
        self.charisma = data['intrinsic']['charisma']

        # team traits
        self.position = data['current_position']
        self.team = data['current_team']
        self.jersey_number = data['jersey_number']

        # lifetime statistics
        self.batting = BattingStats(json.loads(data['batting_stats']))
        self.pitching = PitchingStats(json.loads(data['pitching_stats']))
        self.fielding = FieldingStats(json.loads(data['fielding_stats']))

    def to_json(self):
        dictionary = {
            "gender": self.gender,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "height_inches": self.height_inches,
            "weight_lbs": self.weight_lbs,
            "nationality": self.nationality,
            "intrinsic": {
                "consistency": self.consistency,
                "power": self.power,
                "contact": self.contact,
                "crit_thinking_batting": self.crit_thinking_batting,
                "crit_thinking_fielding": self.crit_thinking_fielding,
                "speed": self.speed,
                "throwing_power": self.throwing_power,
                "pitching_control": self.pitching_control,
                "pitching_spin": self.pitching_spin,
                "pitching_stamina": self.pitching_stamina,
                "confidence": self.confidence,
                "handedness": self.handedness,
                "injury_liability": self.injury_liability,
                "charisma": self.charisma
            },
            "batting_stats": self.batting.to_json(),
            "pitching_stats": self.pitching.to_json(),
            "fielding_stats": self.fielding.to_json(),
            "current_team": self.team,
            "current_position": self.position,
            "jersey_number": self.jersey_number
        }
        return json.dumps(dictionary)