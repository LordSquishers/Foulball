import random
import time
from enum import Enum, IntEnum

import numpy as np
from tabulate import tabulate

from old.data.player import Player
from old.data.stadium import Stadium
from old.data.stats import l2, l3

HOME_TEAM = 1
AWAY_TEAM = 0

FIRST_BASE = 0
SECOND_BASE = 1
THIRD_BASE = 2

PITCHER = 1
CATCHER = 2
FIRST_BASEMAN = 3
SECOND_BASEMAN = 4
SHORTSTOP = 5
THIRD_BASEMAN = 6
LEFT_FIELDER = 7
CENTER_FIELDER = 8
RIGHT_FIELDER = 9
DH = 10

MPH_TO_MPS = 0.44704
METERS_TO_FEET = 3.28
GRAVITY = 9.8106
DRAG_CONSTANT_K = 0.0002855973575
BATTING_DIST_ADJUSTMENT = 1.25

# won't always be static if there are shifts but there are no shifts yet
# DIST_FEET, ANGLE_DEG_FROM_LEFT
FIELDER_POSITIONS = [(60.5, 45), (0, 0), (100, 78.75), (130, 56.25), (130, 33.75), (100, 11.25), (270, 16.5), (320, 45), (270, 82.5)]
FORCEOUT_THRESHOLD = [0.9, 0.8, 1, 1, 0.8, 1, 0.8, 1, 1, 0.75, 1, 1]  # 1 is impossible, 0 is easiest
OUTCOME_NAME = ['OUTFIELD SINGLE', 'OUTFIELD DOUBLE', 'OUTFIELD TRIPLE', 'HOMERUN', 'FLYOUT', 'POPOUT', 'LINEOUT', '-', '-', 'INFIELD SINGLE', '-', '-']


def convert_half_to_full_inning(half_inning):
    # 0 is top 1st, 17 is bottom 9th.
    half = "Top"
    if half_inning % 2 == 1:
        half = "Bottom"
    inning = int(half_inning / 2) + 1
    return half + " " + str(inning)


class BattingOutcome(Enum):
    BATTER_CONTACT = 1,
    HIT_BY_PITCH = 2,
    STRIKEOUT_SWINGING = 3,
    STRIKEOUT_LOOKING = 4,
    WALK = 5


class BattedBallOutcome(IntEnum):
    OUTFIELDSINGLE = 1,
    OUTFIELDDOUBLE = 2,
    OUTFIELDTRIPLE = 3,
    HOMERUN = 4,
    FLYOUT = 5,
    POPOUT = 6,
    LINEOUT = 7,
    DOUBLEPLAY1B2B = 8,
    DOUBLEPLAY2B3B = 11,
    DOUBLEPLAY3BHP = 12,
    TRIPLEPLAY = 9,
    INFIELDSINGLE = 10


def pitch_bat_matchup(pitcher: Player, batter: Player, real_time: bool):
    balls = 0
    strikes = 0
    pitches = 0
    while True:
        if real_time:
            time.sleep(5)
            opt = random.choice([0, 1, 2, 3])
            if opt == 1:
                print('Pitcher deals...')
            elif opt == 2:
                print('And the pitch...')
            elif opt == 3:
                print('Pitcher throws...')
            time.sleep(3)
        # outcomes: hit, bb, soL, soS, hbp
        # must find ball difficulty
        target_pitch_difficulty = pitcher.throwing_power * pitcher.pitching_control * pitcher.pitching_spin  # how difficult the pitchers "best" pitch is
        random_target_blend = pitcher.pitching_control * pitcher.pitching_stamina * pitcher.confidence  # blend between random and best
        pitch_difficulty = np.interp(random_target_blend, [0, 1], [np.random.random(), target_pitch_difficulty])
        ball_difficulty = (1 - pitcher.consistency) * np.random.random() + pitcher.consistency * pitch_difficulty  # if not consistent, then its just random

        # how will the batter fare?
        batter_skill = batter.crit_thinking_batting * batter.contact
        random_skill_blend = batter.confidence
        batter_ability = np.interp(random_skill_blend, [0, 1], [np.random.random(), batter_skill])
        swing_skill = (1 - batter.consistency) * np.random.random() + batter.consistency * batter_ability

        mean = (swing_skill - ball_difficulty) / 2 + 0.25
        std = (1.0 - abs(swing_skill - ball_difficulty)) / 3.0 / 1.5  # <- changes hit difficulty

        is_ball_hit = np.random.normal(mean, std, 1)[0] > 0.5
        is_ball_outside = (ball_difficulty < 0.4 and batter.crit_thinking_batting > 0.5) or (ball_difficulty < 0.75 < batter.crit_thinking_batting) or ball_difficulty < 0.25
        is_ball_hbp = ball_difficulty < 0.01

        pitches += 1

        if is_ball_hit and not is_ball_hbp:
            if real_time:
                print(batter.full_name + ' makes contact!')
            return BattingOutcome.BATTER_CONTACT, pitches, swing_skill - ball_difficulty
        if is_ball_hbp:
            if real_time:
                print(batter.full_name + ' is hit by the pitch.')
            return BattingOutcome.HIT_BY_PITCH, pitches, 0
        if not is_ball_hit and not is_ball_outside:
            strikes += 1
            pitcher.pitching.strikes += 1
            if real_time:
                print('Strike! Count is now ' + str(balls) + '-' + str(strikes) + '.')
        if not is_ball_hit and is_ball_outside:
            balls += 1
            pitcher.pitching.balls += 1
            if real_time:
                print('Ball! Count is now ' + str(balls) + '-' + str(strikes) + '.')
        if strikes > 2:
            if real_time:
                print(batter.full_name + ' strikes out swinging!')
            return BattingOutcome.STRIKEOUT_SWINGING, pitches, 0
        if balls > 3:
            if real_time:
                print(batter.full_name + ' takes a walk.')
            return BattingOutcome.WALK, pitches, 0


async def pitch_bat_matchup_discord(pitcher: Player, batter: Player, c):
    balls = 0
    strikes = 0
    pitches = 0
    while True:
        time.sleep(5)
        opt = random.choice([0, 1, 2, 3])
        if opt == 1:
            await c.send('*Pitcher deals...*')
        elif opt == 2:
            await c.send('*And the pitch...*')
        elif opt == 3:
            await c.send('*Pitcher throws...*')
        time.sleep(3)
        # outcomes: hit, bb, soL, soS, hbp
        # must find ball difficulty
        target_pitch_difficulty = pitcher.throwing_power * pitcher.pitching_control * pitcher.pitching_spin  # how difficult the pitchers "best" pitch is
        random_target_blend = pitcher.pitching_control * pitcher.pitching_stamina * pitcher.confidence  # blend between random and best
        pitch_difficulty = np.interp(random_target_blend, [0, 1], [np.random.random(), target_pitch_difficulty])
        ball_difficulty = (1 - pitcher.consistency) * np.random.random() + pitcher.consistency * pitch_difficulty  # if not consistent, then its just random

        # how will the batter fare?
        batter_skill = batter.crit_thinking_batting * batter.contact
        random_skill_blend = batter.confidence
        batter_ability = np.interp(random_skill_blend, [0, 1], [np.random.random(), batter_skill])
        swing_skill = (1 - batter.consistency) * np.random.random() + batter.consistency * batter_ability

        mean = (swing_skill - ball_difficulty) / 2 + 0.25
        std = (1.0 - abs(swing_skill - ball_difficulty)) / 3.0 / 1.5  # <- changes hit difficulty

        is_ball_hit = np.random.normal(mean, std, 1)[0] > 0.5
        is_ball_outside = (ball_difficulty < 0.4 and batter.crit_thinking_batting > 0.5) or (ball_difficulty < 0.75 < batter.crit_thinking_batting) or ball_difficulty < 0.25
        is_ball_hbp = ball_difficulty < 0.01

        pitches += 1

        if is_ball_hit and not is_ball_hbp:
            await c.send(batter.full_name + ' makes contact!')
            return BattingOutcome.BATTER_CONTACT, pitches, swing_skill - ball_difficulty
        if is_ball_hbp:
            await c.send(batter.full_name + ' is hit by the pitch.')
            return BattingOutcome.HIT_BY_PITCH, pitches, 0
        if not is_ball_hit and not is_ball_outside:
            strikes += 1
            pitcher.pitching.strikes += 1
            await c.send('*Strike! Count is now ' + str(balls) + '-' + str(strikes) + '.*')
        if not is_ball_hit and is_ball_outside:
            balls += 1
            pitcher.pitching.balls += 1
            await c.send('*Ball! Count is now ' + str(balls) + '-' + str(strikes) + '.*')
        if strikes > 2:
            await c.send(batter.full_name + ' strikes out swinging!')
            return BattingOutcome.STRIKEOUT_SWINGING, pitches, 0
        if balls > 3:
            await c.send(batter.full_name + ' takes a walk.')
            return BattingOutcome.WALK, pitches, 0


def calculate_hit(pitcher: Player, current_batter: Player, contact_strength):
    # 0=level, 90= straight up, -90=straight down
    # cs- 1 = pitcher dominant, 0.5 = equal, 0 = batter dominant
    la_mag = (90 - 180 * ((1 - contact_strength) / 2))
    la_vert = np.sign(np.random.normal(contact_strength, 0.333, 1)[0])
    launch_angle = la_vert * la_mag

    ev_mean = ((pitcher.throwing_power * current_batter.power) + contact_strength) * 30 + 80
    ev_std = (1 - contact_strength) * 3
    exit_velocity = np.random.normal(ev_mean, ev_std, 1)[0]  # mph

    direction = 0  # 0=leftpole, 90=rightpole
    if current_batter.handedness == 'left':
        direction = min(max(0, np.random.normal(33, 15, 1)[0]), 90)
    if current_batter.handedness == 'right':
        direction = min(max(0, np.random.normal(66, 15, 1)[0]), 90)
    if current_batter.handedness == 'switch':
        direction = min(max(0, np.random.normal(45, 15, 1)[0]), 90)
    # power and throwing power dictate LA and EV, handedness dictates direction
    return launch_angle, exit_velocity, direction


def calculate_impact_point(launch_angle, exit_velocity, batting_height):
    LA_rad = np.deg2rad(launch_angle)
    EV_mps = exit_velocity * MPH_TO_MPS
    EV_y = EV_mps * np.sin(LA_rad)
    EV_x = EV_mps * np.cos(LA_rad)
    h_0 = batting_height * 0.0254

    time_in_air_sqrd = (EV_y + np.sqrt(EV_y ** 2 + 2 * h_0 * GRAVITY)) / GRAVITY
    impact_distance = EV_x * np.sqrt(time_in_air_sqrd) - 0.5 * DRAG_CONSTANT_K ** 2 * EV_mps ** 4 * time_in_air_sqrd
    return impact_distance * METERS_TO_FEET * BATTING_DIST_ADJUSTMENT, np.sqrt(time_in_air_sqrd)


def get_polar_distance(r1, r2, theta1, theta2):
    return np.sqrt(r1 ** 2 + r2 ** 2 - 2 * r1 * r2 * np.cos(np.deg2rad(theta1 - theta2)))


def get_stadium_wall_distance(direction, stadium: Stadium):
    return np.interp(direction, [0, 45, 90], stadium.field_distances)


def count_runners(runners_on_base):
    total = 0
    for runner in runners_on_base:
        if runner is not None:
            total += 1
    return total


home_runs = list()


class Game:
    def __init__(self, away_team, home_team):
        # scoring attributes #
        self.game_runs = [0, 0]
        self.game_hits = [0, 0]
        self.game_errors = [0, 0]
        self.inning_runs = [list(), list()]
        self.pitch_totals = [0, 0]

        # player attributes #
        self.batter_on_plate = [0, 0]

        # current game attributes #
        self.away_team: Team = away_team
        self.home_team: Team = home_team
        self.fielding_team = self.home_team
        self.batting_team = self.away_team

        self.away_team.create_game_roster()
        self.home_team.create_game_roster()

        self.half_inning = 0
        self.should_continue_playing = True

        self.stadium = home_team.home_stadium

    def __repr__(self):
        return self.away_team.short_name + ' @ ' + self.home_team.short_name

    def calculate_fielding_outcome(self, distance_of_ball, direction, time_in_air, fielding_team, stadium: Stadium):
        if distance_of_ball > get_stadium_wall_distance(direction, stadium):
            return BattedBallOutcome.HOMERUN, 0, None
        if distance_of_ball > 160:  # feet! outfield
            closest_fielder = None
            if direction < 33:  # LF
                closest_fielder = LEFT_FIELDER
            elif 33 <= direction <= 66:  # CF
                closest_fielder = CENTER_FIELDER
            else:  # RF
                closest_fielder = RIGHT_FIELDER
            fielder: Player = fielding_team.get_player_at_position(closest_fielder)
            catch_probability, fielder_distance = self.get_catch_probability(distance_of_ball, direction, closest_fielder, fielding_team, True)
            if np.sign(catch_probability) <= 0:
                return BattedBallOutcome.FLYOUT, fielder.throwing_power * fielder.crit_thinking_fielding, closest_fielder
            else:  # they did not catch it.
                if fielder_distance > 100:
                    return BattedBallOutcome.OUTFIELDTRIPLE, fielder.throwing_power * fielder.crit_thinking_fielding, closest_fielder
                elif 100 >= fielder_distance >= 25:
                    return BattedBallOutcome.OUTFIELDDOUBLE, fielder.throwing_power * fielder.crit_thinking_fielding, closest_fielder
                elif fielder_distance < 25:
                    return BattedBallOutcome.OUTFIELDSINGLE, fielder.throwing_power * fielder.crit_thinking_fielding, closest_fielder
        elif 160 > distance_of_ball > 50:  # infield
            catch_chance = np.interp(time_in_air, [2, 3, 4, 6], [0, 0.5, 0.75, 1])
            if np.random.random(1)[0] > (1 - catch_chance):
                return BattedBallOutcome.POPOUT, 0, None
            # otherwise...
            closest_fielder = None
            if direction < 22.5:  # LF
                closest_fielder = THIRD_BASEMAN
            elif 22.5 <= direction <= 45:  # CF
                closest_fielder = SHORTSTOP
            elif 45 < direction <= 67.5:  # RF
                closest_fielder = SECOND_BASEMAN
            elif direction > 67.5:
                closest_fielder = FIRST_BASEMAN
            fielder: Player = fielding_team.get_player_at_position(closest_fielder)
            catch_probability, fielder_distance = self.get_catch_probability(distance_of_ball, direction, closest_fielder, fielding_team, False)
            if np.sign(catch_probability) <= 0:  # caught
                return BattedBallOutcome.LINEOUT, fielder.throwing_power * fielder.crit_thinking_fielding, closest_fielder
            # otherwise
            return BattedBallOutcome.INFIELDSINGLE, 0, None
        else:  # C and P
            if np.random.random(1)[0] < (fielding_team.get_player_at_position(PITCHER).consistency + fielding_team.get_player_at_position(CATCHER).consistency) / 2:
                return BattedBallOutcome.POPOUT, 0, CATCHER
            else:
                return BattedBallOutcome.INFIELDSINGLE, 0, None

    def get_catch_probability(self, distance_of_ball, direction, closest_fielder, fielding_team, is_outfield):
        distance_from_fielder = get_polar_distance(distance_of_ball, FIELDER_POSITIONS[closest_fielder-1][0], direction, FIELDER_POSITIONS[closest_fielder-1][1])
        fielder: Player = fielding_team.get_player_at_position(closest_fielder)

        # can they catch the ball?
        range_mean = 0
        range_std = 0
        if is_outfield:
            range_mean = (fielder.consistency + fielder.speed) * 10 + 30
            range_std = (1 - fielder.consistency) * 10
        else:
            range_mean = (fielder.consistency + fielder.speed) * 3 + 5
            range_std = (1 - fielder.consistency) * 2
        max_range = max(0, np.random.normal(range_mean, range_std, 1)[0])
        # print("fielder distance (ft): " + str(distance_from_fielder), " fielder range (ft): " + str(max_range))

        fielder_distance = max(0, distance_from_fielder - max_range)
        range_deficit = fielder_distance - (fielder.height_inches / 24)  # diving catch!
        range_deficit /= (fielder.height_inches / 12)  # -0.5 is within range, 0 is at half of reach, 0.5 is at reach

        catch_probability = np.random.normal(range_deficit, (1 - fielder.consistency) / 2, 1)[0]  # neg is catch, pos is miss
        if np.sign(catch_probability) > 0 > range_deficit:
            # print(str(fielder) + " MAKES AN ERROR!")
            self.game_errors[self.half_inning % 2] += 1
            fielder.fielding.errors += 1
        return catch_probability, fielder_distance

    def play_game(self, should_print: bool, real_time: bool):
        # STATS #
        self.away_team.get_player_at_position('P').pitching.games_pitched_in += 1
        self.home_team.get_player_at_position('P').pitching.games_pitched_in += 1

        for idx in range(2,11):
            try:
                self.batting_team.get_player_at_position(idx).batting.games_played += 1
                self.fielding_team.get_player_at_position(idx).batting.games_played += 1
            except:
                print('Home lineup:')
                for pn in self.batting_team.lineup:
                    print(self.batting_team.get_player_by_name(pn))
                for pn in self.fielding_team.lineup:
                    print(self.fielding_team.get_player_by_name(pn))

        if real_time:
            print('Game starting soon! ' + self.away_team.name + ' (' + str(self.away_team.stats.wins) + 'W-' + str(self.away_team.stats.losses) + 'L) @ ' + self.home_team.name + ' (' + str(self.home_team.stats.wins) + 'W-' + str(self.home_team.stats.losses) + 'L) at ' + self.stadium.name + ' (' + self.stadium.state + ')')

        # inning loop #
        while self.should_continue_playing:
            if real_time:
                time.sleep(15)
            # inning attributes #
            outs = 0
            inning_half = self.half_inning % 2
            runs_this_inning = 0
            runners_on_base = [None, None, None]

            # set correct teams #
            if inning_half == AWAY_TEAM:
                self.fielding_team = self.home_team
                self.batting_team = self.away_team
            else:
                self.fielding_team = self.away_team
                self.batting_team = self.home_team

            # inning loop #
            pitcher: Player = self.fielding_team.get_player_at_position('P')
            if self.half_inning > 17:  # extra innings
                last_out_idx = (self.batter_on_plate[inning_half] - 1) % 9 - 1
                if last_out_idx == -1:
                    last_out_idx = 8
                runners_on_base[SECOND_BASE] = self.batting_team.get_player_by_name(self.batting_team.lineup[last_out_idx])
            # print("Now pitching: " + str(pitcher))
            if should_print:
                print()
                print("Now entering: " + convert_half_to_full_inning(self.half_inning) + ". Pitching is " + str(pitcher) + ': IP:' + str(pitcher.pitching.innings_pitched) + ', ERA: ' + l2(pitcher.pitching.era()) + ', WHIP: ' + l2(pitcher.pitching.whip()) + ', K/BB: ' + pitcher.pitching.k_bb_str() + ', HR: ' + str(pitcher.pitching.home_runs_allowed))
                print(self.away_team.name + ' @ ' + self.home_team.name + ': ' + str(self.game_runs[AWAY_TEAM]) + '-' + str(self.game_runs[HOME_TEAM]) + '.')
            while outs < 3:
                current_batter: Player = self.batting_team.get_player_by_name(self.batting_team.lineup[self.batter_on_plate[inning_half]])
                if real_time:
                    if count_runners(runners_on_base) > 0:
                        runners_on = 'Runners on: '
                    else:
                        runners_on = 'No runners on.'
                    if runners_on_base[FIRST_BASE] is not None:
                        runners_on += '1B (' + runners_on_base[FIRST_BASE].last_name + ') '
                    if runners_on_base[SECOND_BASE] is not None:
                        runners_on += '2B (' + runners_on_base[SECOND_BASE].last_name + ') '
                    if runners_on_base[THIRD_BASE] is not None:
                        runners_on += '3B (' + runners_on_base[THIRD_BASE].last_name + ') '
                    print('Now batting: ' + str(current_batter) + ': AVG: ' + l3(current_batter.batting.b_avg()) + ', HR: ' + str(current_batter.batting.home_runs) + ', RBI: ' + str(current_batter.batting.runs_batted_in) + ', OPS: ' + l3(current_batter.batting.ops()) + '. ' + runners_on)
                    time.sleep(2)
                outcome, pitches, contact_strength = pitch_bat_matchup(pitcher, current_batter, real_time)
                # STATS #
                current_batter.batting.plate_appearances += 1
                pitcher.pitching.batters_faced += 1

                if outcome == BattingOutcome.STRIKEOUT_SWINGING:
                    outs += 1
                    current_batter.batting.strikeouts += 1
                    current_batter.batting.at_bats += 1
                    current_batter.batting.left_on_base += count_runners(runners_on_base)
                    pitcher.pitching.strikeouts += 1

                    if should_print:
                        print(str(current_batter) + " strikes out to " + str(pitcher) + ". " + str(outs) + " out(s).")

                if real_time:
                    time.sleep(3)
                if outcome == BattingOutcome.BATTER_CONTACT:
                    launch_angle, exit_velocity, direction = calculate_hit(pitcher, current_batter, contact_strength)
                    distance_of_ball, time_in_air = calculate_impact_point(launch_angle, exit_velocity, current_batter.height_inches / 2)

                    current_batter.batting.at_bats += 1
                    current_batter.batting.batted_balls += 1

                    current_batter.batting.launch_angle.append(launch_angle)
                    current_batter.batting.exit_velocity.append(exit_velocity)
                    current_batter.batting.direction.append(direction)

                    pitcher.pitching.launch_angle_against.append(launch_angle)
                    pitcher.pitching.exit_velocity_against.append(exit_velocity)
                    pitcher.pitching.direction_against.append(direction)

                    hit_result, forceout_probability, closest_fielder = self.calculate_fielding_outcome(distance_of_ball, direction, time_in_air, self.fielding_team, self.stadium)

                    current_batter.batting.batted_ball_outcome.append(hit_result)
                    pitcher.pitching.batted_ball_outcome_against.append(hit_result)

                    if hit_result == BattedBallOutcome.HOMERUN:
                        current_batter.batting.home_runs += 1
                        current_batter.batting.runs_batted_in += count_runners(runners_on_base) + 1
                        current_batter.batting.runs += 1
                        current_batter.batting.hits += 1

                        pitcher.pitching.home_runs_allowed += 1
                        pitcher.pitching.hits_allowed += 1

                        if should_print:
                            print("A " + str(count_runners(runners_on_base) + 1) + " RUN HOME RUN! Distance (ft): " + str(int(distance_of_ball)) + " Direction: " + str(int(direction)) + " by " + str(current_batter))
                        home_runs.append((current_batter, distance_of_ball, direction, exit_velocity, launch_angle, self.half_inning))

                        runs_this_inning += count_runners(runners_on_base) + 1
                        self.game_runs[inning_half] += count_runners(runners_on_base) + 1
                        for runner in runners_on_base:
                            if runner is not None:
                                runner.batting.runs += 1
                        runners_on_base = [None, None, None]
                        self.game_hits[inning_half] += 1
                    # popout, lineout, flyout, infieldsingle, outfieldsingle, outfielddouble, outfieldtriple
                    if hit_result == BattedBallOutcome.POPOUT or hit_result == BattedBallOutcome.LINEOUT or hit_result == BattedBallOutcome.FLYOUT:
                        word = ""
                        if hit_result == BattedBallOutcome.POPOUT:
                            word = "pops"
                            current_batter.batting.out_popout += 1
                        if hit_result == BattedBallOutcome.LINEOUT:
                            word = "lines"
                            current_batter.batting.out_lineout += 1
                        if hit_result == BattedBallOutcome.FLYOUT:
                            word = "flies"
                            current_batter.batting.out_flyout += 1
                        outs += 1
                        current_batter.batting.left_on_base += count_runners(runners_on_base)
                        if should_print:
                            if closest_fielder is None:
                                print(str(current_batter) + " " + word + " out to the infield. " + str(outs) + " out(s).")
                            else:
                                print(str(current_batter) + " " + word + " out to " + str(self.fielding_team.get_player_at_position(closest_fielder)) + ". " + str(outs) + " out(s).")
                    # forceout? #
                    if real_time:
                        time.sleep(3)
                    if count_runners(runners_on_base) > 0:
                        if forceout_probability > FORCEOUT_THRESHOLD[hit_result]:
                            for idx in range(3):
                                if runners_on_base[2 - idx] is not None:
                                    outs += 1
                                    if should_print:
                                        print('Runner on ' + str(idx + 1) + " (" + str(runners_on_base[2 - idx]) + ") caught out on a " + OUTCOME_NAME[hit_result] + ". " + str(outs) + " out(s).")
                                    runners_on_base[2 - idx] = None
                                    break
                    if outs > 2:
                        break
                    if hit_result == BattedBallOutcome.INFIELDSINGLE or hit_result == BattedBallOutcome.OUTFIELDSINGLE:
                        self.game_hits[inning_half] += 1
                        current_batter.batting.singles += 1
                        current_batter.batting.hits += 1

                        pitcher.pitching.singles_allowed += 1
                        pitcher.pitching.hits_allowed += 1
                        if should_print:
                            print(str(current_batter) + " hits a single!")
                        if runners_on_base[THIRD_BASE] is not None:
                            runs_this_inning += 1
                            self.game_runs[inning_half] += 1
                            current_batter.batting.runs_batted_in += 1
                            runners_on_base[THIRD_BASE].batting.runs += 1
                            if should_print:
                                print(str(runners_on_base[THIRD_BASE]) + " scores. " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                        runners_on_base[THIRD_BASE] = runners_on_base[SECOND_BASE]
                        runners_on_base[SECOND_BASE] = runners_on_base[FIRST_BASE]
                        runners_on_base[FIRST_BASE] = current_batter
                    if hit_result == BattedBallOutcome.OUTFIELDDOUBLE:
                        self.game_hits[inning_half] += 1
                        current_batter.batting.doubles += 1
                        current_batter.batting.hits += 1
                        pitcher.pitching.extra_base_hits_allowed += 1
                        pitcher.pitching.hits_allowed += 1
                        if should_print:
                            print(str(current_batter) + " hits a double!!")
                        if np.random.random(1) > 0.4:
                            runs_this_inning += count_runners(runners_on_base)
                            self.game_runs[inning_half] += count_runners(runners_on_base)
                            if should_print:
                                print(str(count_runners(runners_on_base)) + " runner(s) score(s). " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                            current_batter.batting.runs_batted_in += count_runners(runners_on_base)
                            for runner in runners_on_base:
                                if runner is not None:
                                    runner.batting.runs += 1
                            runners_on_base = [None, current_batter, None]
                        else:
                            runs_this_inning += max(0, count_runners(runners_on_base) - 1)
                            self.game_runs[inning_half] += max(0, count_runners(runners_on_base) - 1)
                            current_batter.batting.runs_batted_in += max(0, count_runners(runners_on_base) - 1)
                            if should_print:
                                print(str(max(0, count_runners(runners_on_base) - 1)) + " runner(s) score(s). " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                            last_runner = None
                            for idx in range(3):
                                if runners_on_base[2 - idx] is not None:
                                    last_runner = runners_on_base[2 - idx]
                            for runner in runners_on_base:
                                if runner != last_runner and runner is not None:
                                    runner.batting.runs += 1
                            runners_on_base = [None, current_batter, last_runner]
                    if hit_result == BattedBallOutcome.OUTFIELDTRIPLE:
                        self.game_hits[inning_half] += 1
                        current_batter.batting.triples += 1
                        current_batter.batting.hits += 1
                        current_batter.batting.runs_batted_in += count_runners(runners_on_base)
                        pitcher.pitching.hits_allowed += 1
                        pitcher.pitching.extra_base_hits_allowed += 1
                        runs_this_inning += count_runners(runners_on_base)
                        self.game_runs[inning_half] += count_runners(runners_on_base)
                        for runner in runners_on_base:
                            if runner is not None:
                                runner.batting.runs += 1
                        if should_print:
                            print(str(current_batter) + " hits a triple!!! " + str(count_runners(runners_on_base)) + " runner(s) score(s). " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                        runners_on_base = [None, None, current_batter]
                if outcome == BattingOutcome.WALK or outcome == BattingOutcome.HIT_BY_PITCH:
                    if should_print:
                        print(str(pitcher) + " walks " + str(current_batter) + ".")
                    if outcome == BattingOutcome.WALK:
                        current_batter.batting.walks += 1
                        pitcher.pitching.walks_given += 1
                    else:
                        current_batter.batting.hit_by_pitch += 1
                        pitcher.pitching.hit_by_pitches += 1
                    if runners_on_base[THIRD_BASE] is not None and runners_on_base[SECOND_BASE] is not None and runners_on_base[FIRST_BASE] is not None:
                        runs_this_inning += 1
                        self.game_runs[inning_half] += 1
                        current_batter.batting.runs_batted_in += 1
                        if should_print:
                            print(str(runners_on_base[THIRD_BASE]) + " scores. " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                        runners_on_base[THIRD_BASE].batting.runs += 1
                        runners_on_base[THIRD_BASE] = runners_on_base[SECOND_BASE]
                        runners_on_base[SECOND_BASE] = runners_on_base[FIRST_BASE]
                        runners_on_base[FIRST_BASE] = current_batter
                    elif runners_on_base[THIRD_BASE] is None and runners_on_base[SECOND_BASE] is not None and runners_on_base[FIRST_BASE] is not None:
                        runners_on_base[THIRD_BASE] = runners_on_base[SECOND_BASE]
                        runners_on_base[SECOND_BASE] = runners_on_base[FIRST_BASE]
                        runners_on_base[FIRST_BASE] = current_batter
                    elif runners_on_base[THIRD_BASE] is None and runners_on_base[SECOND_BASE] is None and runners_on_base[FIRST_BASE] is not None:
                        runners_on_base[SECOND_BASE] = runners_on_base[FIRST_BASE]
                        runners_on_base[FIRST_BASE] = current_batter
                    else:
                        runners_on_base[FIRST_BASE] = current_batter

                self.batter_on_plate[inning_half] += 1
                self.batter_on_plate[inning_half] %= 9
                self.pitch_totals[inning_half] += pitches

                pitcher.pitching.pitches += pitches

            # populate scoring data for inning #
            self.inning_runs[inning_half].append(runs_this_inning)

            pitcher.pitching.runs_allowed += runs_this_inning

            # should game end? #
            if self.half_inning < 16:  # all the way to bot 8th
                self.should_continue_playing = True
            else:  # extra innings plus 9th (same logic)
                if inning_half == AWAY_TEAM:  # top of inning
                    self.should_continue_playing = self.game_runs[AWAY_TEAM] >= self.game_runs[HOME_TEAM]
                else:  # bottom of inning
                    self.should_continue_playing = self.game_runs[AWAY_TEAM] == self.game_runs[HOME_TEAM]

            # change inning #
            self.half_inning += 1
            pitcher.pitching.innings_pitched += 1
        if self.game_runs[AWAY_TEAM] == 0:
            self.home_team.get_player_at_position('P').pitching.shutouts += 1
        if self.game_runs[HOME_TEAM] == 0:
            self.away_team.get_player_at_position('P').pitching.shutouts += 1

        self.away_team.stats.runs_scored += self.game_runs[AWAY_TEAM]
        self.away_team.stats.runs_against += self.game_runs[HOME_TEAM]
        self.home_team.stats.runs_scored += self.game_runs[HOME_TEAM]
        self.home_team.stats.runs_against += self.game_runs[AWAY_TEAM]

        if self.game_runs[AWAY_TEAM] > self.game_runs[HOME_TEAM]:
            self.away_team.stats.wins += 1
            self.home_team.stats.losses += 1
            return AWAY_TEAM
        else:
            self.home_team.stats.wins += 1
            self.away_team.stats.losses += 1
            return HOME_TEAM

    def print_results(self):
        # Top row #
        inning_header = list(range(1, len(self.inning_runs[0]) + 1))
        inning_header.insert(0, "Team")
        inning_header.extend(['R', 'H', 'E'])

        # Scoring data #
        if len(self.inning_runs[AWAY_TEAM]) > len(self.inning_runs[HOME_TEAM]):
            self.inning_runs[HOME_TEAM].append('-')
        self.inning_runs[AWAY_TEAM].extend([self.game_runs[AWAY_TEAM], self.game_hits[AWAY_TEAM], self.game_errors[AWAY_TEAM]])
        self.inning_runs[HOME_TEAM].extend([self.game_runs[HOME_TEAM], self.game_hits[HOME_TEAM], self.game_errors[HOME_TEAM]])

        # add team names #
        self.inning_runs[AWAY_TEAM].insert(0, self.away_team.name)
        self.inning_runs[HOME_TEAM].insert(0, self.home_team.name)

        # make table and print #
        table = [inning_header, self.inning_runs[AWAY_TEAM], self.inning_runs[HOME_TEAM]]
        print()
        print(tabulate(table))
        print('Game played at ' + self.stadium.name + ", " + self.stadium.state + " (" + str(int(self.stadium.field_distances[0])) + "/" + str(int(self.stadium.field_distances[1])) + "/" + str(int(self.stadium.field_distances[2])) + "ft)")
        print('Away pitches: ' + str(self.pitch_totals[AWAY_TEAM]) + ' Home pitches: ' + str(self.pitch_totals[HOME_TEAM]))
        print()
        print('Home runs:')
        for batter, dist, dir, ev, la, inning in home_runs:
            print(str(batter) + " in " + convert_half_to_full_inning(inning) + ". Distance: " + str(int(dist)) + " ft, EV: " + str(round(ev,1)) + " mph, LA: " + str(round(la,1)) + " deg, Field Direction: " + str(round(dir,1)) + " deg")

    async def play_game_discord(self, c, t_c):
        # STATS #
        self.away_team.get_player_at_position('P').pitching.games_pitched_in += 1
        self.home_team.get_player_at_position('P').pitching.games_pitched_in += 1

        try:
            for idx in range(2, 11):
                self.batting_team.get_player_at_position(idx).batting.games_played += 1
                self.fielding_team.get_player_at_position(idx).batting.games_played += 1
        except TypeError:
            print('Home lineup:')
            for pn in self.batting_team.lineup:
                print(self.batting_team.get_player_by_name(pn))
            print('Away lineup:')
            for pn in self.fielding_team.lineup:
                print(self.fielding_team.get_player_by_name(pn))

        await c.send('***Game starting soon!*** ' + self.away_team.name + ' (' + str(self.away_team.stats.wins) + 'W-' + str(self.away_team.stats.losses) + 'L) @ ' + self.home_team.name + ' (' + str(self.home_team.stats.wins) + 'W-' + str(self.home_team.stats.losses) + 'L) at ' + self.stadium.name + ' (' + self.stadium.state + ')')

        # inning loop #
        while self.should_continue_playing:
            time.sleep(15)
            # inning attributes #
            outs = 0
            inning_half = self.half_inning % 2
            runs_this_inning = 0
            runners_on_base = [None, None, None]

            # set correct teams #
            if inning_half == AWAY_TEAM:
                self.fielding_team = self.home_team
                self.batting_team = self.away_team
            else:
                self.fielding_team = self.away_team
                self.batting_team = self.home_team

            # inning loop #
            pitcher: Player = self.fielding_team.get_player_at_position('P')
            if self.half_inning > 17:  # extra innings
                last_out_idx = (self.batter_on_plate[inning_half] - 1) % 9 - 1
                if last_out_idx == -1:
                    last_out_idx = 8
                runners_on_base[SECOND_BASE] = self.batting_team.get_player_by_name(self.batting_team.lineup[last_out_idx])
            # print("Now pitching: " + str(pitcher))
            await c.send("**Now entering:** " + convert_half_to_full_inning(self.half_inning) + ". Pitching is " + str(pitcher) + ': IP:' + str(pitcher.pitching.innings_pitched) + ', ERA: ' + l2(pitcher.pitching.era()) + ', WHIP: ' + l2(pitcher.pitching.whip()) + ', K/BB: ' + pitcher.pitching.k_bb_str() + ', HR: ' + str(pitcher.pitching.home_runs_allowed))
            await c.send('`' + self.away_team.name + ' @ ' + self.home_team.name + ': ' + str(self.game_runs[AWAY_TEAM]) + '-' + str(self.game_runs[HOME_TEAM]) + '.`')
            while outs < 3:
                current_batter: Player = self.batting_team.get_player_by_name(self.batting_team.lineup[self.batter_on_plate[inning_half]])
                if count_runners(runners_on_base) > 0:
                    runners_on = 'Runners on: '
                else:
                    runners_on = 'No runners on.'
                if runners_on_base[FIRST_BASE] is not None:
                    runners_on += '1B (' + runners_on_base[FIRST_BASE].last_name + ') '
                if runners_on_base[SECOND_BASE] is not None:
                    runners_on += '2B (' + runners_on_base[SECOND_BASE].last_name + ') '
                if runners_on_base[THIRD_BASE] is not None:
                    runners_on += '3B (' + runners_on_base[THIRD_BASE].last_name + ') '
                await c.send('**Now batting:** ' + str(current_batter) + '\nAVG: ' + l3(current_batter.batting.b_avg()) + ', HR: ' + str(current_batter.batting.home_runs) + ', RBI: ' + str(current_batter.batting.runs_batted_in) + ', OPS: ' + l3(current_batter.batting.ops()) + '. ' + runners_on)
                time.sleep(2)
                outcome, pitches, contact_strength = await pitch_bat_matchup_discord(pitcher, current_batter, c)
                # STATS #
                current_batter.batting.plate_appearances += 1
                pitcher.pitching.batters_faced += 1

                if outcome == BattingOutcome.STRIKEOUT_SWINGING:
                    outs += 1
                    current_batter.batting.strikeouts += 1
                    current_batter.batting.at_bats += 1
                    current_batter.batting.left_on_base += count_runners(runners_on_base)
                    pitcher.pitching.strikeouts += 1

                    await c.send(str(current_batter) + " strikes out to " + str(pitcher) + ". " + str(outs) + " out(s).")

                time.sleep(3)
                if outcome == BattingOutcome.BATTER_CONTACT:
                    launch_angle, exit_velocity, direction = calculate_hit(pitcher, current_batter, contact_strength)
                    distance_of_ball, time_in_air = calculate_impact_point(launch_angle, exit_velocity, current_batter.height_inches / 2)

                    current_batter.batting.at_bats += 1
                    current_batter.batting.batted_balls += 1

                    current_batter.batting.launch_angle.append(launch_angle)
                    current_batter.batting.exit_velocity.append(exit_velocity)
                    current_batter.batting.direction.append(direction)

                    pitcher.pitching.launch_angle_against.append(launch_angle)
                    pitcher.pitching.exit_velocity_against.append(exit_velocity)
                    pitcher.pitching.direction_against.append(direction)

                    hit_result, forceout_probability, closest_fielder = self.calculate_fielding_outcome(distance_of_ball, direction, time_in_air, self.fielding_team, self.stadium)

                    current_batter.batting.batted_ball_outcome.append(hit_result)
                    pitcher.pitching.batted_ball_outcome_against.append(hit_result)

                    if hit_result == BattedBallOutcome.HOMERUN:
                        current_batter.batting.home_runs += 1
                        current_batter.batting.runs_batted_in += count_runners(runners_on_base) + 1
                        current_batter.batting.runs += 1
                        current_batter.batting.hits += 1

                        pitcher.pitching.home_runs_allowed += 1
                        pitcher.pitching.hits_allowed += 1

                        await c.send("A " + str(count_runners(runners_on_base) + 1) + " RUN HOME RUN! Distance (ft): " + str(int(distance_of_ball)) + " Direction: " + str(int(direction)) + " by " + str(current_batter))
                        home_runs.append((current_batter, distance_of_ball, direction, exit_velocity, launch_angle, self.half_inning))

                        runs_this_inning += count_runners(runners_on_base) + 1
                        self.game_runs[inning_half] += count_runners(runners_on_base) + 1
                        for runner in runners_on_base:
                            if runner is not None:
                                runner.batting.runs += 1
                        runners_on_base = [None, None, None]
                        self.game_hits[inning_half] += 1
                    # popout, lineout, flyout, infieldsingle, outfieldsingle, outfielddouble, outfieldtriple
                    if hit_result == BattedBallOutcome.POPOUT or hit_result == BattedBallOutcome.LINEOUT or hit_result == BattedBallOutcome.FLYOUT:
                        word = ""
                        if hit_result == BattedBallOutcome.POPOUT:
                            word = "pops"
                            current_batter.batting.out_popout += 1
                        if hit_result == BattedBallOutcome.LINEOUT:
                            word = "lines"
                            current_batter.batting.out_lineout += 1
                        if hit_result == BattedBallOutcome.FLYOUT:
                            word = "flies"
                            current_batter.batting.out_flyout += 1
                        outs += 1
                        current_batter.batting.left_on_base += count_runners(runners_on_base)
                        if closest_fielder is None:
                            await c.send(str(current_batter) + " " + word + " out to the infield. " + str(outs) + " out(s).")
                        else:
                            await c.send(str(current_batter) + " " + word + " out to " + str(self.fielding_team.get_player_at_position(closest_fielder)) + ". " + str(outs) + " out(s).")
                    # forceout? #
                    time.sleep(3)
                    if count_runners(runners_on_base) > 0:
                        if forceout_probability > FORCEOUT_THRESHOLD[hit_result]:
                            for idx in range(3):
                                if runners_on_base[2 - idx] is not None:
                                    outs += 1
                                    await c.send('Runner on ' + str(idx + 1) + " (" + str(runners_on_base[2 - idx]) + ") caught out on a " + OUTCOME_NAME[hit_result] + ". " + str(outs) + " out(s).")
                                    runners_on_base[2 - idx] = None
                                    break
                    if outs > 2:
                        break
                    if hit_result == BattedBallOutcome.INFIELDSINGLE or hit_result == BattedBallOutcome.OUTFIELDSINGLE:
                        self.game_hits[inning_half] += 1
                        current_batter.batting.singles += 1
                        current_batter.batting.hits += 1

                        pitcher.pitching.singles_allowed += 1
                        pitcher.pitching.hits_allowed += 1
                        await c.send(str(current_batter) + " hits a single!")
                        if runners_on_base[THIRD_BASE] is not None:
                            runs_this_inning += 1
                            self.game_runs[inning_half] += 1
                            current_batter.batting.runs_batted_in += 1
                            runners_on_base[THIRD_BASE].batting.runs += 1
                            await c.send(str(runners_on_base[THIRD_BASE]) + " scores. " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                        runners_on_base[THIRD_BASE] = runners_on_base[SECOND_BASE]
                        runners_on_base[SECOND_BASE] = runners_on_base[FIRST_BASE]
                        runners_on_base[FIRST_BASE] = current_batter
                    if hit_result == BattedBallOutcome.OUTFIELDDOUBLE:
                        self.game_hits[inning_half] += 1
                        current_batter.batting.doubles += 1
                        current_batter.batting.hits += 1
                        pitcher.pitching.extra_base_hits_allowed += 1
                        pitcher.pitching.hits_allowed += 1
                        await c.send(str(current_batter) + " hits a double!!")
                        if np.random.random(1) > 0.4:
                            runs_this_inning += count_runners(runners_on_base)
                            self.game_runs[inning_half] += count_runners(runners_on_base)
                            await c.send(str(count_runners(runners_on_base)) + " runner(s) score(s). " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                            current_batter.batting.runs_batted_in += count_runners(runners_on_base)
                            for runner in runners_on_base:
                                if runner is not None:
                                    runner.batting.runs += 1
                            runners_on_base = [None, current_batter, None]
                        else:
                            runs_this_inning += max(0, count_runners(runners_on_base) - 1)
                            self.game_runs[inning_half] += max(0, count_runners(runners_on_base) - 1)
                            current_batter.batting.runs_batted_in += max(0, count_runners(runners_on_base) - 1)
                            await c.send(str(max(0, count_runners(runners_on_base) - 1)) + " runner(s) score(s). " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                            last_runner = None
                            for idx in range(3):
                                if runners_on_base[2 - idx] is not None:
                                    last_runner = runners_on_base[2 - idx]
                            for runner in runners_on_base:
                                if runner != last_runner and runner is not None:
                                    runner.batting.runs += 1
                            runners_on_base = [None, current_batter, last_runner]
                    if hit_result == BattedBallOutcome.OUTFIELDTRIPLE:
                        self.game_hits[inning_half] += 1
                        current_batter.batting.triples += 1
                        current_batter.batting.hits += 1
                        current_batter.batting.runs_batted_in += count_runners(runners_on_base)
                        pitcher.pitching.hits_allowed += 1
                        pitcher.pitching.extra_base_hits_allowed += 1
                        runs_this_inning += count_runners(runners_on_base)
                        self.game_runs[inning_half] += count_runners(runners_on_base)
                        for runner in runners_on_base:
                            if runner is not None:
                                runner.batting.runs += 1
                        await c.send(str(current_batter) + " hits a triple!!! " + str(count_runners(runners_on_base)) + " runner(s) score(s). " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                        runners_on_base = [None, None, current_batter]
                if outcome == BattingOutcome.WALK or outcome == BattingOutcome.HIT_BY_PITCH:
                    if outcome == BattingOutcome.WALK:
                        await c.send(str(pitcher) + " walks " + str(current_batter) + ".")
                    else:
                        await c.send(str(pitcher) + " hits " + str(current_batter) + " with the pitch!")
                    if outcome == BattingOutcome.WALK:
                        current_batter.batting.walks += 1
                        pitcher.pitching.walks_given += 1
                    else:
                        current_batter.batting.hit_by_pitch += 1
                        pitcher.pitching.hit_by_pitches += 1
                    if runners_on_base[THIRD_BASE] is not None and runners_on_base[SECOND_BASE] is not None and runners_on_base[FIRST_BASE] is not None:
                        runs_this_inning += 1
                        self.game_runs[inning_half] += 1
                        current_batter.batting.runs_batted_in += 1
                        await c.send(str(pitcher) + " walks " + str(current_batter) + ".")(str(runners_on_base[THIRD_BASE]) + " scores. " + self.away_team.name + ' ' + str(self.game_runs[AWAY_TEAM]) + ', ' + self.home_team.name + ' ' + str(self.game_runs[HOME_TEAM]))
                        runners_on_base[THIRD_BASE].batting.runs += 1
                        runners_on_base[THIRD_BASE] = runners_on_base[SECOND_BASE]
                        runners_on_base[SECOND_BASE] = runners_on_base[FIRST_BASE]
                        runners_on_base[FIRST_BASE] = current_batter
                    elif runners_on_base[THIRD_BASE] is None and runners_on_base[SECOND_BASE] is not None and runners_on_base[FIRST_BASE] is not None:
                        runners_on_base[THIRD_BASE] = runners_on_base[SECOND_BASE]
                        runners_on_base[SECOND_BASE] = runners_on_base[FIRST_BASE]
                        runners_on_base[FIRST_BASE] = current_batter
                    elif runners_on_base[THIRD_BASE] is None and runners_on_base[SECOND_BASE] is None and runners_on_base[FIRST_BASE] is not None:
                        runners_on_base[SECOND_BASE] = runners_on_base[FIRST_BASE]
                        runners_on_base[FIRST_BASE] = current_batter
                    else:
                        runners_on_base[FIRST_BASE] = current_batter

                self.batter_on_plate[inning_half] += 1
                self.batter_on_plate[inning_half] %= 9
                self.pitch_totals[inning_half] += pitches

                pitcher.pitching.pitches += pitches

            # populate scoring data for inning #
            self.inning_runs[inning_half].append(runs_this_inning)

            pitcher.pitching.runs_allowed += runs_this_inning

            # should game end? #
            if self.half_inning < 16:  # all the way to bot 8th
                self.should_continue_playing = True
            else:  # extra innings plus 9th (same logic)
                if inning_half == AWAY_TEAM:  # top of inning
                    self.should_continue_playing = self.game_runs[AWAY_TEAM] >= self.game_runs[HOME_TEAM]
                else:  # bottom of inning
                    self.should_continue_playing = self.game_runs[AWAY_TEAM] == self.game_runs[HOME_TEAM]

            # change inning #
            self.half_inning += 1
            pitcher.pitching.innings_pitched += 1
        if self.game_runs[AWAY_TEAM] == 0:
            self.home_team.get_player_at_position('P').pitching.shutouts += 1
        if self.game_runs[HOME_TEAM] == 0:
            self.away_team.get_player_at_position('P').pitching.shutouts += 1

        self.away_team.stats.runs_scored += self.game_runs[AWAY_TEAM]
        self.away_team.stats.runs_against += self.game_runs[HOME_TEAM]
        self.home_team.stats.runs_scored += self.game_runs[HOME_TEAM]
        self.home_team.stats.runs_against += self.game_runs[AWAY_TEAM]

        if self.game_runs[AWAY_TEAM] > self.game_runs[HOME_TEAM]:
            self.away_team.stats.wins += 1
            self.home_team.stats.losses += 1
        else:
            self.home_team.stats.wins += 1
            self.away_team.stats.losses += 1

        await self.print_results_discord(t_c)
        await c.delete(reason='Game Complete')

    async def print_results_discord(self, c):
        # Top row #
        inning_header = list(range(1, len(self.inning_runs[0]) + 1))
        inning_header.insert(0, "Team")
        inning_header.extend(['R', 'H', 'E'])

        # Scoring data #
        if len(self.inning_runs[AWAY_TEAM]) > len(self.inning_runs[HOME_TEAM]):
            self.inning_runs[HOME_TEAM].append('-')
        self.inning_runs[AWAY_TEAM].extend([self.game_runs[AWAY_TEAM], self.game_hits[AWAY_TEAM], self.game_errors[AWAY_TEAM]])
        self.inning_runs[HOME_TEAM].extend([self.game_runs[HOME_TEAM], self.game_hits[HOME_TEAM], self.game_errors[HOME_TEAM]])

        # add team names #
        self.inning_runs[AWAY_TEAM].insert(0, self.away_team.name)
        self.inning_runs[HOME_TEAM].insert(0, self.home_team.name)

        # make table and print #
        table = [inning_header, self.inning_runs[AWAY_TEAM], self.inning_runs[HOME_TEAM]]
        await c.send('```' + tabulate(table) + '```')
        await c.send('Game played at ' + self.stadium.name + ", " + self.stadium.state + " (" + str(int(self.stadium.field_distances[0])) + "/" + str(int(self.stadium.field_distances[1])) + "/" + str(int(self.stadium.field_distances[2])) + "ft)")
        await c.send('Away pitches: ' + str(self.pitch_totals[AWAY_TEAM]) + ' Home pitches: ' + str(self.pitch_totals[HOME_TEAM]))
        await c.send('\nHome runs:')
        for batter, dist, dir, ev, la, inning in home_runs:
            await c.send(str(batter) + " in " + convert_half_to_full_inning(inning) + ". Distance: " + str(int(dist)) + " ft, EV: " + str(round(ev,1)) + " mph, LA: " + str(round(la,1)) + " deg, Field Direction: " + str(round(dir,1)) + " deg")

