import pandas as pd
from ast import literal_eval
from datetime import datetime
import xmltodict
import json
import numpy as np
import xml.etree.ElementTree as ET

def string_to_timestamp(string):
    timestamp = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
    return timestamp

def tenth_dbuv_dbm(values):
    new_values = []
    for value in values:
        new_values.append(round(value/10 - 106.99, 1))
    return new_values

def dbm_tenth_dbuv(values):
    new_values = []
    print(values[0])
    for value in values:
        new_values.append(np.int16((value + 107)*10))
    return new_values

def crfs_msn_csv(df):
    new_df = pd.DataFrame()
    df.values = df['values'].apply(literal_eval)
    new_df['lvls'] = df['values'].apply(dbm_tenth_dbuv)
    new_df['start_frq'] = df['start_frequency']
    new_df['stop_frq'] = df['end_frequency']
    new_df['step_frq'] = (df['end_frequency'][0] - df['start_frequency'][0])/len(df['values'])
    new_df['timestamp'] = df['timestamp'].apply(string_to_timestamp)
    new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms', utc=True)

    df = new_df.sort_values(by='timestamp', ascending=[True])
    
    
    return df

def dons_app(df):
    new_df = pd.DataFrame()
    new_df['start_frq'] = df['frqfirststep']
    new_df['step_frq'] = df['stepfrqnumer']/df['stepfrqdenom']
    new_df['stop_frq'] = df['frqfirststep']+(len(df['levels'][0])*df['step_frq'][0])
    new_df['lvls'] = df['levels']
    new_df['lvls'] =  new_df['lvls']
    new_df['timestamp'] = df['timestamp.$date']
    new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms', utc=True)
    
    df = new_df.sort_values(by='timestamp', ascending=[True])
    return df

def mlog(file):
            lines = file.readlines()
            lines.pop(3)
            lines.append("</RFLog>")
            line_string = ""
            for line in lines:
                line_string = line_string + line
            
            xml_dict = xmltodict.parse(line_string)
            json_data = json.dumps(xml_dict)
            json_data = json.loads(json_data)
            df = pd.json_normalize(json_data, record_path =['RFLog', 'RFSample'])
            df2 = pd.json_normalize(json_data)
            df['stop_frq'] = df2['RFLog.FreqRng.Max.@FreqHZ'][0]
            df['start_frq'] = df2['RFLog.FreqRng.Min.@FreqHZ'][0]
            df.rename(columns={'@TSize': 'num_datapoints', '#text': 'lvls', 'DTSpan.@STime': 'start_time', 'DTSpan.@ETime': 'stop_time'}, inplace=True)
            df['lvls'] = df['lvls'].str.split(',')
            for row in df.itertuples():
                i = 0
                for lvl in row.lvls:
                    row.lvls[i] = float(lvl)
                    i = i + 1
            #df['start_time'] = pd.to_datetime(df['start_time'], unit='ms', utc=True)
            df['lvls'] = df['lvls'].apply(dbm_tenth_dbuv)
            df['timestamp'] = pd.to_datetime(df['start_time'], format="%Y%m%d%H%M%S.%f")
            df = df.drop(columns=['start_time', 'stop_time', 'num_datapoints'])
            df['start_frq'] = pd.to_numeric(df['start_frq'],errors='coerce')
            df['stop_frq'] = pd.to_numeric(df['stop_frq'],errors='coerce')
            return df
