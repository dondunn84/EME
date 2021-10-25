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
    page = new_traceset.page()
    with open(page, "rb") as file:
         btn = st.download_button(
                 label="Download html",
                 data=file,
                 file_name="test.html",
                 mime="text/html"
         )
