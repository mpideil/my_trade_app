#!/bin/python
import json
import _2process_positions
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
import numpy as np

def main(tickers=None):
    print(f'===================== GENERATE REPORT ====================')
    #myLibrary.printWholeDataframe()

    if tickers is None:
        ret = myPersist.getMeasurements(less_than_one_hour=False)
        if not ret: return ret
        tickers=ret.value

    if len(tickers) == 0:
        ret = myAlert.stackAlertMessage(f'No data less than 1 hour for tickers')
        if not ret: return ret

    #tickers = ['SBUX','AAPL','NKE'] #test
    #tickers=['JPM','SBUX','AAPL']
    #tickers=['SBUX']
    df_prices=pd.DataFrame()
    #df_strategy_local=pd.DataFrame()
    df_strategy_computed=pd.DataFrame()
    #df_strategy_real=pd.DataFrame()

    for ticker in tickers:
        print(f'Check data for {ticker}')
        draw_ticker_and_local_positions(ticker,report_title=ticker)
        myReport.showGraph()
        exit()
        # ret = draw_strategies(ticker=ticker,local=False,computed=True,real=False,draw=False)
        # if not ret and ret.empty: continue
        # elif not ret: return ret
        # res=ret.value
        # df_prices[ticker]=res['nostrat']
        # #df_strategy_local[ticker]=res['strategy_local']
        # df_strategy_computed[ticker]=res['strategy_computed']
        # #df_strategy_real[ticker]=res['strategy_real']
    
    df_total=pd.DataFrame(index=df_prices.index)
    df_total['nostrat']=df_prices.mean(axis=1)
    #df_total['strategy_local']=df_strategy_local.mean(axis=1)
    df_total['strategy_computed']=df_strategy_computed.mean(axis=1)
    #df_total['n']=df_strategy_computed.notna().sum(axis=1)

    returns=df_total
    draw=True
    if draw:
        returns_filled=returns.fillna(0)
        temp = returns_filled.cumsum().apply(np.exp)
        ret = myReport.plotCharts(temp)
        if not ret: return ret
        myReport.showGraph()

    return Result.ok()

if __name__ == "__main__":
    main()