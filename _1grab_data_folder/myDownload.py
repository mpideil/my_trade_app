import pandas as pd
import requests
import time
from os import path
import myVariables
from Result import Result
import yfinance as yf
import myAlert
import datetime
import pytz

def test_tiingo2():
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization' : f'Token {myVariables.datasource_dict["token"]}'
        }
        print(headers)
        url = f'https://api.tiingo.com/api/test/'
        res = requests.get(url,headers=headers)
    except:
        print('JSONDecodeError. Skipping ...')
        return Result.ok(pd.DataFrame([]))
    
    print(res.json())
    return Result.ok()

def get_data_all(ticker,freq="1h"):
    #return get_data_all_av(ticker)
    return get_data_all_tiingo(ticker)

def get_data_all_yf(ticker):
    ticker = yf.Ticker(ticker)
    #res = ticker.history(period="2d", interval="60m")
    try:
        res = ticker.history(period="2y", interval="60m")
    except JSONDecodeError:
        print('JSONDecodeError. Skipping ...')
        return Result.ok(pd.DataFrame([]))
    if res.empty:
        print('Empty data. Skipping ...')
        return Result.ok(res)

    #yahoo_finance_calls = yahoo_finance_calls + 1
    res.index = res.index.tz_convert(tz=myVariables.tz)

    if res.index[-1].minute != 30 and res.index[-1].second != 0:
        res = res[:-1]
    if res.index[-1].minute != 30 and res.index[-1].second != 0:
        print('Last element removed but still bad last element')
        return Result.error()

    #data_to_delete = res.loc[res['Volume'] == 0]
    return Result.ok(res)

def get_data_all_tiingo(ticker,freq):
    date_from = datetime.datetime.now(pytz.timezone(myVariables.tz))-pd.Timedelta(days=2*365)
    date_from = date_from.strftime('%Y-%m-%d')

    url = ""
    if freq == "1h" or freq == "1hour" or freq == "hourly":
        req_freq = "1hour"
        url = f'https://api.tiingo.com/iex/{ticker}/prices?columns=open,high,low,close,volume&startDate={date_from}&resampleFreq={req_freq}'
    elif: freq == "1d" or freq == "1day" or freq == "daily":
        url = f'https://api.tiingo.com/tiingo/daily/{ticker}/prices?columns=open,high,low,close,volume&startDate={date_from}'
 
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization' : f'Token {myVariables.datasource_dict["token"]}'
        }
        res = requests.get(url,headers=headers)
    except JSONDecodeError:
        print(f'JSONDecodeError. Skipping ...')
        myAlert.stackAlertMessage(f'Error: getting history {ticker} JSONDecodeError')
        return Result.ok(pd.DataFrame([]))
    if res.status_code != 200:
        print(f'{res.status_code} http code. Skipping ...')
        myAlert.stackAlertMessage(f'Error: getting history {ticker} HTTPStatusCode {res.status_code}')
        return Result.ok(pd.DataFrame([]))
    
    stockprices = pd.DataFrame(res.json())
    if stockprices.empty:
        print('Error: data empty')
        myAlert.stackAlertMessage(f'Error: empty history {ticker}')
        return Result.ok(stockprices)

    stockprices['date'] = pd.to_datetime(stockprices['date']).dt.tz_convert(myVariables.tz)
    stockprices.set_index('date',inplace=True)

    return Result.ok(stockprices)

def get_data_all_av(ticker):
    api_key = 'xxxx'
    res = pd.DataFrame()
    count=0
    #for i in ['year1month1','year1month2','year1month3','year1month4','year1month5','year1month6','year1month7','year1month8','year1month9','year1month10','year1month11','year1month12','year2month1','year2month2','year2month3','year2month4','year2month5','year2month6','year2month7','year2month8','year2month9','year2month10','year2month11','year2month12']:
    for i in ['year1month1']:
        print("Downloading ticker "+ticker+" slice "+i+" ...")
        # stockprices = pd.read_csv(f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&symbol=AAPL&interval=60min&slice=year1month2&apikey=1X5VS10ZQI93ROP8')
        stockprices = pd.read_csv(f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&symbol={ticker}&interval=60min&slice={i}&apikey={api_key}')
        if 'close' in stockprices.columns:
            res=res.append(stockprices,ignore_index=True)
            count=0
        else:
            if count == 5:
                print("5 times 30s without correct answer. Exiting...")
                exit(1)
            else:
                print("Retrying in 30s")
                count=count+1
                time.sleep(30)
    # Add TZ to data
    res['time'] = pd.to_datetime(res['time']).dt.tz_localize(tz=myVariables.tz)
    res=res.set_index('time')
    return Result.ok(res)

def get_data_latest(ticker,hours=24,freq="1h"):
    return get_data_latest_tiingo(ticker,hours,freq)

def get_data_latest_yf(ticker,hours=24):
    ticker_obj = yf.Ticker(ticker)
    try:
        res = ticker_obj.history(period=f'{hours}h', interval="60m")
    except JSONDecodeError:
        print('JSONDecodeError. Skipping ...')
        myAlert.stackAlertMessage(f'Error: getting history {ticker}')
        return Result.ok(pd.DataFrame([]))

    if res.empty:
        print(f' Empty data for ticker {ticker}')
        myAlert.stackAlertMessage(f'Error: empty history {ticker}')
        return Result.ok(res)

    #yahoo_finance_calls = yahoo_finance_calls + 1
    res.index = res.index.tz_convert(tz=myVariables.tz)
    if res.index[-1].minute != 30 and res.index[-1].second != 0:
        if len(res) > 2:
            res = res[:-1]
        else:
            myAlert.stackAlertMessage(f'Error: too short history {ticker}')
            myAlert.stackAlertMessage(f' debug : {res}')
            #myAlert.stackAlertMessage(res)
            print(f'problem: latest data downloaded are too short :')
            print(res)
            return Result.warn(res,msg=f'problem: latest data downloaded are too short')
    if res.index[-1].minute != 30 and res.index[-1].second != 0:
        print('Last element removed but still bad last element')
        return Result.error()
    return Result.ok(res)

def get_data_latest_av(ticker):
    api_key = 'xxxx'
    quandl='xxxx'
    marketstack='xxxx'
    res = pd.DataFrame()
    count=0
    print("Downloading ticker "+ticker+" latest data ...")
    stockprices = pd.read_csv(f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=60min&apikey={api_key}&datatype=csv')
    print(stockprices.head())
    if 'close' in stockprices.columns:
        res=res.append(stockprices,ignore_index=True)
        count=0
    else:
        if count == 5:
            print("5 times 30s without correct answer. Exiting...")
            return Result.error(msg="5 times 30s without correct answer. Exiting...")
        else:
            print("Retrying in 30s")
            count=count+1
            time.sleep(30)
    # Add TZ to data
    res['timestamp'] = pd.to_datetime(res['timestamp']).dt.tz_localize(tz=myVariables.tz)
    res=res.set_index('timestamp')
    return Result.ok(res)

def get_data_latest_tiingo(ticker,hours,freq='1h'):
    # Must return   date(index),open,high,low,close,volume

    date_from = datetime.datetime.now(pytz.timezone(myVariables.tz))-pd.Timedelta(hours=hours)
    date_from = date_from.strftime('%Y-%m-%d')

    url = ""
    if freq == "1h" or freq == "1hour" or freq == "hourly":
        req_freq = "1hour"
        url = f'https://api.tiingo.com/iex/{ticker}/prices?columns=open,high,low,close,volume&startDate={date_from}&resampleFreq={req_freq}'
    elif: freq == "1d" or freq == "1day" or freq == "daily":
        url = f'https://api.tiingo.com/tiingo/daily/{ticker}/prices?columns=open,high,low,close,volume&startDate={date_from}'

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization' : f'Token {myVariables.datasource_dict["token"]}'
        }
        res = requests.get(url,headers=headers)
    except JSONDecodeError:
        print(f'JSONDecodeError. Skipping ...')
        myAlert.stackAlertMessage(f'Error: getting history {ticker} JSONDecodeError')
        return Result.ok(pd.DataFrame([]))
    if res.status_code != 200:
        print(f'{res.status_code} http code. Skipping ...')
        myAlert.stackAlertMessage(f'Error: getting history {ticker} HTTPStatusCode {res.status_code}')
        return Result.ok(pd.DataFrame([]))

    stockprices = pd.DataFrame(res.json())
    if stockprices.empty:
        print('Error: data empty')
        myAlert.stackAlertMessage(f'Error: empty history {ticker}')
        return Result.ok(stockprices)

    stockprices['date'] = pd.to_datetime(stockprices['date']).dt.tz_convert(myVariables.tz)

    stockprices.set_index('date',inplace=True)
    return Result.ok(stockprices)

if __name__ == "__main__":
    print('dont call directly that file')
    #exit(1)
