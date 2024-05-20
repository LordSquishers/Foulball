import random
import time
from enum import Enum

import numpy as np

from data.stadium import Stadium
from data.team import Team
from data.text_formatting import convert_inning_id_to_string
from data.player import Player
from display.text_output import display_text


class TeamSide(Enum):
    AWAY_TEAM = 0
    HOME_TEAM = 1


class FieldPosition(Enum):
    PITCHER = 1
    CATCHER = 2
    FIRST_BASEMAN = 3
    SECOND_BASEMAN = 4
    THIRD_BASEMAN = 5
    SHORTSTOP = 6
    LEFT_FIELDER = 7
    CENTER_FIELDER = 8
    RIGHT_FIELDER = 9
    DH = 10


class BattingOutcome(Enum):
    BATTER_CONTACT = 1
    HIT_BY_PITCH = 2
    STRIKEOUT_SWINGING = 3
    STRIKEOUT_LOOKING = 4  # TODO- NOT IMPLEMENTED
    WALK = 5


class BattedBallOutcome(Enum):
    OUTFIELD_SINGLE = 1
    OUTFIELD_DOUBLE = 2
    OUTFIELD_TRIPLE = 3
    HOMERUN = 4
    FLYOUT = 5
    POPOUT = 6
    LINEOUT = 7
    DOUBLE_PLAY1B2B = 8
    DOUBLE_PLAY2B3B = 11
    DOUBLE_PLAY3BHP = 12
    TRIPLE_PLAY = 9
    INFIELD_SINGLE = 10
    GROUND_OUT = 13


# Simulation Constants #
MPH_TO_MPS = 0.44704
M_TO_FT = 3.28
GRAVITY = 9.8106
DRAG_CONSTANT_K = 0.0002855973575
BATTING_DISTANCE_ADJUSTMENT = 1.25

# for now, fielding positions are static as shifts are not implemented. #
# FORMAT: DISTANCE_IN_FEET, ANGLE_FROM_LEFT_FOUL_LINE_DEGREES #
FIELDER_POSITIONS = [(60.5, 45), (0, 0), (100, 78.75), (130, 56.25), (130, 33.75), (100, 11.25), (270, 16.5), (320, 45), (270, 82.5)]

# TODO- figure out EXACTLY how this works. I don't think ground balls existed before.
# Chance that a play results in another runner on base being forced out. #
FORCEOUT_THRESHOLD = [0.9, 0.8, 1, 1, 0.8, 1, 0.8, 1, 1, 0.75, 1, 1]  # 1 is impossible, 0 is easiest
OUTCOME_NAME = ['OUTFIELD SINGLE', 'OUTFIELD DOUBLE', 'OUTFIELD TRIPLE', 'HOMERUN', 'FLYOUT', 'POPOUT', 'LINEOUT', '-', '-', 'INFIELD SINGLE', '-', '-']


# Simulation Functions #
def simulate_at_bat(pitcher: Player, batter: Player, real_time_reporting: bool) -> (BattingOutcome, int, float):
    # at-bat variables #
    balls = 0
    strikes = 0
    total_pitches = 0

    # at-bat loop #
    while True:
        if real_time_reporting:
            time.sleep(5)
            display_option = random.choice(['Pitcher deals...', 'And the pitch...', 'Pitcher throws...', pitcher.last_name + ' deals...', 'And the pitch from ' + pitcher.last_name + '...'])
            display_text(display_option)
            time.sleep(3)

        # possible outcomes: HIT, BB, K, ꓘ, HBP #

        # finding the pitch difficulty #
        ideal_pitch_difficulty = pitcher.throwing_power * pitcher.pitching_control * pitcher.pitching_spin  # the pitchers "best" pitch
        random_ideal_blend = pitcher.pitching_control * pitcher.pitching_stamina * pitcher.confidence  # blend between a random pitch and the best pitch
        actual_pitch_difficulty = np.interp(random_ideal_blend, [0, 1], [np.random.random(), ideal_pitch_difficulty])
        ball_difficulty = (1 - pitcher.consistency) * np.random.random() + (pitcher.consistency * actual_pitch_difficulty)  # if the pitcher isn't consistent, it's even more random.

        # finding the batter ability #
        batter_skill = batter.crit_thinking_batting * batter.contact
        random_skill_blend = batter.confidence  # confidence is key
        batter_ability = np.interp(random_skill_blend, [0, 1], [np.random.random(), batter_skill])  # same deal as pitcher calculations
        swing_skill = (1 - batter.consistency) * np.random.random() + batter.consistency * batter_ability

        # calculate the distribution of hits for this matchup #
        swing_pitch_disparity = swing_skill - ball_difficulty
        dist_mean = 0.5 * swing_pitch_disparity + 0.25
        dist_std = (1.0 - abs(swing_pitch_disparity)) / 3.0
        dist_std /= 1.5  # adjusts hit difficulty. larger divisor makes the band to hit smaller.

        # find outcome of pitch #
        # TODO - graph how this logic works in desmos
        is_ball_hit = np.random.normal(dist_mean, dist_std, 1)[0] > 0.5  # if more than 50%, it's a hit!
        # depends on ball difficulty and batter smarts #
        is_ball_outside_strikezone = (ball_difficulty < 0.25) or (ball_difficulty < 0.4 and batter.crit_thinking_batting > 0.5) or (ball_difficulty < 0.75 < batter.crit_thinking_batting)
        does_ball_hit_batter = ball_difficulty < 0.01  # if it is truly an *awful* pitch

        # increment pitch count #
        total_pitches += 1

        # process outcome #
        if is_ball_hit and not does_ball_hit_batter:
            if real_time_reporting:
                display_text(batter.full_name + ' makes contact!')
            return BattingOutcome.BATTER_CONTACT, total_pitches, swing_pitch_disparity
        if does_ball_hit_batter:
            if real_time_reporting:
                display_text(batter.full_name + ' is hit by the pitch!')
            return BattingOutcome.HIT_BY_PITCH, total_pitches, 0
        if not is_ball_hit and not is_ball_outside_strikezone:
            if real_time_reporting:
                display_text('Strike! Count is now ' + str(balls) + '-' + str(strikes) + '.')
            strikes += 1
            pitcher.stats.pitching.strikes += 1
        if not is_ball_hit and is_ball_outside_strikezone:
            if real_time_reporting:
                display_text('Ball! Count is now ' + str(balls) + '-' + str(strikes) + '.')
            balls += 1
            pitcher.stats.pitching.balls += 1
        if strikes > 2:
            if real_time_reporting:
                display_text(batter.full_name + ' strikes out swinging!')
            pitcher.stats.pitching.strikeouts += 1
            return BattingOutcome.STRIKEOUT_SWINGING, total_pitches, 0
        if balls > 3:
            if real_time_reporting:
                display_text(batter.full_name + ' takes a walk.')
            pitcher.stats.pitching.walks_given += 1
            return BattingOutcome.WALK, total_pitches, 0


def calculate_hit_trajectory(pitcher: Player, batter: Player, contact_strength: float) -> (float, float, float):
    # LA: 0 is level, 90 is straight up, -90 is straight down #
    # contact_strength: 1 is pitcher dominant, 0.5 is equal, 0 is batter dominant #
    # hit direction: 0 is left foul pole, 90 is right foul pole

    # TODO- also graph this interaction in desmos or something
    # TODO- redo logic here

    # Launch Angle #
    la_magnitude = 90 * contact_strength  # this is dubious and needs a rewrite
    la_sign = np.sign(np.random.normal(contact_strength, 0.333, 1)[0])  # more often positive than negative but i DONT agree with this.
    launch_angle = la_magnitude * la_sign

    # Exit Velocity #
    ev_mean = 30 * (pitcher.throwing_power * batter.power + contact_strength) + 80  # TODO- see if this matches reality
    ev_std = 3 * (1 - contact_strength)
    exit_velocity = np.random.normal(ev_mean, ev_std, 1)[0]  # mph

    # Hit Direction #
    direction = 45
    if batter.handedness == 'left':
        direction = np.clip(np.random.normal(33, 15, 1)[0], 0, 90)
    elif batter.handedness == 'right':
        direction = np.clip(np.random.normal(66, 15, 1)[0], 0, 90)
    elif batter.handedness == 'switch':
        direction = np.clip(np.random.normal(45, 15, 1)[0], 0, 90)

    return launch_angle, exit_velocity, direction


def calculate_hit_distance_and_time(launch_angle: float, exit_velocity: float, batter_height: float) -> (float, float):
    # Equation pre-processing #
    launch_angle_radians = np.deg2rad(launch_angle)

    exit_velocity_mps = exit_velocity * MPH_TO_MPS
    exit_velocity_x = exit_velocity_mps * np.cos(launch_angle_radians)
    exit_velocity_y = exit_velocity_mps * np.sin(launch_angle_radians)

    initial_height = batter_height * 0.0254  # inches to meters

    # Calculate distance #
    time_in_air_squared = (exit_velocity_y + np.sqrt(exit_velocity_y ** 2 + 2 * initial_height * GRAVITY)) / GRAVITY
    impact_distance = exit_velocity_x * np.sqrt(time_in_air_squared) - 0.5 * DRAG_CONSTANT_K ** 2 * exit_velocity_mps ** 4 * time_in_air_squared
    return impact_distance * M_TO_FT * BATTING_DISTANCE_ADJUSTMENT, np.sqrt(time_in_air_squared)


def get_polar_distance(r1: float, r2: float, deg1: float, deg2: float) -> float:
    return np.sqrt(r1 ** 2 + r2 ** 2 - 2 * r1 * r2 * np.cos(np.deg2rad(deg1 - deg2)))


def get_stadium_wall_distance(direction: float, stadium: Stadium):
    return np.interp(direction, [0, 45, 90], stadium.field_distances)


def count_runners(runners_on_base: list) -> int:
    total_runners_on_base = 0
    for runner in runners_on_base:
        if runner is not None:
            total_runners_on_base += 1
    return total_runners_on_base


class Game:
    def __init__(self, away_team: Team, home_team: Team, real_time_reporting: bool):
        # Game Score Tracking #
        self.game_runs = [0, 0]
        self.game_hits = [0, 0]
        self.game_errors = [0, 0]
        self.inning_runs = [[], []]
        self.pitch_totals = [0, 0]
        self.home_runs = []

        # Player Tracking #
        self.batter_on_plate = [0, 0]
        self.real_time_reporting = real_time_reporting

        # Simulation Tracking #
        self.away_team: Team = away_team
        self.home_team: Team = home_team

        self.fielding_team = self.home_team
        self.batting_team = self.away_team

        # Set up teams #
        self.away_team.update_lineup()
        self.home_team.update_lineup()

        # Innings #
        self.half_inning = 0
        self.should_continue_playing = True

        # Location by Playboi Carti #
        self.stadium = home_team.home_stadium

    def __repr__(self):
        return self.away_team.short_name + ' @ ' + self.home_team.short_name

    def get_catch_probability(self, distance_of_ball: float, direction: float, fielder_position: int, fielding_team: Team, is_outfield: bool) -> (float, float):
        # TODO- redo all this logic to detect which positions this passes by (i.e. lineout to infield vs ground to outfield)
        distance_from_fielder = get_polar_distance(distance_of_ball, FIELDER_POSITIONS[fielder_position - 1][0], direction, FIELDER_POSITIONS[fielder_position - 1][1])
        fielder: Player = fielding_team.get_player_at_field_position_in_lineup(fielder_position)

        # Calculate Fielder Reach #
        range_mean = 0
        range_std = 0
        if is_outfield:  # outfielders have much more range compared to infielders
            range_mean = 10 * (fielder.consistency + fielder.speed) + 30
            range_std = 10 * (1 - fielder.consistency)
        else:  # probably because they have less time to react
            range_mean = 3 * (fielder.consistency + fielder.speed) + 5
            range_std = 2 * (1 - fielder.consistency)
        max_range = np.max([0, np.random.normal(range_mean, range_std, 1)[0]])

        # Calculating Range Deficit (units are in feet) #
        fielder_distance = np.max([0, distance_from_fielder - max_range])
        range_deficit = fielder_distance - (fielder.height_inches / 12 / 2)  # diving catch! they say your wingspan is your height, so use half.
        range_deficit /= fielder.height_inches / 12  # shifts to: -0.5 is in range, 0 is at half of reach, 0.5 is full extension

        # Catching Probability #
        catch_probability = np.random.normal(range_deficit, 0.5 * (1 - fielder.consistency), 1)[0]
        # negative is catch, positive is miss. consistency of 1 means if it's within half reach they will ALWAYS get it.
        if np.sign(catch_probability) > 0 and range_deficit < 0:  # they didn't catch it, but it was catchable!
            if self.real_time_reporting:
                display_text(fielder.last_name + ' makes an error fielding the ball!')
            fielder.stats.fielding.errors += 1
            self.game_errors[self.half_inning % 2] += 1
        return catch_probability, fielder_distance

    def calculate_fielding_outcome(self, distance_of_ball: float, direction: float, time_in_air: float, launch_angle: float, fielding_team: Team, stadium: Stadium) -> (BattedBallOutcome, float, FieldPosition):
        # TODO- groundouts don't reaalllyyy exist, must simulate path of ball.
        # Where is the ball going to land? #
        if distance_of_ball > get_stadium_wall_distance(direction, stadium):
            return BattedBallOutcome.HOMERUN, 0, None
        if distance_of_ball > 160:  # infield/outfield boundary, feet
            # Finding the closest fielder #
            if direction < 33:  # left field
                closest_fielder = FieldPosition.LEFT_FIELDER
            elif 33 <= direction <= 66:  # center field
                closest_fielder = FieldPosition.CENTER_FIELDER
            else:  # right field
                closest_fielder = FieldPosition.RIGHT_FIELDER

            # Fielder Play Simulation #
            fielder: Player = fielding_team.get_player_at_field_position_in_lineup(closest_fielder.value)
            catch_probability, fielder_distance = self.get_catch_probability(distance_of_ball, direction, closest_fielder.value, fielding_team, True)
            fielder_play_skill = fielder.throwing_power * fielder.crit_thinking_fielding

            # Catch logic #
            if np.sign(catch_probability) <= 0:  # it's a catch!
                return BattedBallOutcome.FLYOUT, fielder_play_skill, closest_fielder
            else:  # no catch.
                if fielder_distance > 100:  # crazy, but possible
                    return BattedBallOutcome.OUTFIELD_TRIPLE, fielder_play_skill, closest_fielder
                elif 25 <= fielder_distance <= 100:  # solid hit
                    return BattedBallOutcome.OUTFIELD_DOUBLE, fielder_play_skill, closest_fielder
                elif fielder_distance < 25:  # bloop
                    return BattedBallOutcome.OUTFIELD_SINGLE, fielder_play_skill, closest_fielder
        elif 50 < distance_of_ball < 160:  # infield, feet
            # figuring out if it is a popout #
            popout_catch_chance = np.interp(time_in_air, [2, 3, 4, 6], [0, 0.5, 0.7, 1])  # seconds, chance.
            if np.random.random() > (1 - popout_catch_chance):  # it's a popout!
                return BattedBallOutcome.POPOUT, 0, None

            # otherwise... find the closest fielder #
            if direction < 22.5:  # 3B
                closest_fielder = FieldPosition.THIRD_BASEMAN
            elif 22.5 <= direction <= 45:  # SS (has a litttle more range so has the =s)
                closest_fielder = FieldPosition.SHORTSTOP
            elif 45 < direction <= 67.5:  # 2B (little more right range so has one =)
                closest_fielder = FieldPosition.SECOND_BASEMAN
            else:  # 1B
                closest_fielder = FieldPosition.FIRST_BASEMAN

            # Fielder Play Simulation #
            fielder: Player = fielding_team.get_player_at_field_position_in_lineup(closest_fielder.value)
            catch_probability, fielder_distance = self.get_catch_probability(distance_of_ball, direction, closest_fielder.value, fielding_team, False)
            fielder_play_skill = fielder.throwing_power * fielder.crit_thinking_fielding

            # Catch logic #
            if np.sign(catch_probability) <= 0:  # caught!
                return BattedBallOutcome.LINEOUT, fielder_play_skill, closest_fielder
            else:  # not caught.
                # TODO- TEMPORARY GROUND BALLS
                if np.random.random() > 0.5:  # ground ball
                    return BattedBallOutcome.GROUND_OUT, fielder_play_skill, closest_fielder
                else:  # single
                    return BattedBallOutcome.INFIELD_SINGLE, 0, None
        else:  # catcher/pitcher fielding
            pitcher = fielding_team.get_player_at_field_position_in_lineup('P')
            catcher = fielding_team.get_player_at_field_position_in_lineup('C')
            if np.random.random() < (pitcher.consistency + catcher.consistency) / 2:  # average of fielding ability
                if launch_angle > 0:  # "pop up"
                    return BattedBallOutcome.POPOUT, 0, random.choice([FieldPosition.CATCHER, FieldPosition.PITCHER])
                else:  # topped the ball
                    return BattedBallOutcome.GROUND_OUT, 0, random.choice([FieldPosition.CATCHER, FieldPosition.PITCHER])
            else:  # they don't make it in time :(
                return BattedBallOutcome.INFIELD_SINGLE, 0, None
