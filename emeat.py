import streamlit as st
import msn_chart2
from transform import crfs_msn_csv as cmcsv
import pandas as pd

st.title("EME Analysis Tool, HTML Creator")


csv_upload = st.file_uploader("Use Mission CSV")
if csv_upload:
    df = pd.read_csv(csv_upload)
    df = cmcsv(df)
    new_traceset = msn_chart2.TraceSet(df, 100)
    new_traceset.page()