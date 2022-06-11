import pandas as pd
import numpy as np
import streamlit as st

N_SIMS = 1000
SEED = 0

rng = np.random.default_rng(SEED)

home_shots = st.text_input('xG of all home team shots (comma separated)')
away_shots = st.text_input('xG of all away team shots (comma separated)')

st.write(home_shots)
st.write(away_shots)