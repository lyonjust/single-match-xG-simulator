import pandas as pd
import streamlit as st

n_shots_home = st.sidebar.number_input("Number of shots (home team)", 0, 30, 1)
rows_home = st.columns(n_shots_home)

n_shots_home = st.sidebar.number_input("Number of shots (away team)", 0, 30, 1)
rows_away = st.columns(n_shots_home)

for i, x in enumerate(rows_home):
    x.number_input(f"xG of home shot # {i}",min_value=0, max_value=1, step=0.01, key=i)

for i, x in enumerate(rows_away):
    x.number_input(f"xG of away shot # {i}",min_value=0, max_value=1, step=0.01, key=i)