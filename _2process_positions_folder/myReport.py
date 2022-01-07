#!/usr/bin/python

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import talib
import sys
import json

from Result import Result
from _2process_positions_folder import myStrategie,myReport
from _1grab_data_folder import myDownload
import myPersist
import myVariables
import myLibrary

import datetime
#from datetime import timedelta,datetime
import pytz

import seaborn as sns
sns.set()

def printAll(bol,macd,posDbg,pos,scatter1,scatter2):
    #plt.figure(figsize=(20,7))
    fig,ax = plt.subplots(4, 1, gridspec_kw={'height_ratios': [7, 1, 1, 1]},sharex=True,figsize=(20,7))

    #Add position time
    bol['positioned']=np.where(pos['posFinal'] == 1,bol['close'].max(),0)
    bol.plot(ax=ax[0])
    ax[0].legend(fontsize='xx-small',loc='upper left')
    ax[0].fill_between(bol.index, bol['bolu'], bol['boll'], facecolor='orange', alpha=0.1)
    ax[0].fill_between(bol.index, 0, bol['positioned'], facecolor='blue', alpha=0.1)
    ax[0].scatter(scatter1, bol.loc[scatter1,'close'], color='r',marker='^')
    ax[0].scatter(scatter2, bol.loc[scatter2,'close'], color='b',marker='v')

    macd.plot(ax=ax[1])
    ax[1].legend(fontsize='xx-small',loc='upper left')
    ax[1].fill_between(macd.index, macd['MACDsig'], macd['MACD'], facecolor='red', alpha=0.2)
    ax[1].bar(macd.index, macd['MACDhist'].fillna(0), width=0.5, snap=False)

    posDbg.plot(ax=ax[2])
    ax[2].legend(fontsize='xx-small',loc='upper left')

    pos.plot(ax=ax[3])
    ax[3].legend(fontsize='xx-small',loc='upper left')
    plt.tight_layout()

    #if png:
    #    plt.savefig('apple.png', bbox_inches='tight')
    #else:
    #    plt.show()

def computeReturns(data,position):
    ## Compute returns
    data['bullish'] = np.where(data['sma1'] >= data['sma2'],2.0,0.5)
    data['returns'] = np.log(data['close'] / data['close'].shift(1))
    #data['returns'].hist(bins=35,figsize=(10, 6))
    data['strategy'] = position['posFinal'].shift(1) * data['returns']
    #data[['returns', 'strategy']].sum()
    #data[['returns', 'strategy']].sum().apply(np.exp)
    test=data[['returns', 'strategy']].cumsum().apply(np.exp).copy()
    test['bullish']=data['bullish'].copy()
    #data[['returns', 'strategy']].cumsum().apply(np.exp).plot(figsize=(10, 6))
    
    axtest=test.plot(figsize=(10, 6))
    axtest.fill_between(test.index, 0, test['bullish'], facecolor='red', alpha=0.2)
    
    
    plt.tight_layout()    

def showGraph():
    plt.show()

def globalReport():
    total_with_trades = 0
    total_without_trades = 0
    total_long = 0

    two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2*365)
    ret = myPersist.getData(ticker=None,flavour='trade',from_datetime=None)
    if not ret: return ret
    trades = ret.value
    if trades.empty:
        return Result.error(msg='Empty data trades')

    tickers = trades['_measurement'].unique()

    for ticker in tickers:
        data = trades.loc[trades['_measurement'] == ticker]
        # Avoid last bugfix trade to be removed
        if data.iloc[-1]['remaining'] != '0' and data.iloc[-1]['kind'] == 'fakebuy' and data.iloc[-1]['_value'] == 0.0 :
            x = data.iloc[-1]
            data = data.loc[data['_value'] != 0.0]
            data = data.append(x)
        else:
            data = data.loc[data['_value'] != 0.0]

        if data.empty:
            total_without_trades = total_without_trades + 1
            #print(f'no trades on {ticker}')
        elif data.iloc[-1]['remaining'] != '0':
            #print(f'long on {ticker}')
            total_with_trades = total_with_trades + 1
            total_long = total_long + 1
        else:
            total_with_trades = total_with_trades + 1
            #print(f'out on {ticker}')

    ret = myPersist.getMeasurements(less_than_one_hour=False)
    if not ret: return ret
    tickers_total = ret.value

    ret = myPersist.getMeasurements(less_than_one_hour=True)
    if not ret: return ret
    tickers_uptodate = ret.value


    print(f'We monitor a total of {len(tickers_total)} tickers :')
    print(f'{len(tickers_uptodate)} are uptodate')
    print(f'{total_with_trades} had a trade')
    print(f'{len(tickers_total)- total_with_trades} never had any trade')
    print(f'{total_long} are still long')
    #pdb.set_trace()
    return Result.ok()

def createReport(ticker):
    
    plt.style.use('seaborn')
    mpl.rcParams['savefig.dpi'] = 300
    mpl.rcParams['font.family'] = 'serif'

    ret = myPersist.getData(ticker=ticker,kind='price',flavour='raw',from_datetime=None,field='close')
    if not ret: return ret
    data = ret.value

    if data.empty:
        print(f'ticker {ticker} as no value')
        return Result.ok(data)

    data.rename(columns={"_value": "close"},inplace=True)
    data.drop(columns=['_field','kind','flavour','_measurement'],inplace=True)

    if data.empty:
        print(' DATA FOR TICKER {ticker} EMPTY ????')
        return Result.ok()

    # Compute needed indicators
    data = myStrategie.computeSma(data,20,50)
    print(data)
    data = myStrategie.computeBollinger(data,20,20)
    print(data)
    macd = myStrategie.computeMACD(data, 12, 26, 9)
    print(macd)
    exit()

    return Result.ok(df)

def main():
    #ret = globalReport()
    #if not ret: return ret

    process_position(ticker='AAPL',report=False,write_positions=True)

    ret = myPersist.getMeasurements(less_than_one_hour=False)
    if not ret: return ret
    tickers=ret.value
    #tickers = ['SBUX','AAPL','NKE'] #test

    #fig,ax = plt.subplots(10, 10, gridspec_kw={'height_ratios': [7, 1, 1, 1]},sharex=True,figsize=(20,7))
    fig,ax = plt.subplots(10, 10,figsize=(20,7))

    i=0
    j=0
    local_ax=None
    df_global = pd.DataFrame([1,2,3,5,9])
    for ticker in tickers:
        ret = createReport(ticker)
        if not ret: return ret
        df = ret.value
        if df.empty:
            continue
        print(f'i : {i} , j : {j}')
        #df_global.plot(ax=ax[i,j])
        df.plot(ax=ax[i,j])
        if i == 9:
            if j==9:
                break
            else:
                j=j+1
                i=0
        else:
            i=i+1

        #df_global = pd.concat([df_global, df], axis=1)

    #df_global.plot()
    print("end")
    plt.show()
    return Result.ok()

if __name__ == "__main__":
    main()

def plotCharts(charts):
    """
    Input : charts must be indexed by datetime and have as many column as you want graphs to be plotted
    """
    ax=charts.plot()
    ax.legend(fontsize='xx-small',loc='upper left')
    plt.tight_layout()
    return Result.ok(ax)

def plotPositions(prices,positions,additional_indicator,report_title=None):
    scatter1 = positions.loc[positions['tics'] == 1].index
    scatter2 = positions.loc[positions['tics'] == -1].index
    #print('scatter1')
    #print(scatter1)
    #exit()

    if type(additional_indicator) != type(pd.DataFrame()):
        additional_indicator = False

    bollinger=False
    if 'bolu' in prices and 'boll' in prices:
        bollinger=True

    #plt.figure(figsize=(20,7))
    subplots_number = 2
    height_ratios = [7, 1]

    if additional_indicator is not None:
        subplots_number = 3
        height_ratios = [7, 1, 1]

    fig,ax = plt.subplots(subplots_number, 1, gridspec_kw={'height_ratios':height_ratios },sharex=True,figsize=(20,7))
    if report_title is not None:
        fig.suptitle(report_title, fontsize=16)

    #Add position time
    #bol['positioned']=np.where(pos['posFinal'] == 1,bol['close'].max(),0)
    prices.plot(ax=ax[0])
    ax[0].legend(fontsize='xx-small',loc='upper left')
    if bollinger:
        ax[0].fill_between(prices.index, prices['bolu'], prices['boll'], facecolor='orange', alpha=0.1)
    #ax[0].fill_between(main_data.index, 0, bol['positioned'], facecolor='blue', alpha=0.1)
    # ax[0].scatter(scatter1, prices.loc[scatter1,'close'], color='b',marker='^')
    # ax[0].scatter(scatter2, prices.loc[scatter2,'close'], color='r',marker='v')
    ax[0].scatter(scatter1, prices.loc[scatter1,'close'], color='b',marker='^')
    ax[0].scatter(scatter2, prices.loc[scatter2,'close'], color='r',marker='v')


    if additional_indicator is not None:
        additional_indicator[['MACD','MACDsig']].plot(ax=ax[1])
        ax[1].legend(fontsize='xx-small',loc='upper left')
        ax[1].fill_between(additional_indicator.index, additional_indicator['MACD'], additional_indicator['MACDsig'], facecolor='red', alpha=0.2)
        #ax[1].bar(additional_indicator.index, additional_indicator['MACDhist'].fillna(0), width=0.1, snap=False,linewidth=0)
        #ax[1].bar(additional_indicator.index, additional_indicator['MACDhist'].fillna(0))
        ax[1].fill_between(additional_indicator.index, additional_indicator['MACDhist'], 0, facecolor='blue', alpha=0.5)
    # positions.plot(ax=ax[2])
    # ax[2].legend(fontsize='xx-small',loc='upper left')
    
    plt.tight_layout()

def draw_report(prices,positions,additional_indicator,report_title):
    """
    Inputs
        - prices :  (date),                         close       sma1      sma2        bolu        boll      MACD   MACDsig  MACDhist
                    2021-04-14 11:00:00-04:00  133.330000  132.70500  129.7755  135.113759  130.296241  1.206786  1.291221 -0.084435
        - positions : (date),                  signal  bullish  reintegration  position  ready_to_sell    stoploss
                    2021-04-14 11:00:00-04:00       0        1              1         0              0  119.675003
        - additional_indicator :    (date)                         MACD   MACDsig  MACDhist
                                    2021-04-14 10:00:00-04:00  1.296462  1.312330 -0.015868
    """

    #get tics for markers buy/sell

    if not 'tics' in positions:
        positions['tics'] = 0
        for i in range(1, len(positions)):
            if positions['position'].values[i-1] == 0 and positions['position'].values[i] == 1:
                positions['tics'].values[i] = 1
            elif positions['position'].values[i-1] == 1 and positions['position'].values[i] == 0:
                positions['tics'].values[i] = -1

    print(prices)
    ret = plotPositions(prices,positions,additional_indicator,report_title=report_title)

    return Result.ok()