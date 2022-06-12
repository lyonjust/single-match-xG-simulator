import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

N_SIMS = 10000
SEED = 0

rng = np.random.default_rng(SEED)

st.title('Single match xG simulator')


st.header('Input')
st.caption("Please enter the xG of each team's shots in the input boxes below. Individual xG values should be separated by a comma (',')")

default_value_home_shots_string = '0.75, 0.75, 0.5, 0.4'
default_value_away_shots_string = away_shots_xg = '0.12, ' * 19 + '0.12'

home_shots = st.text_input(
    'Home shots xG',
    value=default_value_home_shots_string)
away_shots = st.text_input(
    'Away shots xG',
    value=default_value_away_shots_string)


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

df_grouped['proportion'] = df_grouped['count'] / df_grouped['count'].sum()

df_grouped = df_grouped[['proportion']]

st.header('Outcome')

st.write(df_grouped)

plot_title = 'Home team ' + f'{sum(home_xg):.2f}' + \
    ' xG - Away team ' + f'{sum(away_xg):.2f}' + ' xG\n'

# plot_title = plot_title + 'Home team win ' +

fig, ax = plt.subplots()

sns.histplot(data=df_match_outcomes, x='home_margin', discrete=True,
             stat='density', hue='match_outcome', ax=ax, zorder=1)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_ylabel('density')

fig.suptitle(plot_title)

st.pyplot(fig=fig)
