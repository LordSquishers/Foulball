import json
import os

from data import stats
from data.team import Team

print(os.listdir())
all_players = stats.load_player_file()
all_teams = dict()


def load_teams():
    for team_file in os.listdir('../game/saves/teams/'):
        if team_file == '.DS_Store':
            continue
        with open('../game/saves/teams/' + team_file) as f:
            team_data = json.load(f)
            loaded_team = Team(team_data, all_players)
            all_teams[loaded_team.name] = loaded_team


load_teams()

for team in all_teams.keys():
    print(team, all_teams[team].division)

# pl = list()
# for p in all_players:
#     data = all_players[p]
#     pl.append(Player(json.loads(data)))
# all_players = pl
#
# ops = []
# era = []
# team_wins = []
#
# for team_name in all_teams:
#     team_wins.append(all_teams[team_name].stats.wins)
#     tops = list()
#     tera = list()
#     for player in all_teams[team_name].roster:
#         if player.batting.ops() > 0:
#             tops.append(player.power+player.consistency+player.confidence+player.crit_thinking_fielding+player.crit_thinking_batting+player.contact)
#         if player.pitching.era() > 0:
#             tera.append(player.throwing_power+player.pitching_control+player.pitching_stamina+player.pitching_spin+player.consistency+player.confidence)
#     ops.append(np.average(tops))
#     era.append(np.average(tera))
#
# plt.close()
# fig = plt.figure()
# plt.scatter(team_wins, ops, label='Batting')
# # plt.scatter(team_wins, era, label='Pitching')
# plt.legend()
# plt.xlabel('Wins')
# plt.ylabel('Stat')
# plt.show()
