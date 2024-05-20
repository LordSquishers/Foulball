from enum import Enum

from data.team import Team, get_position_by_number, get_position_by_name
from data.text_formatting import l1, l2, l3, convert_inning_id_to_string
from tabulate import tabulate

from simulation.game_simulation import Game, TeamSide


class OutputType(Enum):
    CONSOLE = 1
    DISCORD_BOT = 2


OUTPUT_TYPE = OutputType.CONSOLE


def display_game_results(game: Game) -> None:
    if OUTPUT_TYPE == OutputType.CONSOLE:
        print_game_results(game)
    elif OUTPUT_TYPE == OutputType.DISCORD_BOT:
        pass  # TODO- TO BE IMPLEMENTED


def display_text(output: any) -> None:
    if OUTPUT_TYPE == OutputType.CONSOLE:
        print(output)
    elif OUTPUT_TYPE == OutputType.DISCORD_BOT:
        pass  # TODO- TO BE IMPLEMENTED


def display_lineup(team: Team) -> None:
    if OUTPUT_TYPE == OutputType.CONSOLE:
        print_lineup(team)
    elif OUTPUT_TYPE == OutputType.DISCORD_BOT:
        pass  # TODO- TO BE IMPLEMENTED


def display_full_roster(team: Team) -> None:
    if OUTPUT_TYPE == OutputType.CONSOLE:
        print_full_roster_stats(team)
    elif OUTPUT_TYPE == OutputType.DISCORD_BOT:
        pass  # TODO- TO BE IMPLEMENTED


def print_lineup(team: Team) -> None:
    """
    Prints the simulation lineup (formatted) to the console.
    """
    print("The " + team.name + " (" + team.state + ")")
    for player in team.game_lineup.values():
        player = team.get_player_by_name(player)
        print(get_position_by_number(player.position) + ": #" + str(player.jersey_number) + " " + player.full_name)


def print_full_roster_stats(team: Team) -> None:
    """
    Prints the full forty-man roster as a formatted console output.
    """
    print(team.__repr__() + ' Stats')
    pitching_headers = ['#', 'Pitcher', 'Games', 'IP', 'ERA', 'HRs', 'K/BB', 'WHIP', 'Pitches/Game']
    pitching_stats = list()
    pitching_stats.append(pitching_headers)
    for pitcher in team.forty_man_roster:
        if pitcher.position != get_position_by_name('P') or pitcher.position == 0:
            continue
        p_stats = pitcher.stats.pitching
        pitching_stats.append(
            [pitcher.jersey_number, pitcher.full_name, p_stats.games_pitched_in, p_stats.innings_pitched, l2(p_stats.era()), p_stats.home_runs_allowed,
             p_stats.k_bb_str(), l2(p_stats.whip()), int(p_stats.pitches_per_game())])
    print(tabulate(pitching_stats))
    print()
    player_headers = ['#', 'Pos.', 'Player', '.AVG', 'HR', 'RBIs', 'OPS', '1B', 'xBH', 'BBs', 'SOs', 'PAs', 'Avg. EV', 'Games', 'Errors']
    player_table = list()
    player_table.append(player_headers)
    for player in team.forty_man_roster:
        if player.position == get_position_by_name('P') or player.position == 0:
            continue
        ps = player.stats.batting
        fs = player.stats.fielding
        player_table.append(
            [player.jersey_number, get_position_by_number(player.position), player.full_name, l3(ps.b_avg()), ps.home_runs, ps.runs_batted_in, l3(ps.ops()),
             ps.singles, ps.xbh(), ps.walks, ps.strikeouts, ps.plate_appearances, l1(ps.avg_ev()), ps.games_played, fs.errors])
    print(tabulate(player_table))


def print_game_results(game: Game):
    # Top row #
    inning_header = list(range(1, len(game.inning_runs[0]) + 1))
    inning_header.insert(0, "Team")
    inning_header.extend(['R', 'H', 'E'])

    # Scoring data #
    if len(game.inning_runs[TeamSide.AWAY_TEAM]) > len(game.inning_runs[TeamSide.HOME_TEAM]):
        game.inning_runs[TeamSide.HOME_TEAM].append('-')
    game.inning_runs[TeamSide.AWAY_TEAM].extend([game.game_runs[TeamSide.AWAY_TEAM], game.game_hits[TeamSide.AWAY_TEAM], game.game_errors[TeamSide.AWAY_TEAM]])
    game.inning_runs[TeamSide.HOME_TEAM].extend([game.game_runs[TeamSide.HOME_TEAM], game.game_hits[TeamSide.HOME_TEAM], game.game_errors[TeamSide.HOME_TEAM]])

    # add team names #
    game.inning_runs[TeamSide.AWAY_TEAM].insert(0, game.away_team.name)
    game.inning_runs[TeamSide.HOME_TEAM].insert(0, game.home_team.name)

    # make table and print #
    table = [inning_header, game.inning_runs[TeamSide.AWAY_TEAM], game.inning_runs[TeamSide.HOME_TEAM]]
    print()
    print(tabulate(table))
    print('Game played at ' + game.stadium.name + ", " + game.stadium.state + " (" + str(int(game.stadium.field_distances[0])) + "/" + str(int(game.stadium.field_distances[1])) + "/" + str(int(game.stadium.field_distances[2])) + "ft)")
    print('Away pitches: ' + str(game.pitch_totals[TeamSide.AWAY_TEAM]) + ' Home pitches: ' + str(game.pitch_totals[TeamSide.HOME_TEAM]))
    print()
    print('Home runs:')
    for batter, dist, direction, ev, la, inning in game.home_runs:
        print(str(batter) + " in " + convert_inning_id_to_string(inning) + ". Distance: " + str(int(dist)) + " ft, EV: " + str(round(ev, 1)) + " mph, LA: " + str(round(la, 1)) + " deg, Field Direction: " + str(round(direction, 1)) + " deg")

