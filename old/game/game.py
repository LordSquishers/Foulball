
class Game:
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

            # should simulation end? #
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
