import pandas as pd
import streamlit as st

ncol = st.sidebar.number_input("Number of xG instances", 0, 20, 1)
cols = st.beta_columns(ncol)

for i, x in enumerate(cols):
    x.selectbox(f"Input # {i}",[1,2,3], key=i)