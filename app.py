import pandas as pd
import numpy as np
import streamlit as st

n_shots_home = st.sidebar.number_input("Number of shots (home team)", 0, 30, 1)
rows_home = st.columns(n_shots_home)

n_shots_home = st.sidebar.number_input("Number of shots (away team)", 0, 30, 1)
rows_away = st.columns(n_shots_home)

home_shots_xg = []
away_shots_xg = []


for i, x in enumerate(rows_home):
    shot_xg = x.number_input(f"xG of home shot # {i}",min_value=0.01, max_value=0.99, step=0.01, key=i)
    home_shots_xg.append(shot_xg)

for i, x in enumerate(rows_away):
    shot_xg = x.number_input(f"xG of away shot # {i}",min_value=0.01, max_value=0.99, step=0.01, key=i)
    away_shots_xg.append(shot_xg)

print(home_shots_xg)