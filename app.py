import pandas as pd
import numpy as np
import streamlit as st

N_SIMS = 1000
SEED = 0

rng = np.random.default_rng(SEED)

n_shots_home = st.sidebar.number_input("Number of shots (home team)", 0, 30, 1)
rows_home = st.columns(n_shots_home)

n_shots_home = st.sidebar.number_input("Number of shots (away team)", 0, 30, 1)
rows_away = st.columns(n_shots_home)

home_shots_xg = []
away_shots_xg = []


for i, x in enumerate(rows_home):
    shot_xg = x.number_input(f"xG of home shot # {i+1}",min_value=0.01, max_value=0.99, step=0.01, key=i)
    home_shots_xg.append(shot_xg)

for i, x in enumerate(rows_away):
    shot_xg = x.number_input(f"xG of away shot # {i+1}",min_value=0.01, max_value=0.99, step=0.01, key=i)
    away_shots_xg.append(shot_xg)

# print(home_shots_xg)

home_goals = []
away_goals = []

for i in range(N_SIMS):
    for shot_xg in home_shots_xg:
        random = rng.random()
        if shot_xg >= random:
            outcome = 1
        else:
            outcome = 0
        home_goals.append(outcome)

for i in range(N_SIMS):
    for shot_xg in away_shots_xg:
        random = rng.random()
        if shot_xg >= random:
            outcome = 1
        else:
            outcome = 0
        away_goals.append(outcome)


mean_home_goals = np.mean(home_goals)
mean_away_goals = np.mean(away_goals)

st.text('home goals: ' + str(mean_home_goals))
st.text('away goals: ' + str(mean_away_goals))


