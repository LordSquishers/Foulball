import json

import numpy as np


class BattingStats:
    def __init__(self, data=None):
        if data is not None:
            self.from_json(data)
        else:
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

    def b_avg(self):
        return self.hits / max(self.at_bats, 1)

    def avg_ev(self):
        if len(self.exit_velocity) == 0:
            return 0
        return np.average(self.exit_velocity)

    def slg(self):
        return (self.singles + 2 * self.doubles + 3 * self.triples + 4 * self.home_runs) / max(self.at_bats, 1)

    def obp(self):
        return (self.hits + self.hit_by_pitch + self.walks) / max(self.plate_appearances, 1)

    def ops(self):
        return self.obp() + self.slg()

    def xbh(self):
        return self.doubles + self.triples

    def lofopo_str(self):
        return str(self.out_lineout) + '/' + str(self.out_flyout) + '/' + str(self.out_popout)

    def to_json(self):
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

    def from_json(self, data):
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


class PitchingStats:
    def __init__(self, data=None):
        if data is not None:
            self.from_json(data)
        else:
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

    def era(self):
        return 9 * self.runs_allowed / max(self.innings_pitched, 1)

    def whip(self):
        return (self.walks_given + self.hits_allowed) / max(self.innings_pitched, 1)

    def pitches_per_game(self):
        return self.pitches / max(self.games_pitched_in, 1)

    def k_bb(self):
        return self.strikeouts / max(self.walks_given, 1)

    def k_bb_str(self):
        return str(self.strikeouts) + '/' + str(self.walks_given)

    def to_json(self):
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

    def from_json(self, data):
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


class FieldingStats:
    def __init__(self, data=None):
        if data is not None:
            self.from_json(data)
        else:
            self.errors = 0

    def to_json(self):
        dictionary = {
            "errors": self.errors
        }
        return json.dumps(dictionary)

    def from_json(self, data):
        self.errors = data['errors']


class TeamStats:
    def __init__(self, data=None):
        if data is not None:
            self.from_json(data)
        else:
            self.wins = 0
            self.losses = 0
            self.runs_scored = 0
            self.runs_against = 0

    def from_json(self, data):
        self.wins = data['wins']
        self.losses = data['losses']
        self.runs_scored = data['runs_scored']
        self.runs_against = data['runs_against']

    def run_diff(self):
        return self.runs_scored - self.runs_against

    def win_pct(self):
        if self.wins + self.losses == 0:
            return 0
        return self.wins / (self.wins + self.losses)

    def to_json(self):
        dictionary = {
            "wins": self.wins,
            "losses": self.losses,
            "runs_scored": self.runs_scored,
            "runs_against": self.runs_against
        }
        return json.dumps(dictionary)


# beautifies number for printing
def l1(number):
    return str(round(number, 1))


def l2(number):
    return str(round(number, 2))


def l3(number):
    # return str(round(number, 3))
    if number >= 1:
        output = '{0:.3f}'.format(number)
    else:
        output = '{0:.3f}'.format(number)[1:]
    if output == '':
        return '0'
    return output


def save_player_file(teams: list):
    dictionary = {}
    for team in teams:
        players_json = team.get_players_as_json()
        dictionary.update(json.loads(players_json))

    with open("../game/saves/players.json", "w") as outfile:
        json.dump(dictionary, outfile)


def load_player_file():
    with open('../game/saves/players.json') as f:
        all_players = json.load(f)
    return all_players
