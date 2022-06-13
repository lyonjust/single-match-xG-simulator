import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from highlight_text import HighlightText, ax_text, fig_text

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

caption = 'This app takes a given number of xG values for a hypothetical home and away team in a football match.\n\n'
caption = caption + 'It performs 10,000 random simulations of the match based on the outcome of each shot attempt.\n\n'
caption = caption + 'It then provides a summary of the possible match outcomes.\n\n'
caption = caption + \
    'The purpose is to reinforce understanding and improve language around xG, '
caption = caption + 'as well as highlight the limitations of drawing absolute conclusions from just the overall aggregate single match xG comparison.\n\n'
caption = caption + \
    'The default values are taken from the 2022 Champions League Final between Liverpool (the designated "home" team) and Real Madrid. xG figures are courtesy of FotMob.\n\n'


st.caption(caption)

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

for column in ['home_goals', 'away_goals', 'home_margin']:
    df_match_outcomes[column] = df_match_outcomes[column].astype(int)

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

df_match_outcomes['final_score'] = df_match_outcomes['home_goals'].apply(
    str) + ' - ' + df_match_outcomes['away_goals'].apply(str)

# st.write(df_match_outcomes)


number_of_sims_matching_actual_score = len(df_match_outcomes[(df_match_outcomes['home_goals'] == home_team_observed_goals) & (
    df_match_outcomes['away_goals'] == away_team_observed_goals)])
percentage_of_sims_matching_actual_score = number_of_sims_matching_actual_score / N_SIMS

df_grouped = df_match_outcomes[['match_outcome',
                                'home_goals']].groupby('match_outcome').count()
df_grouped.columns = ['count']
df_grouped = df_grouped.reindex(['Home win', 'Draw', 'Away win'])

df_grouped['proportion'] = df_grouped['count'] / df_grouped['count'].sum()

df_grouped['percentage'] = df_grouped['proportion'].astype(
    float).map("{:.1%}".format)

df_grouped = df_grouped[['percentage']]

simulated_home_win_percent = df_grouped.loc['Home win', 'percentage']
simulated_away_win_percent = df_grouped.loc['Away win', 'percentage']
simulated_draw_percent = df_grouped.loc['Draw', 'percentage']

st.header('Match outcomes')

# st.write(df_grouped)

outcome_colours = {
    'Home win': '#4dabf7',
    'Draw': '#ced4da',
    'Away win': '#f783ac'
}

fig, ax = plt.subplots()

sns.histplot(data=df_match_outcomes, x='home_margin', discrete=True,
             stat='density', hue='match_outcome', palette=outcome_colours, ax=ax, zorder=1, alpha=1, legend=False)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_ylabel('Density')  # , rotation=0)
ax.set_xlabel('Full Time Margin (Home Team Goals - Away Team Goals)')


plot_title = 'Home team ' + f'{sum(home_xg):.2f}' + \
    ' xG - Away team ' + f'{sum(away_xg):.2f}' + ' xG'

title = fig_text(x=0.05, y=1.2,
                 s='<' + plot_title + '>' + '\n\nActual outcome: Home team ' + f'{home_team_observed_goals:.0f}' + ' - Away team ' + f'{away_team_observed_goals:.0f}' + '\n\n<Home team wins> in ' + simulated_home_win_percent +
                 ' of simulations\n<Away team wins> in ' +
                 simulated_away_win_percent + ' of simulations\n<Match is drawn> in ' +
                 simulated_draw_percent + ' of simulations\nExact scoreline observed in ' +
                 f'{percentage_of_sims_matching_actual_score:.1%}' + ' simulations',
                 highlight_textprops=[
                     {"weight": "bold"}, {
                         "color": outcome_colours['Home win'], "weight": "bold"},
                     {"color": outcome_colours['Away win'],
                      "weight": "bold"},
                     {"color": outcome_colours['Draw'], "weight": "bold"}])


# fig.tight_layout()

st.pyplot(fig=fig)

df_possible_scores = df_match_outcomes[['final_score', 'home_margin', 'home_goals', 'match_outcome']].groupby(
    ['final_score', 'home_margin', 'match_outcome']).count().reset_index().sort_values('home_goals', ascending=False)
df_possible_scores.columns = ['final_score',
                              'home_margin', 'match_outcome', 'simulations']
df_possible_scores['percent'] = df_possible_scores['simulations'] / N_SIMS


fig, ax = plt.subplots(figsize=(5, 7))

g = sns.barplot(data=df_possible_scores, y='final_score', x='percent',
                hue='match_outcome', palette=outcome_colours, ax=ax, dodge=False)
g.legend_.remove()
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1, 0))

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(
    axis='y',     # changes apply to the y-axis
    which='both',  # both major and minor ticks are affected
    left=False
)
ax.set_ylabel('Match Score\n(Home Team - Away Team)')  # , rotation=0)
ax.set_xlabel('Percent of Simulations')

# fig.tight_layout()

st.pyplot(fig=fig)
