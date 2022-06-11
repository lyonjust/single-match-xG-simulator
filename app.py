import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

N_SIMS = 10000
SEED = 0

rng = np.random.default_rng(SEED)

home_shots = st.text_input(
    'Please enter the xG of all home team shots, separated by a comma (",")')
away_shots = st.text_input(
    'Please enter the xG of all away team shots, separated by a comma (",")')


def xg_to_array(xg_string):
    return [float(x.strip()) for x in xg_string.split(',')]


home_xg = xg_to_array(home_shots)
away_xg = xg_to_array(away_shots)


def simulate_chances(rng, number_of_sims, xg_of_chances):
    '''
    Simulates goals scored given a list of xG chances
    Returns a 1D array of size number_of_sims with each element being the goals scored in that simulation
    '''

    goals_scored = np.zeros(number_of_sims)

    for i in range(number_of_sims):
        for shot_xg in xg_of_chances:
            random = rng.random()
            if shot_xg >= random:
                outcome = 1
            else:
                outcome = 0
            goals_scored[i] = goals_scored[i] + outcome

    return goals_scored


home_goals = simulate_chances(rng, N_SIMS, home_xg)
away_goals = simulate_chances(rng, N_SIMS, away_xg)
home_margin = home_goals - away_goals

match_outcomes = np.vstack((home_goals, away_goals, home_margin))

df_match_outcomes = pd.DataFrame(match_outcomes.T, columns=[
                                 'home_goals', 'away_goals', 'home_margin'])

conditions = [
    df_match_outcomes['home_margin'] > 0,
    df_match_outcomes['home_margin'] < 0
]

choices = [
    'Home win',
    'Away win'
]

df_match_outcomes['match_outcome'] = np.select(
    condlist=conditions, choicelist=choices, default='Draw')

df_grouped = df_match_outcomes[['match_outcome',
                                'home_goals']].groupby('match_outcome').count()
df_grouped.columns = ['count']
df_grouped = df_grouped.reindex(['Home win', 'Draw', 'Away win'])

st.write(df_grouped)

fig, ax = plt.subplots()

sns.histplot(data=df_match_outcomes, x='home_margin', discrete=True,
             stat='density', hue='match_outcome', ax=ax, zorder=1)

st.pyplot(fig=fig)
