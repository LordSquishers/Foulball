import json
import random
from json import JSONDecodeError

import numpy as np
import pandas as pd
from tabulate import tabulate
from wonderwords import RandomWord
from pluralizer import Pluralizer

from data.player import PLAYER_DATA, Player
from data.stadium import Stadium
from data.text_formatting import l1, l2, l3

FIELDING_POSITIONS_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
FIELDING_POSITIONS_TEXT = ['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH']


def get_position_by_number(pos_number: int) -> str:  # this function is kinda stupid but that way it's not hard coded
    return FIELDING_POSITIONS_TEXT[FIELDING_POSITIONS_NUMBERS.index(pos_number)]


def get_position_by_name(pos_name: str) -> int:  # this one makes a little more sense
    return FIELDING_POSITIONS_NUMBERS[FIELDING_POSITIONS_TEXT.index(pos_name)]


class TeamStatistics:

    def __init__(self, data=None):
        if data is None:
            self.generate_empty_stats()
        else:
            self.load_from_json(data)

    def generate_empty_stats(self) -> None:
        self.wins = 0
        self.losses = 0
        self.runs_scored = 0
        self.runs_against = 0

    def to_json(self) -> str:
        dictionary = {
            "wins": self.wins,
            "losses": self.losses,
            "runs_scored": self.runs_scored,
            "runs_against": self.runs_against
        }
        return json.dumps(dictionary)

    def load_from_json(self, data) -> None:
        """
        :param data: JSON object
        :return:
        """
        self.wins = data['wins']
        self.losses = data['losses']
        self.runs_scored = data['runs_scored']
        self.runs_against = data['runs_against']

    def run_diff(self) -> int:
        return self.runs_scored - self.runs_against

    def win_pct(self) -> float:
        if self.wins + self.losses == 0:
            return 0
        return self.wins / (self.wins + self.losses)

    def total_games(self) -> int:
        return self.wins + self.losses


class Team:
    """
    Object handling a Foulball Team
    """
    def __init__(self, json_str: str = None):
        """
        Construct a new Team.
        :param json_str: JSON data for a team as a string (loaded into object by Team class).
        """
        if json_str is not None:
            try:
                json_data = json.loads(json_str)
                self.from_json(json_data)
            except JSONDecodeError as json_error:
                print('Unable to load team JSON data. Is this a valid JSON format?')
                print(json_error)
                print('Bad team data loaded. Exiting to preserve game.')
                exit(1)
        else:
            self.generate_from_scratch()

    def __repr__(self):
        """
        Format: TEAM NAME (#W/#L/+-RD)
        :return: string representation of the team.
        """
        run_diff = self.stats.run_diff()
        if np.sign(run_diff) < 0:
            plus_minus = '-'
        else:
            plus_minus = '+'
        return self.name + ' (' + str(self.stats.wins) + 'W/' + str(self.stats.losses) + 'L/' + plus_minus + str(run_diff) + ' RD)'

    def print_lineup(self) -> None:
        """
        TODO- move to display class.
        Prints the game lineup (formatted) to the console.
        """
        print("The " + self.name + " (" + self.state + ")")
        for player in self.game_lineup.values():
            player = self.get_player_by_name(player)
            print(get_position_by_number(player.position) + ": #" + str(player.jersey_number) + " " + player.full_name)

    def print_full_roster_stats(self) -> None:
        """
        TODO- move to display class.
        Prints the full forty-man roster as a formatted console output.
        """
        print(self.__repr__() + ' Stats')
        pitching_headers = ['#', 'Pitcher', 'Games', 'IP', 'ERA', 'HRs', 'K/BB', 'WHIP', 'Pitches/Game']
        pitching_stats = list()
        pitching_stats.append(pitching_headers)
        for pitcher in self.forty_man_roster:
            if pitcher.position != get_position_by_name('P') or pitcher.position == 0:
                continue
            p_stats = pitcher.pitching
            pitching_stats.append(
                [pitcher.jersey_number, pitcher.full_name, p_stats.games_pitched_in, p_stats.innings_pitched, l2(p_stats.era()), p_stats.home_runs_allowed,
                 p_stats.k_bb_str(), l2(p_stats.whip()), int(p_stats.pitches_per_game())])
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
            player_table.append(
                [player.jersey_number, get_position_by_number(player.position), player.full_name, l3(ps.b_avg()), ps.home_runs, ps.runs_batted_in, l3(ps.ops()),
                 ps.singles, ps.xbh(), ps.walks, ps.strikeouts, ps.plate_appearances, l1(ps.avg_ev()), ps.games_played, fs.errors])
        print(tabulate(player_table))

    def get_player_at_field_position_in_lineup(self, field_position) -> Player:
        """
        Finds the player at the specified field position in the game lineup.
        :param field_position: Position as text or number.
        :return: Player data for the specified position (from lineup)
        """

        if isinstance(field_position, str):
            num_position = get_position_by_name(field_position)
        else:
            num_position = field_position
        for player_name in self.game_lineup.values():
            player = self.get_player_by_name(player_name)
            if player.position == num_position:
                return player
        print('No player in lineup found at position ' + str(num_position) + '! Very odd.')

    def get_number_in_lineup(self, player_full_name) -> int:
        """
        TODO- this might not work
        Get the number of the player in the lineup. If the player is not in the lineup, returns 0.
        :param player_full_name: Player full name.
        :return: Lineup order 1-9 (0 being not found)
        """
        if player_full_name in self.game_lineup.values():
            return list(self.game_lineup.keys()).index(list(self.game_lineup.keys())[list(self.game_lineup.values()).index(player_full_name)])
        else:
            return 0

    def get_active_players_by_position(self, position) -> list:
        """
        Gets active players according to position. Infielders and outfielders are lumped into their own groups.
        :param position: Position as number or string.
        :return: List of players in the position category.
        """

        if isinstance(position, str):
            position_as_number = get_position_by_name(position)
        else:
            position_as_number = position

        if 2 < position_as_number < 7:  # infield
            return self.active_roster['IF']
        elif 6 < position_as_number < 10:  # outfield
            return self.active_roster['OF']
        else:
            return self.active_roster[get_position_by_number(position_as_number)]

    def generate_forty_man_roster(self) -> list:
        """
        Generates a forty-man roster from randomly created players. Unique jersey numbers.
        :return: A list of players in the forty-man roster
        """
        all_jersey_numbers = list(range(100))
        output = []
        for i in range(40):
            new_player = Player()
            new_player.team = self.name
            new_player.jersey_number = random.choice(all_jersey_numbers)
            all_jersey_numbers.remove(new_player.jersey_number)
            output.append(new_player)
        return output

    def get_player_by_name(self, player_full_name: str) -> Player:
        """
        Gets a player from the forty-man roster and returns the player data.
        :param player_full_name: full name of the player
        :return: Player data
        """
        for player in self.forty_man_roster:
            if player.full_name == player_full_name:
                return player

    def get_players_as_json(self) -> str:
        """
        Returns all the teams players as a JSON string with the ids as keys and the player data as the value.
        :return: JSON string with the ids as keys and the player data
        """
        data_object = {}
        for player in self.forty_man_roster:
            data_object[player.full_name + str(player.height_inches)] = player.to_json()
        return json.dumps(data_object)

    def convert_forty_man_to_json(self) -> str:
        """
        Converts the forty-man roster into a JSON string for storage.
        :return: JSON string containing player ids.
        """
        ids = []
        for player in self.forty_man_roster:
            ids.append(player.full_name + str(player.height_inches))
        return json.dumps(ids)

    def load_forty_man_from_json(self, json_str: str):
        """
        Pulls the forty-man roster from a JSON string of the player ids.
        :param json_str: String containing the player ids
        :return: A list of Player objects.
        """
        forty_man = []
        for player_id in json.loads(json_str):
            forty_man.append(Player(json.loads(PLAYER_DATA[player_id])))
        return forty_man

    def update_lineup(self) -> None:
        """
        Using the team strategy, updates the lineup for the next game.
        """
        # possible there is no lineup yet, so check and randomly select if so.
        for pos_name in FIELDING_POSITIONS_TEXT:
            if self.game_lineup[pos_name] == '':
                # randomly select pitcher from active list 'P'
                self.game_lineup['P'] = random.choice(self.active_roster['P'])

                # randomly select catcher from active list 'C'
                self.game_lineup['C'] = random.choice(self.active_roster['C'])

                # randomly select infielders from active list 'IF'
                eligible_infielders = list(self.active_roster['IF'])
                self.game_lineup['1B'] = random.choice(eligible_infielders)
                eligible_infielders.remove(self.game_lineup['1B'])
                self.game_lineup['2B'] = random.choice(eligible_infielders)
                eligible_infielders.remove(self.game_lineup['2B'])
                self.game_lineup['3B'] = random.choice(eligible_infielders)
                eligible_infielders.remove(self.game_lineup['3B'])
                self.game_lineup['SS'] = random.choice(eligible_infielders)
                eligible_infielders.remove(self.game_lineup['SS'])

                # randomly select outfielders from active list 'OF'
                eligible_outfielders = list(self.active_roster['OF'])
                self.game_lineup['LF'] = random.choice(eligible_outfielders)
                eligible_outfielders.remove(self.game_lineup['LF'])
                self.game_lineup['CF'] = random.choice(eligible_outfielders)
                eligible_outfielders.remove(self.game_lineup['CF'])
                self.game_lineup['RF'] = random.choice(eligible_outfielders)
                eligible_outfielders.remove(self.game_lineup['RF'])

                # randomly select DH from active list 'DH'
                self.game_lineup['DH'] = random.choice(self.active_roster['DH'])
                break

        # pull the list of eligible players by category #
        eligible_pitchers: [str] = self.get_active_players_by_position('P')
        eligible_infielders: [str] = self.get_active_players_by_position('IF')
        eligible_outfielders: [str] = self.get_active_players_by_position('OF')
        eligible_catchers: [str] = self.get_active_players_by_position('C')
        eligible_designated_hitters: [str] = self.get_active_players_by_position('DH')

        # per strategy implementation #
        if self.strategy == 0:  # every 5 games, randomly choose next person
            if self.stats.total_games() != 0 and self.stats.total_games() % 5 == 0:
                for position_name in FIELDING_POSITIONS_TEXT:
                    if position_name == 'P':  # pitcher
                        new_pitching_choice: str = random.choice(eligible_pitchers)
                        self.game_lineup[position_name] = new_pitching_choice
                    elif position_name in ['1B', '2B', '3B', 'SS']:
                        new_infielder_choice: str = random.choice(eligible_infielders)
                        self.game_lineup[position_name] = new_infielder_choice
                        eligible_infielders.remove(new_infielder_choice)
                    elif position_name in ['LF', 'CF', 'RF']:
                        new_outfielder_choice: str = random.choice(eligible_outfielders)
                        self.game_lineup[position_name] = new_outfielder_choice
                        eligible_outfielders.remove(new_outfielder_choice)
                    elif position_name == 'C':
                        new_catcher_choice: str = random.choice(eligible_catchers)
                        self.game_lineup[position_name] = new_catcher_choice
                        eligible_catchers.remove(new_catcher_choice)
                    elif position_name == 'DH':
                        new_designated_hitter: str = random.choice(eligible_designated_hitters)
                        self.game_lineup[position_name] = new_designated_hitter
                        eligible_designated_hitters.remove(new_designated_hitter)
                    # set the position for the player
                    self.get_player_by_name(self.game_lineup[position_name]).position = get_position_by_name(position_name)
        elif self.strategy == 1:  # every 10 games, replace if below team average
            if self.stats.total_games() != 0 and self.stats.total_games() % 10 == 0:
                for position_name in FIELDING_POSITIONS_TEXT:
                    old_player_name: str = self.game_lineup[position_name]
                    old_player: Player = self.get_player_by_name(old_player_name)
                    if position_name == 'P':  # here we care about ERA
                        if old_player.stats.pitching.era() <= self.get_team_average('era'):
                            eligible_pitchers.remove(old_player_name)
                            self.game_lineup[position_name] = random.choice(eligible_pitchers)
                    else:  # everyone else we care about OPS
                        if old_player.stats.batting.ops() <= self.get_team_average('ops'):
                            if position_name == 'C':
                                eligible_catchers.remove(old_player_name)
                                self.game_lineup[position_name] = random.choice(eligible_catchers)
                            elif position_name == 'DH':
                                eligible_designated_hitters.remove(old_player_name)
                                self.game_lineup[position_name] = random.choice(eligible_designated_hitters)
                            elif position_name in ['1B', '2B', '3B', 'SS']:
                                eligible_infielders.remove(old_player_name)
                                self.game_lineup[position_name] = random.choice(eligible_infielders)
                            elif position_name in ['LF', 'CF', 'RF']:
                                eligible_outfielders.remove(old_player_name)
                                self.game_lineup[position_name] = random.choice(eligible_outfielders)
                    # set the position for the player
                    self.get_player_by_name(self.game_lineup[position_name]).position = get_position_by_name(position_name)
        elif self.strategy == 2:  # if team has X more losses than wins, randomly choose
            if self.stats.wins - self.stats.losses <= -10:
                for position_name in FIELDING_POSITIONS_TEXT:
                    if position_name == 'P':  # pitcher
                        new_pitching_choice: str = random.choice(eligible_pitchers)
                        self.game_lineup[position_name] = new_pitching_choice
                    elif position_name in ['1B', '2B', '3B', 'SS']:
                        new_infielder_choice: str = random.choice(eligible_infielders)
                        self.game_lineup[position_name] = new_infielder_choice
                        eligible_infielders.remove(new_infielder_choice)
                    elif position_name in ['LF', 'CF', 'RF']:
                        new_outfielder_choice: str = random.choice(eligible_outfielders)
                        self.game_lineup[position_name] = new_outfielder_choice
                        eligible_outfielders.remove(new_outfielder_choice)
                    elif position_name == 'C':
                        new_catcher_choice: str = random.choice(eligible_catchers)
                        self.game_lineup[position_name] = new_catcher_choice
                        eligible_catchers.remove(new_catcher_choice)
                    elif position_name == 'DH':
                        new_designated_hitter: str = random.choice(eligible_designated_hitters)
                        self.game_lineup[position_name] = new_designated_hitter
                        eligible_designated_hitters.remove(new_designated_hitter)
                    # set the position for the player
                    self.get_player_by_name(self.game_lineup[position_name]).position = get_position_by_name(position_name)
        else:  # nothing
            pass

    def get_team_average(self, stat_name: str) -> float:
        total_players = 0
        if stat_name == 'ops':
            ops_total = 0
            for player_name in self.active_roster:
                player: Player = self.get_player_by_name(player_name)
                if player.stats.batting.games_played == 0:
                    # if a player hasn't played yet throw the average so it forces a replacement.
                    ops_total = 99999
                if player.position != 1:
                    ops_total += player.stats.batting.ops()
                    total_players += 1
            return ops_total / total_players
        elif stat_name == 'era':
            era_total = 0
            for player_name in self.active_roster:
                player: Player = self.get_player_by_name(player_name)
                if player.stats.pitching.games_pitched_in == 0:
                    era_total = 99999
                if player.position == 1:
                    era_total += player.stats.pitching.era()
                    total_players += 1
            return era_total / total_players

    def generate_random_active_roster(self) -> None:
        """
        Randomly selects players to fill each slot on the active roster from the 40-man.
        6 OF, 7 IF, 2 C, 10 P, 1 DH
        """

        # create copy of all players to pull from
        eligible_players = list(self.forty_man_roster)

        # pitchers #
        for i in range(10):
            p: Player = eligible_players.pop()
            self.active_roster['P'].append(p.full_name)
            p.position = 1  # set player to pitcher

        # catchers #
        for i in range(2):
            p: Player = eligible_players.pop()
            self.active_roster['C'].append(p.full_name)
            p.position = 2  # set player to pitcher

        # outfielders #
        for i in range(6):
            p: Player = eligible_players.pop()
            self.active_roster['OF'].append(p.full_name)
            # won't set position because we don't know where in the OF

        # infielders #
        for i in range(7):
            p: Player = eligible_players.pop()
            self.active_roster['IF'].append(p.full_name)
            # won't set position because we don't know where in the IF

        # DH #
        for i in range(1):
            p: Player = eligible_players.pop()
            self.active_roster['DH'].append(p.full_name)

    def generate_from_scratch(self) -> None:
        """
        Generates new data for a team
        """
        csvfile = pd.read_csv('sources/us-cities.csv')
        location = csvfile.sample()
        team_noun = Pluralizer().plural(RandomWord().word()).title()
        self.name = location.City.to_string(index=False) + " " + team_noun
        self.short_name = location.City.to_string(index=False)[:2].upper() + team_noun[1].upper()
        self.state = location['State short'].to_string(index=False)

        self.forty_man_roster = self.generate_forty_man_roster()
        self.active_roster = {'P': [], 'C': [], 'IF': [], 'OF': [], 'DH': []}
        self.game_lineup = {'P': '', 'C': '', '1B': '', '2B': '', '3B': '', 'SS': '', 'LF': '', 'CF': '', 'RF': '', 'DH': ''}
        self.generate_random_active_roster()
        self.update_lineup()

        self.home_stadium = Stadium([location.City.to_string(index=False), team_noun], self.state)
        self.stats = TeamStatistics()
        self.division = ''

        # management and strategy
        self.strategy = random.choice([0, 1, 2])  # 0 is 5 game trial, 1 is replace if below avg, 2 is randomize if losing

    def from_json(self, json_data) -> None:
        """
        Sets the team parameters from a JSON object.
        :param json_data: JSON object containing data from a team file.
        """
        self.name = json_data['name']
        self.short_name = json_data['short_name']
        self.state = json_data['state']
        self.forty_man_roster = self.load_forty_man_from_json(json_data['forty_man_roster'])
        self.active_roster = json.loads(json_data['active_roster'])
        self.game_lineup = json.loads(json_data['game_lineup'])
        self.home_stadium = Stadium(data=json.loads(json_data['home_stadium']))
        self.stats = TeamStatistics(json.loads(json_data['stats']))
        self.strategy = json_data['strategy']
        self.division = json_data['division']

    def to_json(self) -> str:
        """
        Converts the team object to a JSON string.
        :return: JSON string of team data.
        """
        data_object = {
            'name': self.name,
            'short_name': self.short_name,
            'state': self.state,
            'home_stadium': self.home_stadium.to_json(),
            'forty_man_roster': self.convert_forty_man_to_json(),
            'active_roster': json.dumps(self.active_roster),
            'game_lineup': json.dumps(self.game_lineup),
            'stats': self.stats.to_json(),
            'strategy': self.strategy,
            'division': self.division
        }

        return json.dumps(data_object)


def save_team_file(team: Team) -> None:
    """
    Saves team to json file in save folder.
    :param team: Team object
    """
    team_file_name = team.name.replace(" ", "_") + '.json'
    with open('../game/saves/teams/' + team_file_name, 'w') as outfile:
        json.dump(team.to_json(), outfile)


def load_team_file(team_file_name) -> Team:
    """
    Load team from file
    :param team_file_name: TEAMNAME.json
    :return: Team object.
    """
    with open('../game/saves/teams/' + team_file_name) as f:
        return Team(json_str=f.read())


def convert_position_name_to_category(position_name: str) -> str:
    if position_name in ['1B', '2B', '3B', 'SS']:
        return 'IF'
    elif position_name in ['LF', 'CF', 'RF']:
        return 'OF'
    else:
        return position_name
