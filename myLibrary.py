#!/bin/python
import json
import myPersist
import pandas as pd
import datetime
from datetime import datetime,timedelta
import pytz
import myVariables,myLibrary
from Result import Result
import requests

def printWholeDataframe():
    pd.set_option("display.max_rows", None, "display.max_columns", None)

def getStockList():
    """
    Desc:     Get a list of tickers normalized names
    Input:    None
    Return:   ['AAPL', 'MSF.BR', 'MSFT', ... ]
    """
    return getStockList_fromJsonFile()

def getStockList_fromJsonFile(file=myVariables.json_stock_file):
    """
    Desc:     Get a list of tickers normalized names from a json file
    Input:    JSON file
    Return:   ['AAPL', 'MSF.BR', 'MSFT', ... ]
    """
    with open(file) as f:
        data = json.load(f)
        data = data[:100]
    res = [sub['symbol'] for sub in data]
    return Result.ok(res)

def checkPositionsFilled():
    ret = myPersist.getMeasurements()
    if not ret: return ret
    measurements=ret.value

    for ticker in measurements:
        ret = checkPositionsFilledByTicker(ticker)
        if not ret: return ret
        temp_filled = ret.value # Bool
        if not temp_filled: return Result.ok(False)

    return Result.ok(True)

def checkPositionsFilledByTicker(ticker):

    ret=myPersist.getLastRecords(ticker,freq="1h")
    if not ret: return ret
    last_data = ret.value

    if last_data.empty:
        print(f'No data for ticker {ticker}')
        return Result.error(last_data,msg=f'No data for ticker {ticker}')

    ret=myPersist.getLastPositionHourly(ticker)
    if not ret: return ret
    last_position = ret.value

    if last_position.empty:
        print('No positions for ticker '+ticker)
        return Result.ok(False)

    filled = True
    if last_data.index[0] != last_position.index[0]:
        print(f'WARNING: Positions for ticker {ticker} have to be filled !')
        filled = False
    return Result.ok(filled)

def checkPositionsUpToDate():
    ret = myPersist.getMeasurements()
    if not ret: return ret
    measurements=ret.value

    for ticker in measurements:
        ret = checkPositionsUpToDateByTicker(ticker)
        if not ret: return ret
        positions_uptodate_bool = ret.value
        if not positions_uptodate_bool:
            return Result.ok(False)
    return Result.ok(True)

def checkPositionsUpToDateByTicker(ticker):
    ret = getLastTradingHour()
    if not ret: return ret
    last_trading_hour = ret.value

    ret = myPersist.getLastPositionHourly(ticker)
    if not ret: return ret
    last_position = ret.value

    if last_position.empty:
        print(f'WARNING: No positions for ticker {ticker}')
        return Result.ok(False)
    #elif last_position.index[0] < last_trading_hour.replace(minutes=0,seconds=0):
    elif last_position.index[0] < last_trading_hour-pd.Timedelta(hour=1):
        print(f'WARNING: Positions for ticker {ticker} are outdated !')
        return Result.ok(False)
    return Result.ok(True)

def checkPricesAgeByTicker(ticker,delay_minutes=0,fromLastTradeHour=False):

    current_timezone = pytz.timezone(myVariables.tz)
    current_date = datetime.now(current_timezone)

    if fromLastTradeHour:
        ret = myLibrary.getLastTradingHour()
        if not ret: return ret
        #print(f'last Trading hour {ret.value}')
        current_date = ret.value

    ret = myPersist.getLastRecords(ticker,freq="1h")
    if not ret: return ret
    last_price = ret.value

    if last_price.empty:
        #print(f'WARNING: no prices for ticker {ticker}')
        return Result.ok('noprices',msg=f'No prices for ticker {ticker}')
    #elif last_price.index[0] < current_date-pd.Timedelta(minutes=delay_minutes):
    else:
        #print(f'last price : {last_price.index[0]} and current delayed price : {current_date-pd.Timedelta(minutes=delay_minutes)}')
        ret = hoursDiff(last_price.index[0],current_date-pd.Timedelta(minutes=delay_minutes))
        if not ret: return ret
        hours_since_last_price = ret.value
        #print(f'WARNING: last prices for ticker {ticker} are older than {delay_minutes}min ! Price is {last_price.index[0]} and we compare {current_date}')
        return Result.ok(hours_since_last_price)
    #return Result.ok(True)

def applyTz(df):
    if 'tz' not in df.columns:
        print("The Dataframe have not tz column. Exiting ...")
        exit(1)
    if not len(df['tz'].unique()) == 1:
        print("The Dataframe has different values for TZ column : " + df['tz'].unique() + "Exiting ...")
        exit(1)
    current_tz = df['tz'].unique()[0]

    # Check if tz-aware
    if "datetime64" not in str(df.index.dtype):
        print("WARNING : The pd Dataframe index type is not datetime64")
        df.index = pd.to_datetime(df.index).dt.tz_localize(tz=current_tz)
    elif "datetime64[ns," not in str(df.index.dtype):
        print("The pd Dataframe index type is not datetime64 TZ-aware")
        exit(1)
    #elif "datetime64[ns, tzutc()]" in str(df.index.dtype):
    elif 'datetime64[ns, US/Eastern]' not in str(df.index.dtype):
        #print("The pd Dataframe index type is datetime64 TZ-aware BUT UTC : Conversion")
        df.index = df.index.tz_convert(tz=current_tz)
    #else:
    #    print("The pd Dataframe index type IS datetime64 TZ-aware " + str(df.index.dtype) + " asked : " + current_tz)
    #    print("Doing nothing ....")

    #print("Now type is : " + str(df.index.dtype))
    df.drop(columns=['tz'],inplace=True)

    return df

def olderXHours(source_datetime,current_datetime=False,number=1):
    ret = hoursDiff(source_datetime,current_datetime)
    if not ret: return ret
    hoursDiff = ret.value
    print(f"{hours_diff} hours difference")
    return hours_diff >= number

def olderXDays(source_datetime,current_datetime=False,number=1):
    ret = hoursDiff(source_datetime,current_datetime)/24
    if not ret: return ret
    days_diff = ret.value
    print(f"{days_diff} days difference")
    return days_diff > number

def hoursDiff(source_datetime,current_datetime=False):
    current_timezone = pytz.timezone(myVariables.tz)
    temp_datetime = datetime.now(current_timezone)

    # Check if current_datetime have right TZ or initialize it to now
    if not current_datetime:
        current_datetime=temp_datetime
    elif current_datetime.tzinfo != temp_datetime.tzinfo:
        print(f"Error : Current TZ ({current_datetime.tzinfo}) not the right one define in vars ({temp_datetime.tzinfo}). Stoping ...")
        return Result.error(msg=f"Error : Current TZ ({current_datetime.tzinfo}) not the right one define in vars ({temp_datetime.tzinfo}). Stoping ...")

    # Check if source_datetime have right TZ or change it 
    if source_datetime.tzinfo != temp_datetime.tzinfo:
        source_datetime=source_datetime.replace(tzinfo=current_timezone)

    # Compute the hours delta using days and seconds from timeDelta object returned
    delta=current_datetime-source_datetime
    delta_days=delta.days
    delta_seconds=delta.seconds
    delta_hours=delta_days*24+delta_seconds/60/60

    return Result.ok(delta_hours)

def getLastTradingHour():
    current_timezone = pytz.timezone(myVariables.tz)
    current_datetime = datetime.now(current_timezone)

    modified = False
    if current_datetime.hour >= 15 and current_datetime.minute > 00:
        current_datetime = current_datetime.replace(hour=15,minute=00,second=0)
        modified = True
    elif current_datetime.hour <= 10 and current_datetime.minute <= 00:
        current_datetime = current_datetime.replace(hour=15,minute=00,second=0)- timedelta(days=1)
        modified = True

    if current_datetime.weekday() == 5: #Sat => Fri
        current_datetime = current_datetime.replace(hour=15,minute=00,second=0)
        current_datetime = current_datetime - timedelta(days=1)
        modified = True
    elif current_datetime.weekday() == 6: #Sun => Fri
        current_datetime = current_datetime.replace(hour=15,minute=00,second=0)
        current_datetime = current_datetime - timedelta(days=2)
        modified = True

    #if modified:
    #    print(f"Last trading datetime computed is {current_datetime.strftime('%d-%b-%Y (%H:%M:%S)')}")
    return Result.ok(current_datetime)