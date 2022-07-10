import numpy as np
import pandas as pd
import streamlit as st
import matplotlib as mpl
import aiohttp
import asyncio
from understat import Understat

from functions import simulate

N_SIMS = 10000
SEED = 0

rng = np.random.default_rng(SEED)

mpl.rcParams['figure.dpi'] = 300


st.set_page_config(
    page_title="xG simulator",
    page_icon="⚽",
    #    layout="wide",
    #    initial_sidebar_state="expanded"
)

st.title('Single match xG simulator')

st.header('Author')

st.write("[Justin Lyons](https://lyonjust.github.io/)")

st.header('Overview')

caption = 'This app takes a given number of xG values for a football match and performs 10,000 random simulations of the match based on the outcome of each shot attempt.\n\n'
caption = caption + 'It then provides a summary of the possible match outcomes.\n\n'
caption = caption + \
    'The purpose is to reinforce understanding and improve language around xG, '
caption = caption + 'as well as highlight the limitations of drawing absolute conclusions from just the overall aggregate single match xG comparison.\n\n'
caption = caption + 'If you choose a "custom match", you can enter any sequence of custom xG values for a hypothetical home and away team, as well as a hypothetical match result.\n\n'
caption = caption + \
    'If you choose an "Understat match ID", you can enter a valid match ID for Understat (e.g. "16669") and the app will perform the simulation based on the shot details Understat recorded for this match.\n'
caption = caption + '\nMatch IDs are found from the last part of the Understat match details URL: understat.com/match/<match_id>'

st.caption(caption)

custom_or_understat = st.radio(
    "Simulate a...",
    ('Custom match', 'Understat match ID'))

st.header('Input')

if custom_or_understat == 'Custom match':

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

else:
    st.caption("Please enter the match ID of an Understat match, e.g. 16669")

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

        # st.write(home_xg)
        st.dataframe(df_home_shots)

        st.subheader(away_team + ' (away)')

        # st.write(away_xg)
        st.dataframe(df_away_shots)

        st.header('Match outcomes')

        fig, ax = simulate.plot_margins(df_match_outcomes, int(home_goals_actual), int(away_goals_actual), simulated_home_win_percent,
                                        simulated_draw_percent, simulated_away_win_percent, percentage_of_sims_matching_actual_score, total_home_xg, total_away_xg, match_date=match_date, home_team=home_team, away_team=away_team)

        st.pyplot(fig=fig)

        fig, ax = simulate.plot_exact_scores(df_match_outcomes)

        st.pyplot(fig=fig)
