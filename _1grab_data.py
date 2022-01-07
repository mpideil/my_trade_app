#!/bin/python
import json
from _1grab_data_folder import myDownload
import myPersist
import pandas as pd
import datetime
from datetime import timedelta,datetime
import pytz
import myVariables
import myLibrary
from Result import Result
import myAlert

# Get all ticker from a list and keep DB up to date

yahoo_finance_calls = 0

def grab_data(ticker,freq="1hour"):
    res=pd.DataFrame()

    print(f'Check data for {ticker}')
    ret = myPersist.getLastRecords(ticker,freq=freq)
    if not ret: return ret
    last_record = ret.value

    #hours_since_last_record = -1
        #ret = myLibrary.hoursDiff(last_record.index[0],last_trading_hour)
        #if not ret: return ret
        #hours_since_last_record = ret.value
    ret = myLibrary.checkPricesAgeByTicker(ticker,delay_minutes=60,fromLastTradeHour=True)
    if not ret: return ret
    prices_age = ret.value
    
    if prices_age == 'noprices':
        print(f' No data for {ticker}')
        print(f' Init stocks counter with 0')
        df = pd.DataFrame({'date': [datetime.now(pytz.timezone(myVariables.tz))], 'buy': [0]})
        df['buy'] = df['buy'].astype('float')
        df = df.set_index('date')
        additional_tags= {'remaining':0}
        ret = myPersist.writeData(df,ticker=ticker,kind='buy',flavour="trade",additional_tags=additional_tags,field='buy')
        if not ret: return ret
        print(f'Downloading all data for {ticker}')
        ret = myDownload.get_data_all(ticker,freq=freq)
        if not ret: return ret
        res = ret.value
        if res.empty:
            return Result.ok(False)
    elif prices_age > 0:
        print(f' Data not up-to-date for {ticker}, age = {prices_age}. Downloading ...')
        ret = myDownload.get_data_latest(ticker,hours=prices_age,freq=freq)
        if not ret: return ret
        res = ret.value
        if res.empty:
            return Result.ok(False)
    else:
        print(f" Data OK for {ticker}")
        return Result.ok(False)

    print(f' persist data for {ticker}')
    return myPersist.writeHourly(res,ticker=ticker)

def main(tickers=None):
    print(f'===================== GRAB DATA ====================')
    if tickers is None:
        ret = myLibrary.getStockList()
        if not ret: return ret
        tickers = ret.value
    #tickers = ['SBUX','AAPL','NKE'] #test
    #tickers = ['JPM']
    for ticker in tickers:
        ret=grab_data(ticker=ticker)
        if not ret: return ret
    return Result.ok()

if __name__ == "__main__":
    main()
