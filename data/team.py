import random

import numpy as np
import pandas as pd
from tabulate import tabulate
from wonderwords import RandomWord
from pluralizer import Pluralizer

from data.player import Player
from data.stadium import Stadium
from data.stats import TeamStats, l1, l2, l3

import json

FIELDING_POSITIONS_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
FIELDING_POSITIONS_TEXT = ['P', 'C', '1B', '2B', 'SS', '3B', 'LF', 'CF', 'RF', 'DH']


def get_position_by_number(pos_number): # this function is kinda stupid but that way it's not hard coded
    return FIELDING_POSITIONS_TEXT[FIELDING_POSITIONS_NUMBERS.index(pos_number)]


def get_position_by_name(pos_name): # this one makes a little more sense
    return FIELDING_POSITIONS_NUMBERS[FIELDING_POSITIONS_TEXT.index(pos_name)]


class Team():
    def __init__(self, data=None, player_data=None):
        if data is not None:
            self.from_json(data, player_data)
        else:
            csvfile = pd.read_csv('../data/sources/us-cities.csv')
            location = csvfile.sample()
            team_noun = Pluralizer().plural(RandomWord().word()).title()
            self.name = location.City.to_string(index=False) + " " + team_noun
            self.short_name = location.City.to_string(index=False)[:2].upper() + team_noun[1].upper()
            self.state = location['State short'].to_string(index=False)

            self.forty_man_roster = self.generate_forty_man()
            self.active_roster = []
            self.lineup = []
            self.generate_random_active_roster_and_lineup()
            self.randomize_lineup()

            self.home_stadium = Stadium([location.City.to_string(index=False), team_noun], self.state)
            self.stats = TeamStats()
            self.division = ''

            # management <---- NEXT UP!
            # game plays off of lineup and active roster.
            self.strategy = random.choice([0, 1, 2])  # 0 is 5 game trial, 1 is replace if below average, 2 is random if losing

    def create_game_roster(self):
        if self.strategy == 0:  # 5 games per player, then rotate.
            total_games = self.stats.wins + self.stats.losses
            if total_games != 0 and total_games % 5 == 0:
                for player_name in self.lineup:
                    player = self.get_player_by_name(player_name)
                    if player.position == 1:  # pitcher
                        eligible_pitchers = self.get_active_players_by_position(player.position)
                        eligible_pitchers.remove(player)
                        self.lineup[-1] = random.choice(eligible_pitchers).full_name
                    else:  # batter and fielder
                        # replace with random in active roster.
                        eligible_players = self.get_active_players_by_position(player.position)
                        eligible_players.remove(player)
                        self.lineup[self.get_spot_in_lineup(player_name)] = random.choice(eligible_players).full_name
        elif self.strategy == 1:  # every 10 games, replace if below average
            total_games = self.stats.wins + self.stats.losses
            if total_games != 0 and total_games % 10 == 0:  # every 10 games, but not the first.
                for player_name in self.lineup:
                    player = self.get_player_by_name(player_name)
                    if player.position == 1:  # pitcher
                        if player.pitching.era() <= self.team_average('era'):
                            eligible_pitchers = self.get_active_players_by_position(player.position)
                            eligible_pitchers.remove(player)
                            self.lineup[-1] = random.choice(eligible_pitchers).full_name
                    else:  # batter and fielder
                        if player.batting.ops() <= self.team_average('ops'):
                            # replace with next in active roster.
                            eligible_players = self.get_active_players_by_position(player.position)
                            eligible_players.remove(player)
                            self.lineup[self.get_spot_in_lineup(player_name)] = random.choice(eligible_players).full_name

        elif self.strategy == 2:  # 10 more losses than wins, shuffle.
            if self.stats.wins - self.stats.losses <= -10:
                for player_name in self.lineup:
                    player = self.get_player_by_name(player_name)
                    if player.position == 1:  # pitcher
                        eligible_pitchers = self.get_active_players_by_position(player.position)
                        eligible_pitchers.remove(player)
                        self.lineup[-1] = random.choice(eligible_pitchers).full_name
                    else:  # batter and fielder
                        # replace with random in active roster.
                        eligible_players = self.get_active_players_by_position(player.position)
                        self.lineup[self.get_spot_in_lineup(player_name)] = random.choice(eligible_players).full_name
                        eligible_players.remove(player)
        else:  # nothing
            pass

    def generate_forty_man(self):
        all_jersey_numbers = list(range(100))
        output = []
        for i in range(40):
            new_player = Player()
            new_player.team = self.name
            new_player.jersey_number = random.choice(all_jersey_numbers)
            all_jersey_numbers.remove(new_player.jersey_number)
            output.append(new_player)
        return output

    def randomize_lineup(self):
        pitcher = self.lineup[0]
        self.lineup = self.lineup[1:10]
        random.shuffle(self.lineup)
        self.lineup.append(pitcher)

    def team_average(self, stat_name): # if a player hasnt played, we throw the average so they have a chance.
        if stat_name == 'ops':
            ops_t = 0
            total_players = 0
            for player_name in self.active_roster:
                player = self.get_player_by_name(player_name)
                if player.batting.games_played == 0:
                    ops_t = 99999
                if player.position != 1:
                    ops_t += player.batting.ops()
                    total_players += 1
            return ops_t / total_players
        if stat_name == 'era':
            era_t = 0
            total_players = 0
            for player_name in self.active_roster:
                player = self.get_player_by_name(player_name)
                if player.pitching.games_pitched_in == 0:
                    era_t = 99999
                if player.position == 1:
                    era_t += player.pitching.era()
                    total_players += 1
            return era_t / total_players

    def generate_random_active_roster_and_lineup(self):
        # 6 OF, 8 IF, 3 C, 10 P, 2 flex
        eligible_players = list(self.forty_man_roster)

        # pitchers
        for i in range(10):
            p = eligible_players.pop()
            self.active_roster.append(p.full_name)
            p.position = 1
        self.lineup.append(self.active_roster[-1])

        # catchers
        for i in range(3):
            c = eligible_players.pop()
            self.active_roster.append(c.full_name)
            c.position = 2
        self.lineup.append(self.active_roster[-1])

        # outfielders, 6 total
        of_idx = 7
        filled_lineup = False
        for i in range(6):
            f = eligible_players.pop()
            self.active_roster.append(f.full_name)
            if of_idx > 9:
                of_idx = 7
                filled_lineup = True
            f.position = of_idx

            if of_idx < 10 and not filled_lineup:
                self.lineup.append(f.full_name)
            of_idx += 1

        # infielders, 8 total
        if_idx = 3
        filled_lineup = False
        for i in range(8):
            f = eligible_players.pop()
            self.active_roster.append(f.full_name)
            if if_idx > 6:
                if_idx = 3
                filled_lineup = True
            f.position = if_idx
            if if_idx < 7 and not filled_lineup:
                self.lineup.append(f.full_name)
            if_idx += 1

        # flex
        for i in range(2):
            f = eligible_players.pop()
            self.active_roster.append(f.full_name)
            f.position = 10
        self.lineup.append(self.active_roster[-1])

    def from_json(self, data, player_data):
        self.name = data['name']
        self.short_name = data['short_name']
        self.state = data['state']
        self.forty_man_roster = self.load_forty_man_from_json(json.loads(data['forty_man_roster']), player_data)
        self.active_roster = json.loads(data['active_roster'])
        self.lineup = json.loads(data['lineup'])
        self.home_stadium = Stadium(data=json.loads(data['home_stadium']))
        self.stats = TeamStats(json.loads(data['stats']))
        self.strategy = data['strategy']
        self.division = data['division']

    def __repr__(self):
        rd = self.stats.run_diff()  # run differential
        if np.sign(rd) < 0:
            pm = ''
        else:
            pm = '+'
        return self.name + ' (' + str(self.stats.wins) + 'W/' + str(self.stats.losses) + 'L/' + pm + str(rd) + ' RD)'

    def print_lineup(self):
        print("The " + self.name + " (" + self.state + ")")
        for i in range(10):
            player = self.get_player_by_name(self.lineup[i])
            print(get_position_by_number(player.position) + ": #" + str(player.jersey_number) + " " + player.full_name)

    def print_full_roster_stats(self):
        print(self.__repr__() + ' Stats')
        pitching_headers = ['#', 'Pitcher', 'Games', 'IP', 'ERA', 'HRs', 'K/BB', 'WHIP', 'Pitches/Game']
        pitching_stats = list()
        pitching_stats.append(pitching_headers)
        for pitcher in self.forty_man_roster:
            if pitcher.position != get_position_by_name('P') or pitcher.position == 0:
                continue
            p_stats = pitcher.pitching
            pitching_stats.append([pitcher.jersey_number, pitcher.full_name, p_stats.games_pitched_in, p_stats.innings_pitched, l2(p_stats.era()), p_stats.home_runs_allowed, p_stats.k_bb_str(), l2(p_stats.whip()), int(p_stats.pitches_per_game())])
        print(tabulate(pitching_stats))
        print()
        player_headers = ['#', 'Pos.', 'Player', '.AVG', 'HR', 'RBIs', 'OPS', '1B', 'xBH', 'BBs', 'SOs', 'PAs', 'Avg. EV', 'Games', 'Errors']
        player_table = list()
        player_table.append(player_headers)
        for player in self.forty_man_roster:
            if player.position == get_position_by_name('P') or player.position == 0:
                continue
            ps = player.batting
            fs = player.fielding
            player_table.append([player.jersey_number, get_position_by_number(player.position), player.full_name, l3(ps.b_avg()), ps.home_runs, ps.runs_batted_in, l3(ps.ops()), ps.singles, ps.xbh(), ps.walks, ps.strikeouts, ps.plate_appearances, l1(ps.avg_ev()), ps.games_played, fs.errors])
        print(tabulate(player_table))

    def get_player_at_position(self, position):
        num_position = 0
        if isinstance(position, str):
            num_position = get_position_by_name(position)
        else:
            num_position = position
        for player_name in self.lineup:
            player = self.get_player_by_name(player_name)
            if player.position == num_position:
                return player

    def get_spot_in_lineup(self, player_name):
        return self.lineup.index(player_name)

    def get_active_players_by_position(self, position):
        players = []
        num_position = 0
        if isinstance(position, str):
            num_position = get_position_by_name(position)
        else:
            num_position = position
        for player_name in self.active_roster:
            player = self.get_player_by_name(player_name)
            if player.position == num_position:
                players.append(player)
        return players

    def get_player_by_name(self, player_name):
        for player in self.forty_man_roster:
            if player.full_name == player_name:
                return player

    def convert_forty_man_to_json(self):
        names = []
        for player in self.forty_man_roster:
            names.append(player.full_name)
        return json.dumps(names)

    def get_players_as_json(self):
        dictionary = {}
        for player in self.forty_man_roster:
            dictionary[player.full_name] = player.to_json()
        return json.dumps(dictionary)

    def load_forty_man_from_json(self, forty_man_list, player_data):
        forty_man = []
        for man in forty_man_list:
            forty_man.append(Player(json.loads(player_data[man])))
        return forty_man

    def to_json(self):
        dictionary = {
            "name": self.name,
            "short_name": self.short_name,
            "state": self.state,
            "home_stadium": self.home_stadium.to_json(),
            "forty_man_roster": self.convert_forty_man_to_json(),
            "active_roster": json.dumps(self.active_roster),
            "lineup": json.dumps(self.lineup),
            "stats": self.stats.to_json(),
            "strategy": self.strategy,
            "division": self.division
        }
        with open("../game/saves/teams/" + self.name.replace(' ', '') + ".json", "w") as outfile:
            json.dump(dictionary, outfile)

