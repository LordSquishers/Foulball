import datetime
import random
import asyncio
from datetime import datetime as dt

from pytz import timezone
import os
import us

import discord
from discord.ext import commands, tasks
from tabulate import tabulate
from wonderwords import RandomWord

from old.data import stats
from old.data.player import Player
from old.data.stats import *
from old.data.team import Team, get_position_by_number, get_position_by_name
from old.game.game import Game

est = timezone('US/Eastern')

with open('token.txt') as f:
    token = f.readline()

TEAM_CHANNEL_DICT = {
    'arthurtops': 0,
    'birdsboroshortwaves': 0,
    'brooknealcrosscontaminations': 0,
    'brownsdaleleopards': 0,
    'carriepremiers': 0,
    'creweroughs': 0,
    'eastrochesterprefaces': 0,
    'hidalgodrivings': 0,
    'holtrates': 0,
    'kenodeeps': 0,
    'laporteperps': 0,
    'lyndonvilleswankies': 0,
    'osakisboatloads': 0,
    'pawleysislandsalmon': 0,
    'redfordstags': 0,
    'rockyhilltesties': 0,
    'spraggsquestionnaires': 0,
    'unionvillecentervicinities': 0,
    'wakemanburlesques': 0,
    'waskishbeings': 0
}

DIVISION_NAMES = ['AL East', 'AL West', 'NL West', 'NL East']
NUM_TEAMS = 20
NUM_DIVISIONS = 4
NUM_DIVISION_WINNERS = 1

divisions = list()
division_names = list()

games_list = list()
current_day = -1
games_for_day = [None, None, [], [], [], [], [], []]  # according to RUN_TIMES

RUN_TIMES = [
    datetime.time(hour=0, minute=0, tzinfo=est),
    datetime.time(hour=9, minute=0, tzinfo=est),
    datetime.time(hour=13, minute=2, tzinfo=est),
    datetime.time(hour=19, minute=5, tzinfo=est),
    datetime.time(hour=14, minute=5, tzinfo=est),
    datetime.time(hour=20, minute=5, tzinfo=est),
    datetime.time(hour=16, minute=5, tzinfo=est),
    datetime.time(hour=22, minute=5, tzinfo=est)
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', description='Foul Ball!', intents=intents)

LEAGUE_UPDATES_CHANNEL_ID = 1172465274394513508  # foulball/general/league-news
GAME_DISPLAY_CATEGORY_ID = 1171787231896293407  # foulball/live_games

player_data = {}
team_data = {}


@tasks.loop(time=RUN_TIMES)
async def game_runs():
    current_hour = dt.now(est).hour
    if current_hour == 0:  # scheduling games
        if current_day + 1 == len(games_list): # we've hit the post season!
            await post_season_handling()
        schedule_games()
    elif current_hour == 9:  # 9am EST, print league standings
        updates_chnl = bot.get_channel(LEAGUE_UPDATES_CHANNEL_ID)
        await send_morning_update(updates_chnl)
    elif current_hour == 13:  # 1pm EST
        await display_games(games_for_day[2])
    elif current_hour == 14:  # 1pm CST
        await display_games(games_for_day[3])
    elif current_hour == 15:  # 1pm PST
        await display_games(games_for_day[4])
    elif current_hour == 19:  # 7pm EST
        await display_games(games_for_day[5])
    elif current_hour == 20:  # 7pm CST
        await display_games(games_for_day[6])
    elif current_hour == 22:  # 7pm PST
        await display_games(games_for_day[7])


async def post_season_handling():
    luc = bot.get_channel(LEAGUE_UPDATES_CHANNEL_ID)
    await luc.send('**The season is over!!!** Thanks to all teams for playing.')
    await send_league_leaderboard(luc)
    await luc.send('A special post-season event will happen in the next few weeks. Keep an eye out for an announcement!')
    save_season()


def save_season():
    # clear saves #
    for file_name in os.listdir('../game/saves/teams/'):
        os.remove('../game/saves/teams/' + file_name)
    if 'players.json' in os.listdir('../game/saves/'):
        os.remove('../game/saves/players.json')
    # save team stats #
    for team in list(team_data.values()):
        team.to_json()
    print('Saved ' + str(len(list(team_data.values()))) + ' teams\' data to saves/ !')

    # save player database
    stats.save_player_file(list(team_data.values()))
    print('Player data saved!')


def schedule_games():
    global current_day, games_for_day
    games_for_day = [None, None, [], [], [], [], [], []]
    games_on_this_day = games_list[current_day]
    current_day += 1

    for game in games_on_this_day:
        tz_difference = 19-dt.now(timezone(us.states.lookup(game.stadium.state).capital_tz)).utcoffset().seconds/3600
        if tz_difference == 0:
            gameday_idx = random.choice([2, 5])
        elif tz_difference == 1:
            gameday_idx = random.choice([3, 6])
        elif tz_difference == 2:
            gameday_idx = random.choice([3, 6])
        elif tz_difference == 3:
            gameday_idx = random.choice([4, 7])
        else:
            gameday_idx = 2
        games_for_day[gameday_idx].append(game)


async def send_morning_update(updates_chnl):
    await updates_chnl.purge(limit=100, check=is_me)
    await updates_chnl.send('Good morning! It is {:%A, %B %-d} and these are the current league standings.'.format(dt.now(est)))
    await updates_chnl.send(
        'It is currently day ' + str(current_day + 1) + ' of the season. The season ends in ' + str(len(games_list) - current_day) + ' days.')
    await send_league_leaderboard(updates_chnl)


async def display_games(list_of_games: list):
    live_games_cat = bot.get_channel(GAME_DISPLAY_CATEGORY_ID)
    game_tasks = list()

    for game in list_of_games:
        # create channel per game
        # ideally print games simultaneously
        game_name = game.away_team.short_name + '-' + game.home_team.short_name
        game_chnl = await live_games_cat.create_text_channel(game_name)
        team_chnls = [TEAM_CHANNEL_DICT[game.away_team.name.lower().replace(' ', '').replace('-', '')], TEAM_CHANNEL_DICT[game.home_team.name.lower().replace(' ', '').replace('-', '')]]
        print('creating game ' + game_name)
        game_tasks.append(asyncio.create_task(game.play_game_discord(game_chnl, team_chnls)))
    for task in game_tasks:
        await task


async def send_league_leaderboard(chnl):
    for d_idx in range(len(divisions)):
        division = divisions[d_idx]
        division_name = division_names[d_idx]
        division.sort(key=lambda x: x.stats.wins * 100 + x.stats.run_diff(), reverse=True)  # sort by wins
        division_board = [['Team', 'W', 'L', 'PCT', 'GB', 'RD', 'RS', 'RA']]
        for team in division:
            division_board.append(
                [team.name, team.stats.wins, team.stats.losses, l3(team.stats.win_pct()), games_behind(team, division[0]), team.stats.run_diff(),
                 team.stats.runs_scored, team.stats.runs_against])

        await chnl.send('```\n' + division_name + ':\n' + tabulate(division_board) + '```')


def games_behind(team: Team, top_team: Team):
    gb = (top_team.stats.wins - team.stats.wins + team.stats.losses - top_team.stats.losses) / 2
    if gb == 0:
        return '--'
    return str(gb)


async def generate_divisions():
    for d in range(NUM_DIVISIONS):
        if len(DIVISION_NAMES) > 0 and d < len(DIVISION_NAMES):
            division_names.append(DIVISION_NAMES[d])
        else:
            division_names.append(RandomWord().word().title() + ' Division')
        div_teams = list()
        TEAMS_PER_DIV = int(NUM_TEAMS / NUM_DIVISIONS)
        team_data_list = list(team_data.values())
        if team_data_list[-1].division == '' or team_data_list[-1].division not in DIVISION_NAMES:
            for t in range(TEAMS_PER_DIV):
                div_teams.append(team_data_list[t + (d * TEAMS_PER_DIV)])
                team_data_list[t + (d * TEAMS_PER_DIV)].division = division_names[d]
        else:
            for team in team_data_list:
                if team.division == division_names[d]:
                    div_teams.append(team)
        divisions.append(div_teams)


async def generate_games(teams: dict):
    team_list = teams.values()
    game_list = list()
    for series in range(int(4 / 2)):  # series length
        matches = list((x, y) for x in team_list for y in team_list if x != y)
        total_matches = 0

        current_day_games = list()
        current_day_teams = list()
        while len(matches) > 0:
            acceptable_choice = False
            total_runs = 0
            while not acceptable_choice:
                away_team, home_team = random.choice(matches)
                total_runs += 1
                if (away_team.name not in current_day_teams and home_team.name not in current_day_teams) or total_runs > 1000:
                    acceptable_choice = True

            current_day_teams.append(away_team.name)
            current_day_teams.append(home_team.name)

            matches.remove((away_team, home_team))
            current_day_games.append(Game(away_team=away_team, home_team=home_team))

            total_matches += 1
            if total_matches % 10 == 0:
                game_list.append(current_day_games.copy())
                current_day_games.clear()
                current_day_teams.clear()

    return game_list


async def send_full_roster_stats(team, channel):
    await channel.send('Division: ' + team.division)
    await channel.send(team.__repr__() + ' Stats:')
    pitching_headers = ['#', 'Pitcher', 'Games', 'IP', 'ERA', 'HRs', 'K/BB', 'WHIP', 'Pitches/Game']
    pitching_stats = list()
    pitching_stats.append(pitching_headers)
    for pitcher in team.forty_man_roster:
        if pitcher.position != get_position_by_name('P') or pitcher.position == 0:
            continue
        p_stats = pitcher.pitching
        pitching_stats.append(
            [pitcher.jersey_number, pitcher.full_name, p_stats.games_pitched_in, p_stats.innings_pitched, l2(p_stats.era()), p_stats.home_runs_allowed,
             p_stats.k_bb_str(), l2(p_stats.whip()), int(p_stats.pitches_per_game())])
    await channel.send('```' + tabulate(pitching_stats) + '```')
    player_headers = ['#', 'Pos', 'Player', 'AVG', 'HR', 'RBI', 'OPS', '1B', 'xBH', 'BB/SO', 'PA', 'EV']
    player_table = list()
    player_table.append(player_headers)
    for pname in team.lineup:
        player = team.get_player_by_name(pname)
        if player.position == get_position_by_name('P') or player.position == 0:
            continue
        ps = player.batting
        fs = player.fielding
        player_table.append(
            [player.jersey_number, get_position_by_number(player.position), player.full_name, l3(ps.b_avg()), ps.home_runs, ps.runs_batted_in, l3(ps.ops()),
             ps.singles, ps.xbh(), str(ps.walks) + '/' + str(ps.strikeouts), ps.plate_appearances, l1(ps.avg_ev())])
    await channel.send('```' + tabulate(player_table) + '```')


async def send_lineup(team_name, ctx):
    headers = [['Position', '#', 'Player']]

    team = team_data[team_name]
    await ctx.send("**The " + team.name + " (" + team.state + ")**")
    for i in range(10):
        player = team.get_player_by_name(team.lineup[i])
        headers.append([get_position_by_number(player.position), str(player.jersey_number), player.full_name])
    await ctx.send('```' + tabulate(headers) + '```')


async def send_active_roster(team_name, ctx):
    headers = [['Position', '#', 'Player']]

    team = team_data[team_name]
    await ctx.send("**The " + team.name + " (" + team.state + ")**")
    for i in range(len(team.active_roster)):
        player = team.get_player_by_name(team.active_roster[i])
        headers.append([get_position_by_number(player.position), str(player.jersey_number), player.full_name])
    await ctx.send('```' + tabulate(headers) + '```')


def is_me(m):
    return m.author == bot.user


def set_data(pd, td):
    global player_data, team_data
    player_data = pd
    team_data = td


@bot.command()
async def sync(ctx: commands.Context, guild: discord.Guild):
    await bot.tree.sync(guild=guild)


@bot.event
async def on_ready():
    global games_list
    print(f'Logged in as {bot.user}!')

    all_players = stats.load_player_file()
    all_teams = {}
    print('Loading teams from previous save!')
    for team_file in os.listdir('../game/saves/teams/'):
        if team_file == '.DS_Store':
            continue
        with open('../game/saves/teams/' + team_file) as f:
            td = json.load(f)
            loaded_team = Team(td, all_players)
            all_teams[loaded_team.name.lower().replace(' ', '').replace('-', '')] = loaded_team
            print(f'Loaded {loaded_team.name} from files.')

    set_data(all_players, all_teams)
    game_runs.start()

    await generate_divisions()
    games_list = await generate_games(all_teams)

    for chnl in bot.get_all_channels():
        if chnl.category is not None and chnl.category.name.lower() == 'live games':
            await chnl.delete()
        if chnl.category is not None and chnl.category.name in DIVISION_NAMES:
            team_name = chnl.name.replace('-', '')
            if team_name in all_teams.keys():
                TEAM_CHANNEL_DICT[team_name] = chnl.id

    schedule_games()
    await bot.get_channel(1171786560568565814).send('Foulball initialized. Play ball!')
    await send_morning_update(bot.get_channel(LEAGUE_UPDATES_CHANNEL_ID))

    # for chnl in bot.get_all_channels():
    #     if chnl.category is not None and chnl.category.name in DIVISION_NAMES:
    #         team_name = chnl.name.replace('-', '')
    #         await chnl.purge(limit=100, check=is_me)
    #         if team_name in all_teams.keys():
    #             team = all_teams[team_name]
    #             await chnl.send(team.name + " (" + team.state + ") -- Home Stadium: " + team.home_stadium.name)
    #             await send_full_roster_stats(team, chnl)
    #             print(f'Displayed full roster for {team.name}.')


@bot.event
async def on_disconnect():
    save_season()


@bot.command(pass_context=True, description='Displays lineup of chosen team.')
async def lineup(ctx, *team_words: str):
    team_name = ''
    for wrd in team_words:
        team_name += wrd
    clean_team_name = team_name.lower().replace('-', '')
    if clean_team_name in team_data.keys():
        await send_lineup(clean_team_name, ctx)
    else:
        await ctx.send('Could not find the team you are looking for.')


@bot.command(name='activeroster', description='Displays active roster of chosen team.')
async def active_roster(ctx, *team_words: str):
    team_name = ''
    for wrd in team_words:
        team_name += wrd
    clean_team_name = team_name.lower().replace('-', '')
    if clean_team_name in team_data.keys():
        await send_active_roster(clean_team_name, ctx)
    else:
        await ctx.send('Could not find the team you are looking for.')


@bot.command(name='player', description='Displays detailed player stats.', )
async def show_player_stats(ctx, *player_words: str):
    if len(player_words) == 2:
        player_name = player_words[0].title() + ' ' + player_words[1].title()
        player = Player(data=json.loads(player_data[player_name]))
        team_key = player.team.lower().replace('-', '').replace(' ', '')
        player = team_data[team_key].get_player_by_name(player_name)

        desc = player.full_name + ' (#' + str(player.jersey_number) + ', ' + player.team + ')' + '\n' + player.gender.title() + ', ' + str(player.age) + '. ' + str(int(player.height_inches / 12)) + '\'' + str(player.height_inches % 12) + '\", ' + str(player.weight_lbs) + ' lbs.' + '\n' + 'From: ' + player.nationality.title() + '\n\n' + 'Current plays: ' + get_position_by_number(player.position)

        table_out = ''
        if player.position == get_position_by_name('P'):
            ps = player.pitching
            table = [['ERA', 'HR', 'K/BB', 'WHIP', '|', 'SH', 'HBP'],
                     [l2(ps.era()), ps.home_runs_allowed, ps.k_bb_str(), l2(ps.whip()), '|', ps.shutouts, ps.hit_by_pitches],
                     ['1B', 'xBH', 'LOB', 'BF', '|', 'G', 'IP'],
                     [ps.singles_allowed, ps.extra_base_hits_allowed, ps.left_on_base, ps.batters_faced, '|', ps.games_pitched_in, ps.innings_pitched]]
            table_out = tabulate(table)
        else:
            bs = player.batting
            table = [['AVG', 'OPS', 'HR', 'RBI', '|', '1B', '2B', '3B', '|', 'BB', 'SO'],
                     [l3(bs.b_avg()), l3(bs.ops()), bs.home_runs, bs.runs_batted_in, '|', bs.singles, bs.doubles, bs.triples, '|', bs.walks, bs.strikeouts],
                     ['Avg. EV', 'LO', 'FO', 'PO', '|', 'PA', 'G', 'Runs', '|', 'Errs', ' '],
                     [l1(bs.avg_ev()), bs.out_lineout, bs.out_flyout, bs.out_popout, '|', bs.plate_appearances, bs.games_played, bs.runs, '|', player.fielding.errors]]
            table_out = tabulate(table)
        await ctx.send('```' + desc + '\n' + table_out + '```')
    else:
        await ctx.send('Please use the full name of the player (case-insensitive).')


@bot.command(name='commands', description='Lists all commands.')
async def list_commands(ctx):
    await ctx.send('List of commands: lineup, player, activeroster, leagueboard, schedule, commands')


@bot.command(name='leagueboard', description='Displays league leaderboard.')
async def league_leaderboard(ctx):
    await send_league_leaderboard(ctx)


@bot.command(name='schedule', description='Shows the game schedule for the next week.')
async def show_schedule(ctx):
    idx = 0
    for games in games_for_day:
        if idx == 2:
            if len(games) == 0:
                continue
            await ctx.send('Games at 1PM EST:\n```'+tabulate([games], tablefmt="plain")+'```')
        elif idx == 3:
            if len(games) == 0:
                continue
            await ctx.send('Games at 2PM EST:\n```'+tabulate([games],tablefmt="plain")+'```')
        elif idx == 4:
            if len(games) == 0:
                continue
            await ctx.send('Games at 4PM EST:\n```'+tabulate([games],tablefmt="plain")+'```')
        elif idx == 5:
            if len(games) == 0:
                continue
            await ctx.send('Games at 7PM EST:\n```'+tabulate([games],tablefmt="plain")+'```')
        elif idx == 6:
            if len(games) == 0:
                continue
            await ctx.send('Games at 8PM EST:\n```'+tabulate([games],tablefmt="plain")+'```')
        elif idx == 7:
            if len(games) == 0:
                continue
            await ctx.send('Games at 10PM EST:\n```'+tabulate([games],"plain")+'```')
        idx += 1


@bot.command(name='rename', description='Superficially renames a player.')
async def rename_player(ctx, *player_words: str):
    player_to_replace = player_words[0].title() + ' ' + player_words[1].title()
    player_replacing_with = player_words[2].title() + ' ' + player_words[3].title()


@bot.command(name='playgames', description='Just play some random games.')
async def just_play_a_game(ctx):
    await display_games(games_for_day[2])

bot.run(token)
# TODO: make games automatic and new channels accordingly, all real time, scheduled on date and time.
