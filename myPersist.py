#!/usr/bin/python

import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime,timedelta
import pytz
import numpy as np
import pandas as pd
import matplotlib as mpl
import talib
import sys
import myVariables
import myLibrary
from Result import Result


baseStaticFiles='xxx'


def readHourly(ticker="SBUX",debug=False):
    readHourlyPickle(ticker,debug)

def readHourlyPickle(ticker):
    filePath = f'{baseStaticFiles}/1h-{ticker}.pkl'
    df=pd.read_pickle(filePath)
    df = df.iloc[::-1]
    #df = df.iloc[0:100]
    return df

def writeHourly(df,ticker="SBUX",debug=False):
    return writeHourlyInflux(df,ticker=ticker,debug=debug)

def writeHourlyInflux2(df,ticker="SBUX",debug=False,tz=myVariables.tz):
    #Input: open      high      low    close   volume

    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"
    print("Connect to db")
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=debug)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Check if tz-aware
    if "datetime64" not in str(df.index.dtype):
        print("The pd Dataframe index type is not datetime64")
        exit(1)
    elif "datetime64[ns," not in str(df.index.dtype):
        print("The pd Dataframe index type is not datetime64 TZ-aware")
        exit(1)
    else:
        print("The pd Dataframe index type IS datetime64 TZ-aware")


    full_json=[]
    for row_index, row in df.iterrows() :
        freq = "1h"
        #fieldvalue = row[2]
        json_body = {
                "time": row_index,
                "measurement": ticker,
                "tags": {
                            "freq": freq,
                            "kind": "open",
                            "flavour": "raw",
                            "tz":tz
                        },
                "fields": {
                            "open": row[0],
                }
        }
        full_json.append(json_body)
        json_body = {
                "time": row_index,
                "measurement": ticker,
                "tags": {
                            "freq": freq,
                            "kind": "high",
                            "flavour": "raw",
                            "tz":tz
                        },
                "fields": {
                            "high": row[1],
                }
        }
        full_json.append(json_body)
        json_body = {
                "time": row_index,
                "measurement": ticker,
                "tags": {
                            "freq": freq,
                            "kind": "low",
                            "flavour": "raw",
                            "tz":tz
                        },
                "fields": {
                            "low": row[2],
                }
        }
        full_json.append(json_body)
        json_body = {
                "time": row_index,
                "measurement": ticker,
                "tags": {
                            "freq": freq,
                            "kind": "close",
                            "flavour": "raw",
                            "tz":tz
                        },
                "fields": {
                            "close": row[3],
                }
        }
        full_json.append(json_body)
        json_body = {
                "time": row_index,
                "measurement": ticker,
                "tags": {
                            "freq": freq,
                            "kind": "volume",
                            "flavour": "raw",
                            "tz":tz
                        },
                "fields": {
                            "volume": row[4]
                }
        }
        full_json.append(json_body)
    ret = write_api.write(bucket, org, record=full_json,time_precision='s')
    if ret is not None: return ret
    return Result.ok()

def writeHourlyInflux(df,ticker="SBUX",debug=False,tz=myVariables.tz):
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=debug)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Check if tz-aware
    if "datetime64[ns," not in str(df.index.dtype):
        print('The pd Dataframe index type in writeHourlyInflux is not datetime64 TZ-aware')
        exit(1)

    freq = "1h"
    full_json=[]
    print(str(len(df)) + " lines to myPersist")
    for row_index, row in df.iterrows() :
        json_body = {
                "time": row_index,
                "measurement": ticker,
                "tags": {
                            "freq": freq,
                            "kind": "price",
                            "flavour": "raw",
                            "tz":tz
                        },
                "fields": {
                            "open": row[0],
                            "high": row[1],
                            "low": row[2],
                            "close": row[3],
                            "volume": row[4],
                }
        }
        full_json.append(json_body)
    ret = write_api.write(bucket, org, record=full_json,time_precision='s')
    if ret is not None: return ret
    return Result.ok()

def writeData(df,ticker,debug=False,kind="",flavour="",field="",tz=myVariables.tz,additional_tags=False):
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=debug)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    if kind == "" or flavour == "" or field == "":
        print(f'writeData field empty')
        return Result.error(f'writeData field empty')
    elif field not in df:
        print(f'writeData no field {field} on source dataframe')
        return Result.error(f'writeData no field {field} on source dataframe')
    # Numbers in influxDB are stored as floats
    # elif df[field].dtype != np.float:
    #     print(f'writeData Column {field} no in float type')
    #     return Result.error(f'writeData Column {field} no in float type')

    # Shorten dataframe in order to loop on row[O]
    df = df[[field]]

    # Check if tz-aware
    if "datetime64" not in str(df.index.dtype):
        print("The pd Dataframe index type is not datetime64")
        return Result.error([],msg="The pd Dataframe index type is not datetime64")
    elif "datetime64[ns," not in str(df.index.dtype):
        print("The pd Dataframe index type is not datetime64 TZ-aware")
        return Result.error([],msg="The pd Dataframe index type is not datetime64 TZ-aware")
    #else:
    #    print("The pd Dataframe index type IS datetime64 TZ-aware")

    full_json=[]
    print(str(len(df)) + " lines to myPersist")
    for row_index, row in df.iterrows():
        json_body = {
                "time": row_index,
                "measurement": ticker,
                "tags": {
                            "kind": kind,
                            "flavour": flavour,
                            "tz":tz,
                        },
                "fields": {
                            field: row[0],
                }
        }
        # Add additional_tags
        if additional_tags:
            for i in additional_tags:
                json_body['tags'][i]=additional_tags[i]
        # Append to global dict
        full_json.append(json_body)

    ret = write_api.write(bucket, org, record=full_json)
    if ret is not None: return ret
    return Result.ok()

def getLastRecords(ticker,since_date=None,freq="1hour"):
    if freq == "daily" or freq == "1d" or freq == "1day":
        freq="1d"
    elif freq == "hourly" or freq == "1h" or freq == "1hour":
        freq="1h"
    return getLastRecordsInflux(ticker,since_date,freq)

def getLastRecordsInflux(ticker,since_date=None,freq="1h"):
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=False)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    text_date = None
    if since_date is None:
        text_date = '-3y'
    else:
        # text_date = since_date.strftime('%Y-%m-%d')
        text_date = since_date.astimezone().isoformat()
        # 2021-04-16T15:00:00Z
    print(text_date)

    query= f'''
    from(bucket: "{bucket}")
    |> range(start:{text_date})
    |> filter(fn: (r) => r._measurement == "{ticker}")
    |> filter(fn: (r) => r.freq == "{freq}")
    |> filter(fn: (r) => r.kind == "price")
    |> filter(fn: (r) => r._field=="close")
    |> group(columns:["_measurement"])
    |> sort(columns: ["_time"], desc: false)
    |>last()
    '''
    df = client.query_api().query_data_frame(org=org, query=query)
    if df.empty:
        return Result.ok(df)
    df.drop(columns=['table', 'result','_start','_stop'],inplace=True)
    df.rename(columns={"_time": "date", "_value": "close"},inplace=True)
    df.set_index("date",inplace=True)
    df = myLibrary.applyTz(df)

    return Result.ok(df)

def getLastPositionHourly(ticker):
    return getLastPositionHourlyInflux(ticker)

def getLastPositionHourlyInflux(ticker):
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=False)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    query= f'''
    from(bucket: "{bucket}")
    |> range(start:-3y)
    |> filter(fn: (r) => r._measurement == "{ticker}")
    |> filter(fn: (r) => r.freq == "1h")
    |> filter(fn: (r) => r.kind == "position")
    |> group(columns:["_measurement"])
    |> sort(columns: ["_time"], desc: false)
    |>last()
    '''
    df = client.query_api().query_data_frame(org=org, query=query)
    if df.empty:
        return Result.ok(df)
    df.drop(columns=['table', 'result','_start','_stop'],inplace=True)
    df.rename(columns={"_time": "date", "_value": "position"},inplace=True)
    df['position']=df['position'].astype('float')
    df.set_index("date",inplace=True)
    df = myLibrary.applyTz(df)

    return Result.ok(df)

def getLastTrade(ticker,debug=False):
    return getLastTradeInflux(ticker,debug)

def getLastTradeInflux(ticker,debug=False):
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=debug)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    query= f'''
    from(bucket: "{bucket}")
    |> range(start:-3y)
    |> filter(fn: (r) => r._measurement == "{ticker}")
    |> filter(fn: (r) => r.flavour == "trade")
    |> group(columns:["_measurement"])
    |> sort(columns: ["_time"], desc: false)
    |>last()
    '''
    df = client.query_api().query_data_frame(org=org, query=query)
    if df.empty:
        return Result.ok(df)
    df.drop(columns=['table', 'result','_start','_stop'],inplace=True)
    df.rename(columns={"_time": "date", "_value": "qty"},inplace=True)
    df.set_index("date",inplace=True)
    df['remaining']=df['remaining'].astype('float')
    df = myLibrary.applyTz(df)

    return Result.ok(df)

def getLastBalance(debug=False):
    return getLastBalanceInflux(debug)

def getLastBalanceInflux(debug=False):
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=debug)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    query= f'''
    from(bucket: "{bucket}")
    |> range(start:-3y)
    |> filter(fn: (r) => r._measurement == "CONFIG")
    |> filter(fn: (r) => r.flavour == "config")
    |> sort(columns: ["_time"], desc: false)
    |>last()
    '''
    df = client.query_api().query_data_frame(org=org, query=query)
    if df.empty:
        return Result.ok(df)
    df.drop(columns=['table', 'result','_start','_stop'],inplace=True)
    df.rename(columns={"_time": "date", "_value": "balance"},inplace=True)
    df.set_index("date",inplace=True)
    #df['remaining']=df['remaining'].astype('float')
    df = myLibrary.applyTz(df)
    
    balance = df['balance'][0]

    return Result.ok(balance)

def getMeasurements(debug=False,less_than_one_hour=False):
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=debug)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    start_range = '3y'
    if less_than_one_hour:
        start_range = '1h'

    query= f'''
    from(bucket:"bucket1")
    |> range(start:-{start_range})
    |> filter(fn: (r) => r.kind == "price")
    |> group(columns:["_measurement"])
    |> distinct(column:"_measurement")
    '''
    df = client.query_api().query_data_frame(org=org, query=query)
    if df.empty:
        return Result.ok([])
    measurements = df['_measurement'].values
    measurements=np.delete(measurements, np.where(measurements == 'CONFIG'))
    return Result.ok(measurements)

def getData(ticker,from_datetime=None,kind=False,flavour=False,n=False,debug=False,field=False):
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    # You can generate a Token from the "Tokens Tab" in the UI
    token = "xxx"
    org = "org1"
    bucket = "bucket1"

    #print("Connect to db")
    client = InfluxDBClient(url="http://localhost:8086", token=token,debug=debug)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # from_datetime not provided
    if from_datetime is None:
        from_datetime = datetime.now(pytz.timezone(myVariables.tz)) - timedelta(days=3*365)

    # Compute filters
    filters=f'|> filter(fn: (r) => '
    if ticker != None:
        filters = filters + f'r._measurement == "{ticker}" and '
    if not kind and not flavour:
        print(f'error getData: no kind nor flavour')
        return Result.error(msg=f'error getData: no kind nor flavour')
    elif not kind:
        filters = filters + f'r.flavour == "{flavour}"'
    elif not flavour:
        filters = filters + f'r.kind == "{kind}"'
    else:
        filters = filters + f'r.flavour == "{flavour}" and r.kind == "{kind}"'
    filters=filters + ')'

    #Do we need just n last row ?
    lastRowsQuery=""
    if n:
        lastRowsQuery= f'''
    |>sort(columns: ["_time"])
    |>tail(n:{n})
    '''

    from_date = '-3y'
    if from_datetime != None:
        from_date = from_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    fieldQuery=""
    if field:
        fieldQuery = f'''
    |> filter(fn: (r) => r._field=="{field}")
    '''

    query= f'''
    from(bucket:"bucket1")
    |> range(start:{from_date})
    {filters}
    |> group(columns:["_measurement"])
    {fieldQuery}
    |> drop(columns: ["_start", "_stop","freq"])
    |> sort(columns: ["_time"], desc: false)
    {lastRowsQuery}
    '''
    #|> drop(columns: ["_start", "_stop","_field","_measurement","flavour","freq","kind"])

    df = client.query_api().query_data_frame(org=org, query=query)
    if df.empty:
        return Result.ok(df)

    #df.drop(columns=['table', 'result','_field','kind'],inplace=True)
    df.drop(columns=['table', 'result'],inplace=True)
    df.rename(columns={"_time": "date"},inplace=True)
    df.set_index("date",inplace=True)
    df = myLibrary.applyTz(df)

    #if len(df['_field'].unique()) == 1:
    #    field_name = df['_field'].unique()[0]
    #    df.rename(columns={"_value": field_name},inplace=True)

    return Result.ok(df)

