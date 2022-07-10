import numpy as np
import pandas as pd
import streamlit as st
import matplotlib as mpl
import aiohttp
import asyncio
from understat import Understat

from functions import simulate


mpl.rcParams['figure.dpi'] = 300

N_SIMS = 10000
SEED = 0

rng = np.random.default_rng(SEED)

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

caption = simulate.caption(understat=True)

st.caption(caption)

st.header('Input')
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

    return home_team, home_xg, home_goals_actual, away_team, away_xg, away_goals_actual, match_date


if understat_match_id:
    loop = asyncio.new_event_loop()
    home_team, home_xg, home_goals_actual, away_team, away_xg, away_goals_actual, match_date = loop.run_until_complete(
        get_shots(understat_match_id))

    xg_float_home = [float(xg) for xg in home_xg]
    xg_float_away = [float(xg) for xg in away_xg]

    total_home_xg = sum(xg_float_home)
    total_away_xg = sum(xg_float_away)

    home_goals = simulate.simulate_chances(rng, N_SIMS, xg_float_home)
    away_goals = simulate.simulate_chances(rng, N_SIMS, xg_float_away)
    home_margin = home_goals - away_goals

    df_match_outcomes = simulate.get_match_outcomes(
        home_goals, away_goals, home_margin)

    simulated_home_win_percent, simulated_away_win_percent, simulated_draw_percent, percentage_of_sims_matching_actual_score = simulate.get_sims_matching_score(
        df_match_outcomes, int(home_goals_actual), int(away_goals_actual))

    st.header('xG of each shot')

    st.subheader(home_team + ' (home)')

    st.write(home_xg)

    st.subheader(away_team + ' (away)')

    st.write(away_xg)

    st.header('Match outcomes')

    fig, ax = simulate.plot_margins(df_match_outcomes, int(home_goals_actual), int(away_goals_actual), simulated_home_win_percent,
                                    simulated_draw_percent, simulated_away_win_percent, percentage_of_sims_matching_actual_score, total_home_xg, total_away_xg, match_date=match_date, home_team=home_team, away_team=away_team)

    st.pyplot(fig=fig)

    fig, ax = simulate.plot_exact_scores(df_match_outcomes)

    st.pyplot(fig=fig)
