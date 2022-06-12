import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

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

st.header('Overview')

caption = 'This app takes a given number of xG values for a hypothetical home and away team in a football match.\n\n'
caption = caption + 'It performs 10,000 random simulations of the match based on the outcome of each shot attempt.\n\n'
caption = caption + 'It then provides a summary of the possible match outcomes.\n\n'
caption = caption + \
    'The purpose is to reinforce and improve understanding and language around xG, '
caption = caption + 'as well as highlight the limitations of drawing absolute conclusions from just the overall aggregate single match xG comparison.\n\n'

st.write("App by [Justin Lyons](https://lyonjust.github.io/)")

st.caption(caption)

st.header('Input')
st.caption("Please enter the xG of each team's shots in the input boxes below.\n\nIndividual xG values should be separated by a comma (',')")

default_value_home_shots_string = '0.75, 0.75, 0.5, 0.4'
default_value_away_shots_string = away_shots_xg = '0.12, ' * 19 + '0.12'

home_shots = st.text_input(
    'Home shots xG',
    value=default_value_home_shots_string)
away_shots = st.text_input(
    'Away shots xG',
    value=default_value_away_shots_string)


home_team_observed_goals = st.text_input(
    'Home team actual goals scored',
    value=0)
away_team_observed_goals = st.text_input(
    'Away team actual goals scored',
    value=0)


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

df_grouped['percentage'] = df_grouped['proportion'].astype(
    float).map("{:.0%}".format)

df_grouped = df_grouped[['percentage']]

simulated_home_win_percent = df_grouped.loc['Home win', 'percentage']
simulated_away_win_percent = df_grouped.loc['Away win', 'percentage']

st.header('Match outcomes')

st.write(df_grouped)

plot_title = 'Home team ' + f'{sum(home_xg):.2f}' + \
    ' xG - Away team ' + f'{sum(away_xg):.2f}' + ' xG\n'

plot_title = plot_title + 'Home team wins in ' + \
    simulated_home_win_percent + ' of simulations\n'
plot_title = plot_title + 'Away team wins in ' + \
    simulated_away_win_percent + ' of simulations'

fig, ax = plt.subplots()

sns.histplot(data=df_match_outcomes, x='home_margin', discrete=True,
             stat='density', hue='match_outcome', ax=ax, zorder=1)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_ylabel('density')

fig.suptitle(plot_title)

st.pyplot(fig=fig)
