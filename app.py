import numpy as np
import pandas as pd
import streamlit as st
import matplotlib as mpl
import aiohttp
import asyncio
from understat import Understat
import requests

from functions import simulate

N_SIMS = 100000
SEED = 0

rng = np.random.default_rng(SEED)

mpl.rcParams['figure.dpi'] = 300

st.set_page_config(
    page_title="xG simulator",
    page_icon="⚽"
)

st.title('Single match xG simulator')

# st.header('Author')

st.write('App built by [Justin Lyons](https://github.com/lyonjust)')

# st.header('Overview')

caption = 'This app takes a given number of xG values for a football match and performs ' + \
    f'{N_SIMS:,}' + ' random simulations of the match based on the outcome of each shot attempt.\n\n'
caption = caption + 'It then provides a summary of the possible match outcomes.\n\n'
caption = caption + \
    'The purpose is to reinforce understanding and improve language around xG, '
caption = caption + 'as well as highlight the limitations of drawing absolute conclusions from just the overall aggregate single match xG comparison.\n\n'
caption = caption + 'If you choose a **custom match**, you can enter any sequence of custom xG values for a hypothetical home and away team, as well as a hypothetical match result.\n\n'
caption = caption + \
    'If you choose an **Understat match ID** or **FotMob match ID**, you can enter a valid match ID from Understat (e.g. "16669") or FotMob (e.g. "3854572") and the app will perform the simulation based on the shot details recorded for this match. Penalty shootouts are excluded from these analyses.\n'


understat_helper = '\nUnderstat match IDs are found from the last part of the match details URL: understat.com/match/***<match_id>***\n'
fotmob_helper = '\nFotMob match IDs are found from the digits after the "match" part of the match details URL: fotmob.com/match/***<match_id>***/matchfacts/<home_team>-vs-<away_team>'
caption = caption + understat_helper
caption = caption + fotmob_helper

# st.caption(caption)

with st.expander('Click here for an explanation of how and why to use this app'):
    st.write(caption)

custom_or_understat_or_fotmob = st.radio(
    "Simulate a...",
    ('Custom match', 'Understat match ID', 'FotMob match ID'))

st.header('Input')

if custom_or_understat_or_fotmob == 'Custom match':

    st.caption("Please enter the xG of each team's shots in the input boxes below.\n\nIndividual xG values should be separated by a comma (',')")

    default_value_home_shots_string = '0.8'
    default_value_away_shots_string = away_shots_xg = '0.2, 0.2, 0.2, 0.2'

    home_shots = st.text_input(
        'Home shots xG',
        value=default_value_home_shots_string)
    away_shots = st.text_input(
        'Away shots xG',
        value=default_value_away_shots_string)

    home_team_observed_goals = st.number_input(
        'Home team actual goals scored', min_value=0, step=1,
        value=0)
    away_team_observed_goals = st.number_input(
        'Away team actual goals scored', min_value=0, step=1,
        value=1)

    home_xg = simulate.xg_to_array(home_shots)
    away_xg = simulate.xg_to_array(away_shots)

    home_goals = simulate.simulate_chances(rng, N_SIMS, home_xg)
    away_goals = simulate.simulate_chances(rng, N_SIMS, away_xg)
    home_margin = home_goals - away_goals

    df_match_outcomes = simulate.get_match_outcomes(
        home_goals, away_goals, home_margin)

    simulated_home_win_percent, simulated_away_win_percent, simulated_draw_percent, percentage_of_sims_matching_actual_score = simulate.get_sims_matching_score(
        df_match_outcomes, home_team_observed_goals, away_team_observed_goals)

    st.header('Match outcomes')

    fig, ax = simulate.plot_margins(df_match_outcomes, home_team_observed_goals, away_team_observed_goals, simulated_home_win_percent,
                                    simulated_draw_percent, simulated_away_win_percent, percentage_of_sims_matching_actual_score, sum(home_xg), sum(away_xg))

    st.pyplot(fig=fig)

    fig, ax = simulate.plot_exact_scores(df_match_outcomes)

    st.pyplot(fig=fig)

elif custom_or_understat_or_fotmob == 'Understat match ID':
    understat_caption = 'Please enter the match ID of an Understat match, e.g. 16669'
    understat_caption = understat_caption + '\n\n' + understat_helper
    st.caption(understat_caption)

    understat_match_id = st.text_input(
        'Understat match ID')

    # cater for matches/teams with no shots?

    async def get_shots(match_id):
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            shots = await understat.get_match_shots(match_id)
        home_xg = [shot['xG'] for shot in shots['h']]
        away_xg = [shot['xG'] for shot in shots['a']]
        home_team = shots['h'][0].get('h_team')
        away_team = shots['h'][0].get('a_team')
        home_goals_actual = shots['h'][0].get('h_goals')
        away_goals_actual = shots['h'][0].get('a_goals')
        match_date = pd.to_datetime(shots['h'][0]['date'])
        home_shots_list = [(shot['minute'], shot['player'], float(
            shot['xG']), shot['result']) for shot in shots['h']]
        away_shots_list = [(shot['minute'], shot['player'], float(
            shot['xG']), shot['result']) for shot in shots['a']]

        return home_team, home_xg, home_goals_actual, away_team, away_xg, away_goals_actual, match_date, home_shots_list, away_shots_list

    if understat_match_id:
        loop = asyncio.new_event_loop()
        home_team, home_xg, home_goals_actual, away_team, away_xg, away_goals_actual, match_date, home_shots_list, away_shots_list = loop.run_until_complete(
            get_shots(understat_match_id))

        xg_float_home = [float(xg) for xg in home_xg]
        xg_float_away = [float(xg) for xg in away_xg]

        total_home_xg = sum(xg_float_home)
        total_away_xg = sum(xg_float_away)

        columns = ['Minute', 'Player', 'xG', 'Outcome']
        df_home_shots = pd.DataFrame(home_shots_list, columns=columns)
        df_away_shots = pd.DataFrame(away_shots_list, columns=columns)
        # for df in [df_home_shots, df_away_shots]:
        #     df['xG'] = df['xG'].round(decimals=2)

        home_goals = simulate.simulate_chances(rng, N_SIMS, xg_float_home)
        away_goals = simulate.simulate_chances(rng, N_SIMS, xg_float_away)
        home_margin = home_goals - away_goals

        df_match_outcomes = simulate.get_match_outcomes(
            home_goals, away_goals, home_margin)

        simulated_home_win_percent, simulated_away_win_percent, simulated_draw_percent, percentage_of_sims_matching_actual_score = simulate.get_sims_matching_score(
            df_match_outcomes, int(home_goals_actual), int(away_goals_actual))

        st.header('Shot details')

        st.subheader(home_team + ' (home)')

        st.dataframe(df_home_shots)

        st.subheader(away_team + ' (away)')

        st.dataframe(df_away_shots)

        st.header('Match outcomes')

        fig, ax = simulate.plot_margins(df_match_outcomes, int(home_goals_actual), int(away_goals_actual), simulated_home_win_percent,
                                        simulated_draw_percent, simulated_away_win_percent, percentage_of_sims_matching_actual_score, total_home_xg, total_away_xg, match_date=match_date, home_team=home_team, away_team=away_team)

        st.pyplot(fig=fig)

        fig, ax = simulate.plot_exact_scores(df_match_outcomes)

        st.pyplot(fig=fig)

else:  # fotmob

    fotmob_caption = 'Please enter the match ID of an FotMob match, e.g. 3854572'
    fotmob_caption = fotmob_caption + '\n\n' + fotmob_helper
    st.caption(fotmob_caption)

    fotmob_match_id = st.text_input(
        'FotMob match ID')

    # cater for matches/teams with no shots?

    url_base = 'https://www.fotmob.com/api/'
    url_match_details = 'matchDetails?matchId='

    if fotmob_match_id:

        url_complete = url_base + url_match_details + fotmob_match_id

        match_summary = requests.get(url_complete).json()
        shot_summary = match_summary['content']['shotmap']['shots']
        shot_summary_no_shootout = [
            shot for shot in shot_summary if shot['period'] != 'PenaltyShootout']

        shots_in_extra_time = [shot for shot in shot_summary if shot['period'] in [
            'FirstHalfExtra', 'SecondHalfExtra']]

        extra_plot_comment = ''

        simulate_result_90_mins_only = False
        if shots_in_extra_time:
            simulate_result_90_mins_only = st.checkbox(
                'Simulate result at end of 90 minutes (i.e. ignore extra time)', value=False)

        if simulate_result_90_mins_only:
            shot_summary_no_shootout = [shot for shot in shot_summary_no_shootout if shot['period'] in [
                'FirstHalf', 'SecondHalf']]

            extra_plot_comment += 'Result simulated to end of 90 minutes regulation time\n'

        penalties_not_in_shootout = [
            shot for shot in shot_summary if shot['situation'] == 'Penalty' and shot['period'] != 'PenaltyShootout']

        exclude_penalties = False
        if penalties_not_in_shootout:
            exclude_penalties = st.checkbox(
                'Exclude penalties awarded (i.e. simulate NPxG)', value=False)

        if exclude_penalties:
            shot_summary_no_shootout = [
                shot for shot in shot_summary_no_shootout if shot['situation'] != 'Penalty']

            extra_plot_comment += 'Simulations based on non-penalty xG (NPxG) only'

        match_date = pd.to_datetime(
            match_summary['general']['matchTimeUTCDate'])

        home_team_name = match_summary['general']['homeTeam']['name']
        home_team_id = match_summary['general']['homeTeam']['id']

        away_team_name = match_summary['general']['awayTeam']['name']
        away_team_id = match_summary['general']['awayTeam']['id']

        home_goals_actual = [team['score'] for team in match_summary['header']
                             ['teams'] if team['id'] == home_team_id][0]
        away_goals_actual = [team['score'] for team in match_summary['header']
                             ['teams'] if team['id'] == away_team_id][0]

        home_shots_list = [[shot['min'], shot['playerName'], shot['situation'], shot['expectedGoals'],
                            shot['eventType']] for shot in shot_summary_no_shootout if shot['teamId'] == home_team_id]
        away_shots_list = [[shot['min'], shot['playerName'], shot['situation'], shot['expectedGoals'],
                            shot['eventType']] for shot in shot_summary_no_shootout if shot['teamId'] == away_team_id]

        columns = ['Minute', 'Player', 'Situation', 'xG', 'Outcome']

        df_home_shots = pd.DataFrame(home_shots_list, columns=columns)
        df_away_shots = pd.DataFrame(away_shots_list, columns=columns)

        total_home_xg = df_home_shots['xG'].sum()
        total_away_xg = df_away_shots['xG'].sum()

        home_goals = simulate.simulate_chances(
            rng, N_SIMS, df_home_shots['xG'])
        away_goals = simulate.simulate_chances(
            rng, N_SIMS, df_away_shots['xG'])
        home_margin = home_goals - away_goals

        df_match_outcomes = simulate.get_match_outcomes(
            home_goals, away_goals, home_margin)

        simulated_home_win_percent, simulated_away_win_percent, simulated_draw_percent, percentage_of_sims_matching_actual_score = simulate.get_sims_matching_score(
            df_match_outcomes, int(home_goals_actual), int(away_goals_actual))

        st.header('Shot details')

        st.subheader(home_team_name + ' (home)')

        st.dataframe(df_home_shots)

        st.subheader(away_team_name + ' (away)')

        st.dataframe(df_away_shots)

        st.header('Match outcomes')

        fig, ax = simulate.plot_margins(df_match_outcomes, int(home_goals_actual), int(away_goals_actual), simulated_home_win_percent,
                                        simulated_draw_percent, simulated_away_win_percent, percentage_of_sims_matching_actual_score, total_home_xg, total_away_xg, match_date=match_date, home_team=home_team_name, away_team=away_team_name, extra_plot_comment=extra_plot_comment)

        st.pyplot(fig=fig)

        fig, ax = simulate.plot_exact_scores(df_match_outcomes)

        st.pyplot(fig=fig)
