import streamlit as st
import msn_chart2
from transform import crfs_msn_csv as cmcsv
from transform import mlog
import pandas as pd
import bokeh.io.output
#import os

#path = os.path.dirname(__file__)

st.title("EME Analysis Tool, HTML Creator")

file_type = st.selectbox("File Type", ["Mission CSV", "MANCAT MLog"])

if file_type == "Mission CSV":
    file_upload = st.file_uploader("Use Mission CSV")
    if file_upload:
        df = pd.read_csv(file_upload)
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
                
elif file_type == "MANCAT MLog":
    file_upload = st.file_uploader("Use MANCAT MLog")
    if file_upload:
        df = mlog(file_upload)
        new_traceset = msn_chart2.TraceSet(df, 100)
        page = new_traceset.page()
        with open(page, "rb") as file:
             btn = st.download_button(
                     label="Download html",
                     data=file,
                     file_name="test.html",
                     mime="text/html"
             )
