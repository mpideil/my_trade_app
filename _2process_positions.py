#!/bin/python
import json
from _1grab_data_folder import myDownload
from _2process_positions_folder import myStrategie,myReport
import myPersist
import pandas as pd
from datetime import datetime,timedelta
import pytz
import myVariables
import myLibrary
from Result import Result
import myAlert

def process(ticker,indicators_only=False,nb_pos=None,positions_debug=True): # TODO
    print(f' Computing positions for {ticker} ...')

    from_datetime = datetime.now(pytz.timezone(myVariables.tz)) - timedelta(days=90)
    
    # Getting stock points from start_date
    ret = myPersist.getData(ticker=ticker,kind='price',flavour='raw',from_datetime=from_datetime,field='close')
    if not ret: return ret
    data = ret.value

    if data.empty:
        print(f' data for ticker {ticker} empty ????')
        return Result.empty()
    
    data.rename(columns={"_value": 'close'},inplace=True)
    data.drop(columns=['_field','kind','flavour','_measurement'],inplace=True)

    ret = myStrategie.launch(data=data,indicators_only=indicators_only,debug=positions_debug)
    if not ret: return ret
    positions,data_with_indicators = ret.value

    return Result.ok([positions,data_with_indicators])

def main(tickers=None):
    print(f'===================== PROCESS POSITIONS ====================')
    if tickers is None:
        ret = myPersist.getMeasurements(less_than_one_hour=True)
        if not ret: return ret
        tickers=ret.value

    if len(tickers) == 0:
        ret = myAlert.stackAlertMessage(f'No data less than 1 hour for tickers')
        if not ret: return ret

    #tickers = ['SBUX','AAPL','NKE'] #test
    for ticker in tickers:
        print(f'Check data for {ticker}')

        ret = myPersist.getLastRecords(ticker,freq="1h")
        if not ret: return ret
        last_record = ret.value

        ret=myPersist.getLastPositionHourly(ticker)
        if not ret: return ret
        last_position = ret.value

        if last_record.empty:
            print(f' Prices empty for this ticker {ticker}. Skipping ...')
            return Result.ok() 
        elif not last_position.empty and last_record.index[0] == last_position.index[0] :
            print(f' All positions filled for ticker {ticker}. Skipping ...')
            return Result.ok()
        
        ret = myPersist.getLastRecords(ticker,since_date=last_position.index[0],freq=1h")
        if not ret: return ret
        last_records = ret.value
        prices_without_positions = len(last_records)
        # last_records is the prices recorded since last position
        if len(last_records) > 1:
            print(f'We need {prices_without_positions} positions')

        ret = process(ticker,nb_pos=prices_without_positions)
        if not ret: return ret
        positions,null = ret.value
        print(f' Persisting positions for {ticker} ...')
        additional_tags= {'freq':'1h','version':'1'}
        # Currently writing positions as float but must be changed to int by erasing all the measurement
        positions['position'] = positions['position'].astype('float')

        #positions=positions.head(1)

        ret = myPersist.writeData(positions,ticker=ticker,flavour="computed",kind="position",additional_tags=additional_tags,field='position')
        if not ret: return ret

    return Result.ok()

if __name__ == "__main__":
    main()