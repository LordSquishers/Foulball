import json
import os

import numpy as np
from tabulate import tabulate
from wonderwords import RandomWord

from old.data import stats
from old.data.stats import l3
from old.data.team import Team
from old.game.game import Game

# make simulation logic
NUM_TEAMS = 20
NUM_DIVISIONS = 4
NUM_DIVISION_WINNERS = 1

DIVISION_NAMES = ['AL East', 'AL West', 'NL West', 'NL East']

if NUM_TEAMS % NUM_DIVISIONS != 0:
    print('Teams must be divisible by divisions!')
    exit(1)

if np.log2(NUM_DIVISION_WINNERS * NUM_DIVISIONS) % 1 != 0:
    print('Number of advancing postseason teams must be a power of 2! Currently ' + str(NUM_DIVISION_WINNERS * NUM_DIVISIONS) + ' teams.')
    exit(1)

# generate teams
all_teams = list()
all_players = None

if len(os.listdir('saves/teams/')) > 2:
    all_players = stats.load_player_file()
    print('Loading teams from previous save!')
    for team_file in os.listdir('saves/teams/'):
        if team_file == '.DS_Store':
            continue
        with open('saves/teams/' + team_file) as f:
            team_data = json.load(f)
            loaded_team = Team(team_data, all_players)
            all_teams.append(loaded_team)
else:
    for t in range(NUM_TEAMS):
        all_teams.append(Team())

divisions = list()
division_names = list()

for d in range(NUM_DIVISIONS):
    if len(DIVISION_NAMES) > 0 and d < len(DIVISION_NAMES):
        division_names.append(DIVISION_NAMES[d])
    else:
        division_names.append(RandomWord().word().title() + ' Division')
    div_teams = list()
    TEAMS_PER_DIV = int(NUM_TEAMS / NUM_DIVISIONS)
    if all_teams[-1].division == '' or all_teams[-1].division not in DIVISION_NAMES:
        for t in range(TEAMS_PER_DIV):
            div_teams.append(all_teams[t + (d * TEAMS_PER_DIV)])
            all_teams[t + (d * TEAMS_PER_DIV)].division = division_names[d]
    else:
        for team in all_teams:
            if team.division == division_names[d]:
                div_teams.append(team)
    divisions.append(div_teams)


def play_round_robin(team_list: list, series_length: int, print_results: bool):
    total_games = 0
    series_length = max(2, series_length)  # minimum 2.
    if series_length % 2 == 1:  # can't be odd. both limitations of the current RR algorithm.
        series_length += 1
    matches = set((x, y) for x in team_list for y in team_list if x != y)
    for away_team, home_team in matches:
        if total_games % int(len(matches) / 4) == 0:
            print_league_leaderboard(divisions, division_names)
        if total_games % int(len(matches) / 4) == 0 and total_games != 0:
            should_print = False
            real_time = False
        else:
            should_print = False
            real_time = False

        game_of_choice = int(np.random.random(1)[0] * series_length / 2)
        if game_of_choice == int(series_length / 2):
            game_of_choice -= 1
        for i in range(int(series_length / 2)):
            if i == game_of_choice:
                real_time_s = True
                should_print_s = True
            else:
                real_time_s = False
                should_print_s = False
            game = Game(away_team=away_team, home_team=home_team)
            game.play_game(should_print=(should_print and should_print_s), real_time=(real_time and real_time_s))
            total_games += 1
            if print_results and (should_print and should_print_s):
                game.print_results()
    return total_games


def play_postseason_bracket(divs: list, top_x_teams: int, best_of: int, print_game_events: bool, print_game_results: bool, print_bracket_progress: bool):
    top_teams = list()
    for div in divs:  # collect all the top teams
        for t_idx in range(top_x_teams):
            top_teams.append(div[t_idx])
    for bracket_level in range(int(np.log2(len(top_teams)))):  # for each level of the bracket 8s, quarter, semi, final, etc.
        if print_bracket_progress:
            print('Stage: Round of ' + str(len(top_teams)))
            for team in top_teams:
                print(team)
            print()
        advancing_teams = list()
        for t_idx in range(int(len(top_teams) / 2)):  # match each adjacent team
            away_team = top_teams[t_idx * 2]
            home_team = top_teams[t_idx * 2 + 1]
            wins = [0, 0]
            win_target = np.floor(best_of / 2) + 1
            while wins[0] < win_target and wins[1] < win_target:
                game = Game(away_team=away_team, home_team=home_team)
                result = game.play_game(should_print=print_game_events, real_time=True)  # this results 0 for AWAY and 1 for HOME
                wins[result] += 1
                if print_game_results:
                    game.print_results()
            if wins[0] == win_target:
                winning_team = 0
                print(str(away_team) + ' win the series against ' + str(home_team) + ' (' + str(wins[0]) + '-' + str(wins[1]) + ')')
            else:
                winning_team = 1
                print(str(home_team) + ' win the series against ' + str(away_team) + ' (' + str(wins[1]) + '-' + str(wins[0]) + ')')
            advancing_teams.append(top_teams[t_idx * 2 + winning_team])  # clever indexing!
        top_teams = list(advancing_teams)
        print()
        if len(top_teams) == 1:
            return top_teams[0]


def games_behind(team: Team, top_team: Team):
    gb = (top_team.stats.wins - team.stats.wins + team.stats.losses - top_team.stats.losses) / 2
    if gb == 0:
        return '--'
    return str(gb)


def print_division_leaderboard(division: list, division_name: str):
    division.sort(key=lambda x: x.stats.wins * 100 + x.stats.run_diff(), reverse=True)  # sort by wins
    division_board = [['Team', 'W', 'L', 'PCT', 'GB', 'RD', 'RS', 'RA']]
    for team in division:
        division_board.append([team.name, team.stats.wins, team.stats.losses, l3(team.stats.win_pct()), games_behind(team, division[0]), team.stats.run_diff(), team.stats.runs_scored, team.stats.runs_against])

    print()
    print(division_name + ':')
    print(tabulate(division_board))


def print_league_leaderboard(divs: list, div_names: list):
    for d_idx in range(len(divisions)):
        print_division_leaderboard(divs[d_idx], div_names[d_idx])


# main season #
games_played = play_round_robin(all_teams, series_length=4, print_results=True)
print(str(games_played) + ' games played this season (' + str(games_played / len(all_teams)) + ' games per team).')
print_league_leaderboard(divisions, division_names)
print()

# clear saves #
for file_name in os.listdir('saves/teams/'):
    os.remove('saves/teams/' + file_name)
if 'players.json' in os.listdir('saves/'):
    os.remove('saves/players.json')

# save team stats #
for team in all_teams:
    team.to_json()
print('Saved ' + str(len(all_teams)) + ' teams\' data to saves/ !')

# save player database
stats.save_player_file(all_teams)
print('Player data saved!')

# post season #
winner = play_postseason_bracket(divisions, top_x_teams=1, best_of=5, print_game_results=False, print_game_events=False, print_bracket_progress=True)
print('World Series winner: ' + str(winner))