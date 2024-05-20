import json
from json import JSONDecodeError

import names
import numpy as np

PLAYER_DATA = None

def convert_position_to_str(position):
    """
    Converts a position number to a string.
    :param position: Position as an int (1-10), 0 is N/A.
    :return: Position as str format (P, 2B, etc.).
    """
    return ['N/A', 'P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'][position]


class Player:
    """
    Object handling the Foulball Player.
    """

    def __init__(self, json_str: str = None):
        """
        Construct a new Player.
        :param json_str: JSON data for a player as a string (loaded into object by Player class).
        :return: None.
        """
        if json_str is not None:
            try:
                json_data = json.loads(json_str)  # load string into JSON object
                self.from_json(json_data)  # set fields using JSON data
            except JSONDecodeError as json_error:
                print('Unable to load player JSON data. Is this in a valid JSON format?')
                print(json_error)
                print('Bad player data loaded. Exiting to preserve integrity of simulation. ')
                exit(1)
        else:
            self.generate_from_scratch()  # generate new player data

    def __repr__(self):
        return self.first_name + ' ' + self.last_name + ' [' + convert_position_to_str(
            self.current_position) + '] (#' + str(self.jersey_number) + ', ' + self.current_team + ')'

    def generate_from_scratch(self) -> None:
        """
        Generates new data for a player.
        """
        # Cosmetic Data #
        self.gender = np.random.choice(['male', 'female'], 1, p=[0.8, 0.2])[0]
        self.first_name = names.get_first_name(gender=self.gender)
        self.last_name = names.get_last_name()
        self.full_name = self.first_name + " " + self.last_name
        self.age = int(max(np.random.normal(25, 5, 1)[0], 20))
        self.height_inches = int(np.round(np.random.normal(68, 4, 1))[0])
        self.weight_lbs = int(np.round(np.random.normal(180, 15, 1))[0])
        self.nationality = np.random.choice(
            ['United States', 'Dominican Republic', 'Venezuela', 'Cuba', 'Puerto Rico', 'Mexico', 'Canada', 'Colombia',
             'Panama', 'Japan', 'South Korea'], 1,
            p=[0.708, 0.115, 0.072, 0.023, 0.020, 0.017, 0.011, 0.010, 0.009, 0.008, 0.007])[0]

        # Intrinsic Data #
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

        # Team Data #
        self.position = 0
        self.team = ''
        self.jersey_number = 0

        # Tracked Statistical Data #
        self.stats = PlayerStatistics()

    def from_json(self, json_data) -> None:
        """
        Loads player data from a JSON object (not string).
        :param json_data: Pre-loaded JSON data (not a string).
        """

        # Cosmetic Data #
        self.gender = json_data['gender']
        self.first_name = json_data['first_name']
        self.last_name = json_data['last_name']
        self.full_name = json_data['full_name']
        self.age = json_data['age']
        self.height_inches = json_data['height_inches']
        self.weight_lbs = json_data['weight_lbs']
        self.nationality = json_data['nationality']

        # Intrinsic Data #
        self.consistency = json_data['intrinsic']['consistency']
        self.power = json_data['intrinsic']['power']
        self.contact = json_data['intrinsic']['contact']
        self.crit_thinking_batting = json_data['intrinsic']['crit_thinking_batting']
        self.crit_thinking_fielding = json_data['intrinsic']['crit_thinking_fielding']
        self.speed = json_data['intrinsic']['speed']
        self.throwing_power = json_data['intrinsic']['throwing_power']
        self.pitching_control = json_data['intrinsic']['pitching_control']
        self.pitching_spin = json_data['intrinsic']['pitching_spin']
        self.pitching_stamina = json_data['intrinsic']['pitching_stamina']
        self.confidence = json_data['intrinsic']['confidence']
        self.handedness = json_data['intrinsic']['handedness']
        self.injury_liability = json_data['intrinsic']['injury_liability']
        self.charisma = json_data['intrinsic']['charisma']

        # Team Data #
        self.current_position = json_data['current_position']
        self.current_team = json_data['current_team']
        self.jersey_number = json_data['jersey_number']

        # Tracked Stat Data #
        self.stats = PlayerStatistics(json_data['batting_stats'], json_data['fielding_stats'],
                                      json_data['pitching_stats'])

    def to_json(self) -> str:
        """
        Converts the Player to a JSON string.
        :return: JSON string.
        """
        data_object = {
            # Cosmetic Data #
            "gender": self.gender,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "height_inches": self.height_inches,
            "weight_lbs": self.weight_lbs,
            "nationality": self.nationality,

            # Intrinsic Data #
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

            # Tracked Stat Data #
            "batting_stats": self.stats.batting.to_json(),
            "pitching_stats": self.stats.pitching.to_json(),
            "fielding_stats": self.stats.fielding.to_json(),

            # Team Data #
            "current_team": self.current_team,
            "current_position": self.current_position,
            "jersey_number": self.jersey_number
        }
        return json.dumps(data_object)


class PlayerStatistics:
    """
    Object handling player statistics of all kinds.
    """

    def __init__(self, batting_str: str = None, fielding_str: str = None, pitching_str: str = None):
        self.batting = BattingStatistics(json.loads(batting_str))
        self.fielding = FieldingStatistics(json.loads(fielding_str))
        self.pitching = PitchingStatistics(json.loads(pitching_str))


class BattingStatistics:

    def __init__(self, data=None):
        if data is None:
            self.generate_empty_stats()
        else:
            self.load_from_json_string(data)

    def generate_empty_stats(self) -> None:
        self.at_bats = 0
        self.plate_appearances = 0
        self.hits = 0
        self.singles = 0
        self.doubles = 0
        self.triples = 0
        self.home_runs = 0
        self.strikeouts = 0
        self.walks = 0
        self.runs_batted_in = 0
        self.left_on_base = 0
        self.hit_by_pitch = 0
        self.exit_velocity = list()
        self.launch_angle = list()
        self.direction = list()
        self.batted_ball_outcome = list()
        self.games_played = 0
        self.out_flyout = 0
        self.out_lineout = 0
        self.out_popout = 0
        self.runs = 0
        self.batted_balls = 0

    def to_json(self) -> str:
        dictionary = {
            "at_bats": self.at_bats,
            "plate_appearances": self.plate_appearances,
            "hits": self.hits,
            "singles": self.singles,
            "doubles": self.doubles,
            "triples": self.triples,
            "home_runs": self.home_runs,
            "strikeouts": self.strikeouts,
            "walks": self.walks,
            "runs_batted_in": self.runs_batted_in,
            "left_on_base": self.left_on_base,
            "hit_by_pitch": self.hit_by_pitch,
            "exit_velocity": json.dumps(self.exit_velocity),
            "launch_angle": json.dumps(self.launch_angle),
            "direction": json.dumps(self.direction),
            "batted_ball_outcome": json.dumps(self.batted_ball_outcome),
            "games_played": self.games_played,
            "out_flyout": self.out_flyout,
            "out_lineout": self.out_lineout,
            "out_popout": self.out_popout,
            "runs": self.runs,
            "batted_balls": self.batted_balls
        }
        return json.dumps(dictionary)

    def load_from_json_string(self, data) -> None:
        """
        :param data: JSON object
        """
        self.at_bats = data['at_bats']
        self.plate_appearances = data['plate_appearances']
        self.hits = data['hits']
        self.singles = data['singles']
        self.doubles = data['doubles']
        self.triples = data['triples']
        self.home_runs = data['home_runs']
        self.strikeouts = data['strikeouts']
        self.walks = data['walks']
        self.runs_batted_in = data['runs_batted_in']
        self.left_on_base = data['left_on_base']
        self.hit_by_pitch = data['hit_by_pitch']
        self.exit_velocity = json.loads(data['exit_velocity'])
        self.launch_angle = json.loads(data['launch_angle'])
        self.direction = json.loads(data['direction'])
        self.batted_ball_outcome = json.loads(data['batted_ball_outcome'])
        self.games_played = data['games_played']
        self.out_flyout = data['out_flyout']
        self.out_lineout = data['out_lineout']
        self.out_popout = data['out_popout']
        self.runs = data['runs']
        self.batted_balls = data['batted_balls']

    def b_avg(self) -> float:
        return self.hits / max(self.at_bats, 1)

    def avg_ev(self) -> float:
        if len(self.exit_velocity) == 0:
            return 0
        return np.average(self.exit_velocity)

    def slg(self) -> float:
        return (self.singles + 2 * self.doubles + 3 * self.triples + 4 * self.home_runs) / max(self.at_bats, 1)

    def obp(self) -> float:
        return (self.hits + self.hit_by_pitch + self.walks) / max(self.plate_appearances, 1)

    def ops(self) -> float:
        return self.obp() + self.slg()

    def xbh(self) -> float:
        return self.doubles + self.triples

    def lofopo_str(self) -> str:
        return str(self.out_lineout) + '/' + str(self.out_flyout) + '/' + str(self.out_popout)


class FieldingStatistics:

    def __init__(self, data=None):
        if data is None:
            self.generate_empty_stats()
        else:
            self.load_from_json_string(data)

    def load_from_json_string(self, data) -> None:
        """
        :param data: JSON object
        """
        self.errors = data['errors']

    def to_json(self) -> str:
        dictionary = {
            "errors": self.errors
        }
        return json.dumps(dictionary)

    def generate_empty_stats(self) -> None:
        self.errors = 0


class PitchingStatistics:

    def __init__(self, data=None):
        if data is None:
            self.generate_empty_stats()
        else:
            self.load_from_json_string(data)

    def load_from_json_string(self, data) -> None:
        """
        :param data: JSON object
        """
        self.games_pitched_in = data['games_pitched_in']
        self.shutouts = data['shutouts']
        self.innings_pitched = data['innings_pitched']
        self.hits_allowed = data['hits_allowed']
        self.runs_allowed = data['runs_allowed']
        self.home_runs_allowed = data['home_runs_allowed']
        self.walks_given = data['walks_given']
        self.strikeouts = data['strikeouts']
        self.hit_by_pitches = data['hit_by_pitches']
        self.batters_faced = data['batters_faced']
        self.left_on_base = data['left_on_base']
        self.pitches = data['pitches']
        self.singles_allowed = data['singles_allowed']
        self.extra_base_hits_allowed = data['extra_base_hits_allowed']
        self.strikes = data['strikes']
        self.balls = data['balls']

        self.exit_velocity_against = json.loads(data['exit_velocity_against'])
        self.launch_angle_against = json.loads(data['launch_angle_against'])
        self.direction_against = json.loads(data['direction_against'])
        self.batted_ball_outcome_against = json.loads(data['batted_ball_outcome_against'])

    def to_json(self) -> str:
        dictionary = {
            "games_pitched_in": self.games_pitched_in,
            "shutouts": self.shutouts,
            "innings_pitched": self.innings_pitched,
            "hits_allowed": self.hits_allowed,
            "runs_allowed": self.runs_allowed,
            "home_runs_allowed": self.home_runs_allowed,
            "walks_given": self.walks_given,
            "strikeouts": self.strikeouts,
            "hit_by_pitches": self.hit_by_pitches,
            "batters_faced": self.batters_faced,
            "left_on_base": self.left_on_base,
            "pitches": self.pitches,
            "singles_allowed": self.singles_allowed,
            "extra_base_hits_allowed": self.extra_base_hits_allowed,
            "strikes": self.strikes,
            "balls": self.balls,

            "exit_velocity_against": json.dumps(self.exit_velocity_against),
            "launch_angle_against": json.dumps(self.launch_angle_against),
            "direction_against": json.dumps(self.direction_against),
            "batted_ball_outcome_against": json.dumps(self.batted_ball_outcome_against)
        }
        return json.dumps(dictionary)

    def generate_empty_stats(self) -> None:
        self.games_pitched_in = 0
        self.shutouts = 0
        self.innings_pitched = 0
        self.hits_allowed = 0
        self.runs_allowed = 0
        self.home_runs_allowed = 0
        self.walks_given = 0
        self.strikeouts = 0
        self.hit_by_pitches = 0
        self.batters_faced = 0
        self.left_on_base = 0
        self.pitches = 0
        self.singles_allowed = 0
        self.extra_base_hits_allowed = 0
        self.strikes = 0
        self.balls = 0

        self.exit_velocity_against = list()
        self.launch_angle_against = list()
        self.direction_against = list()
        self.batted_ball_outcome_against = list()

    def era(self) -> float:
        return 9 * self.runs_allowed / max(self.innings_pitched, 1)

    def whip(self) -> float:
        return (self.walks_given + self.hits_allowed) / max(self.innings_pitched, 1)

    def pitches_per_game(self) -> float:
        return self.pitches / max(self.games_pitched_in, 1)

    def k_bb(self) -> float:
        return self.strikeouts / max(self.walks_given, 1)

    def k_bb_str(self) -> str:
        return str(self.strikeouts) + '/' + str(self.walks_given)


def save_player_file(teams: list) -> None:
    dictionary = {}
    for team in teams:
        players_json = team.get_players_as_json()
        dictionary.update(json.loads(players_json))

    with open("saves/players.json", "w") as outfile:
        json.dump(dictionary, outfile)


def load_player_file():
    """
    Loads saved players from file.
    :return: Player objects to be sent to Player class.
    """
    with open('saves/players.json') as f:
        all_players = json.load(f)
    return all_players

