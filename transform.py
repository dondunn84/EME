import pandas as pd
from ast import literal_eval
from datetime import datetime

def string_to_timestamp(string):
    timestamp = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
    return timestamp

def tenth_dbuv_dbm(values):
    new_values = []
    for value in values:
        new_values.append(round(value/10 - 106.99, 1))
    return new_values

#def tenth_dbuv_dbm(value):
#    new_value = (value/10) - 106.99
#    return new_value

def crfs_msn_csv(df):
    new_df = pd.DataFrame()
    new_df['lvls'] = df['values']
    new_df['start_frq'] = df['start_frequency']
    new_df['stop_frq'] = df['end_frequency']
    new_df['step_frq'] = (df['end_frequency'][0] - df['start_frequency'][0])/len(df['values'])
    new_df['timestamp'] = df['timestamp'].apply(string_to_timestamp)
    new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms', utc=True)

    df = new_df.sort_values(by='timestamp', ascending=[True])
    df.lvls = df.lvls.apply(literal_eval)
    
    return df

def dons_app(df):
    new_df = pd.DataFrame()
    new_df['start_frq'] = df['frqfirststep']
    new_df['step_frq'] = df['stepfrqnumer']/df['stepfrqdenom']
    new_df['stop_frq'] = df['frqfirststep']+(len(df['levels'][0])*df['step_frq'][0])
    new_df['lvls'] = df['levels']
    new_df['lvls'] =  new_df['lvls'].apply(tenth_dbuv_dbm)
    new_df['timestamp'] = df['timestamp.$date']
    new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms', utc=True)
    
    df = new_df.sort_values(by='timestamp', ascending=[True])
    return df