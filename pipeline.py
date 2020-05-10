import pandas as pd
import numpy as np
import pandas as pd
import mysql.connector
from tqdm import tqdm
import h5py
from sqlalchemy import types, create_engine 
import os
from os import listdir
from os.path import isfile, join
import config
import time


def get_files_list(): # gets list of filepath strings in ~/data
    mypath = os.getcwd()+'/data/'
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for f in files:
        f = mypath+f # append full path for h5py loading
    files = list(map(lambda f: mypath+f, files))
    return files 

def process_orbit(h5): # filename string. adds h5's observations to dataframe
    # the formatting/array shape is all uniform. thanks, NASA
    f = h5py.File(h5, 'r') # read file
    geo = f['GEOLOCATION_DATA'] # h5 Groups architecture is similar to dict
    sci = f['SCIENCE_DATA']
    # hdf.Datasets -> np.array -> flatten -> list. faster than looping through each matrix
    lat = list(geo['Latitude'].value.ravel())
    long = list(geo['Longitude'].value.ravel()) # is there a less verbose way to do this?
    sat_lat = list(geo['SpacecraftLatitude'].value.ravel())*36 # extend the 1d arrays
    sat_long = list(geo['SpacecraftLongitude'].value.ravel())*36 # don't forget to ravel like i did
    sat_alt = list(geo['SpacecraftAltitude'].value.ravel())*36
    time = list(geo['TimeUTC'].value.ravel())*36 # 36 measurements per position means one "time" value for every consecutive 36 measurements
    sza = list(geo['SolarZenithAngle'].value.ravel())
    pbl = list(sci['ColumnAmountSO2_PBL'].value.ravel())
    anom = list(sci['Flag_SAA'].value.ravel())
    volc = list(sci['Flag_SO2'].value.ravel())
    # combine lists into df
    new = pd.DataFrame(list(zip(lat, long, sat_lat, sat_long, sat_alt, time, sza, pbl, anom, volc)),
                       columns=["lat", "long", "sat_lat", "sat_long", 
                                'sat_alt', "time", "sza", "pbl", "anom", 'volc'])
    new['time'] = new['time'].astype(str) # change time format
    new['time'] = new['time'].apply(lambda st: st[2:12]+' '+st[13:21]) # slice relevant parts
    return new # returns new df with the h5's 11k rows

def make_vars(): # create connection to server
    user = config.user # substitute your own username, password & SQL server host + db name
    pw = config.pw
    host = config.host
    db = config.db
    connst = f'mysql+pymysql://{user}:{pw}@{host}.clqqz5nrghvl.us-east-1.rds.amazonaws.com/{db}'
    engine = create_engine(connst, echo=False) # don't set pool_recycle
    return engine

def process_h5s(files, engine): # filepath strings, sqlalchemy engine
    # loads all h5s into dataframes -> uploads to SQL
    # to keep track of progress
    for f in tqdm(files): # this took 18 hours for 40,000 11k-length h5 files on my laptop
        df = process_orbit(f)
        df.to_sql('so2', con=engine, if_exists='append') # sqlalchemy takes care of sessions, commits etc rather nicely
    return 

# ------------------------------- Run

print('establishing engine...')
engine = make_vars() # establish connection to server
files = get_files_list() # get filepath strings
print(f'processing {len(files)} files...')
process_h5s(files, engine) # process each file & upload to server










