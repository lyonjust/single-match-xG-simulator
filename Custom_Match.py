import numpy as np
import streamlit as st
import matplotlib as mpl

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

caption = simulate.caption(understat=False)

st.caption(caption)

st.caption("The [Understat page](Understat_Match) can be used to perform the same simulation on any match from history that is recorded on Understat's website.")

st.header('Input')
st.caption("Please enter the xG of each team's shots in the input boxes below.\n\nIndividual xG values should be separated by a comma (',')")

default_value_home_shots_string = '0.29, 0.07, 0.04, 0.09, 0.05, 0.06, 0.03, 0.04, 0.13, 0.01, 0.04, 0.05, 0.1, 0.12, 0.04, 0.02, 0.13, 0.04, 0.15, 0.03, 0.05, 0.29, 0.16, 0.16'
default_value_away_shots_string = away_shots_xg = '0.1, 0.06, 0.7, 0.06'

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
