#!/bin/python
import json
from _1grab_data_folder import myDownload
from _2process_positions_folder import myStrategie,myReport
import pandas as pd
from datetime import datetime,timedelta
import pytz
import myPersist
import myVariables
import myLibrary
from Result import Result
import requests
import time
import myAlert

#import logging
#logging.basicConfig(level=logging.DEBUG)

# Get all ticker from local measurements and for each get positions and apply them if possible

alpaca_calls = 0

def apiCallApca(path,paper=False,data=False):
    api_url=myVariables.api_apca_url
    api_id=myVariables.api_apca_id
    api_secret=myVariables.api_apca_secret
    if paper:
        api_url=myVariables.api_apca_paper_url
        api_id=myVariables.api_apca_paper_id
        api_secret=myVariables.api_apca_paper_secret

    path=f'{api_url}{path}'
    response=False
    if data:
        data['qty'] = str(data['qty']) #int not serializable
        response = requests.post(path,
            json=data,
            headers= {
                "APCA-API-KEY-ID": api_id,
                "APCA-API-SECRET-KEY": api_secret,
            }
        )
    else:
        response = requests.get(path,
            headers= {
                "APCA-API-KEY-ID": api_id,
                "APCA-API-SECRET-KEY": api_secret
            }
        )
    if not response:
        return Result.error(msg='Request returned an error.',value=response.text)
    #alpaca_calls = alpaca_calls + 1
    return Result.ok(response.json())

def getPositions(paper):
    return getPositionsApca(paper)

def getPositionsApca(paper):
    ret=apiCallApca(path='/v2/positions',paper=paper)
    if not ret: return ret
    res = ret.value
    df1 = pd.DataFrame([])
    if res is not None and len(res) != 0:
        df1 = pd.DataFrame(res)[['symbol','qty', 'side','market_value']]
        #df1 = pd.DataFrame(res, index =['symbol'], columns =['symbol','qty', 'side','market_value'])
        df1.set_index('symbol',inplace=True)

    return Result.ok(df1)

def getBalance(paper):
    # Get balance
    ret = getBalanceApca(paper)
    if not ret: return ret
    balance = ret.value
    ret = myAlert.stackAlertMessage(f'New balance: {balance}')
    if not ret: return ret
    # Prepare data to myPersist
    current_timezone = pytz.timezone(myVariables.tz)
    date_today = datetime.now(current_timezone)
    date_array=[date_today]
    balance_array=[balance]
    df = pd.DataFrame({'date': date_array, 'balance': balance_array})
    df['balance'] = df['balance'].astype('float')
    df = df.set_index('date')
    return myPersist.writeData(df,"CONFIG",kind="config",flavour="config",field='balance')

def getBalanceApca(paper):
    ret=apiCallApca(path='/v2/account',paper=paper)
    if not ret: return ret
    res = ret.value
    balance=res['cash']
    return Result.ok(balance)

def waitOrdersPassed(paper):
    count = 0
    orders_empty = False
    orders_value = None

    print(f' Waiting 3 seconds before check orders status ...')
    time.sleep(3)

    while not orders_empty:
        if count == 5:
            print(f' 5 times 5s without order being passed. Exiting...')
            print(f' Stuck order is : {orders_value}')
            return Result.error(msg='order stuck')
        else:
            ret = getOrders(paper)
            if not ret: return ret
            orders_value = ret.value
            if orders_value.empty:
                print(f'Order passed !')
                ret = myAlert.stackAlertMessage(f'Order passed')
                if not ret: return ret
                orders_empty = True
            else:
                print(f' Waiting for order to be passed, retrying in 5 seconds ...')
                count=count+1
                time.sleep(5)
    return Result.ok()

def getOrders(paper):
    return getOrdersApca(paper)

def getOrdersApca(paper):
    ret = apiCallApca(path='/v2/orders',paper=paper)
    if not ret: return ret
    res = ret.value

    if len(res) == 0:
        return Result.ok(pd.DataFrame([]))
    df1 = pd.DataFrame(res, columns =['symbol','qty', 'side','filled_qty','order_type','status'])
    df1.set_index('symbol',inplace=True)
    return Result.ok(df1)

def setOrder(paper,ticker,qty,side='buy',type='market',test=True):
    # Testing parameters setOrder
    if side not in {'buy','sell'}:
        print('error: side must be buy or sell')
        exit(1)
    if test:
        print(f'Passing FAKE order : paper={paper},ticker={ticker},qty={qty},side={side},type={type}')
        return Result.ok(True)
    print(f" Info : Setting {side} order for {ticker}")
    current_timezone = pytz.timezone(myVariables.tz)
    date_today = datetime.now(current_timezone)
    date_array=[date_today]
    qty_array=[qty]
    df = pd.DataFrame({'date': date_array, side: qty_array})
    df[side] = df[side].astype('float')
    df = df.set_index('date')
    # Setting order
    ret = setOrderApca(paper,ticker,qty,side=side,type='market')
    if not ret: return ret
    # myPersisting order data
    ret = getLocalOpenPositionByTicker(ticker)
    if not ret: return ret
    local_positions = ret.value
    stocks_owned = 0
    if not local_positions.empty:
        stocks_owned = local_positions['qty'][0]
    if side == "buy": stocks_owned=stocks_owned+qty
    elif side == "sell": stocks_owned=stocks_owned-qty
    additional_tags= {'remaining':stocks_owned}
    ret = myPersist.writeData(df,ticker,kind=side,flavour="trade",additional_tags=additional_tags,field=side)
    if not ret: return ret
    return myAlert.stackAlertMessage(f'Order sent : {side} {qty} {ticker}')

def setOrderApca(paper,ticker,qty,side='buy',type='market'):
    data={'symbol':ticker,'qty':qty,'side':side,'type':type,'time_in_force':'gtc'}
    return apiCallApca(path='/v2/orders',paper=paper,data=data)

def buyStock(ticker,qty,paper=True,test=True):
    return setOrder(paper=paper,ticker=ticker,qty=qty,side='buy',test=test)

def sellStock(ticker,qty,paper=True,test=True):
    return setOrder(paper=paper,ticker=ticker,qty=qty,side='sell',test=test)

def getRealOpenPositions(paper=True):
    ret = getPositions(paper=paper)
    if not ret: return ret
    positions = ret.value

    if len(positions) == 0 :
        return Result.ok(positions)
    elif positions['side'].unique() != ['long']:
        ret = myAlert.stackAlertMessage(f'Not only long positions. Exiting ...')
        if not ret: return ret
        return Result.error(msg='not only long positions')
        
    return Result.ok(positions)

def getLocalOpenPositions():
    ret = myPersist.getMeasurements()
    if not ret: return ret
    measurements=ret.value
    local_positions=pd.DataFrame(columns=['symbol','qty']) # qty here is remaining field in DB
    local_positions.set_index('symbol',inplace=True)

    for ticker in measurements:
        ret=getLocalOpenPositionByTicker(ticker)
        if not ret: return ret
        position_ticker = ret.value
        local_positions=local_positions.append(position_ticker)

    local_positions = local_positions.loc[local_positions['qty'] != 0]

    return Result.ok(local_positions)

def getLocalOpenPositionByTicker(ticker):
    array_local_position=[]
    ret = myPersist.getLastTradeInflux(ticker)
    if not ret: return ret
    last_trade = ret.value
    remaining_stocks=0
    if not last_trade.empty:
        remaining_stocks=last_trade.iloc[0]['remaining']
        array_local_position.append([ticker,remaining_stocks])
    local_position=pd.DataFrame(columns=['symbol','qty'],data=array_local_position)
    local_position.set_index('symbol',inplace=True)

    return Result.ok(local_position)

def checkStocksNumberConsistence(paper=True):
    ret = getLocalOpenPositions()
    if not ret: return ret
    local = ret.value

    if not local.empty:
        local=local.loc[local['qty'] != 0]

    ret = getRealOpenPositions(paper=True)
    if not ret: return ret
    real = ret.value
    #print("Current remote positions :")
    #print(real)

    # Check local and real equality
    eq=True
    if len(local.index) != len(real.index):
        print('bad localindex : ')
        print(local)
        print('bad realindex :')
        print(real)
        eq = False
    
    if eq:
        for i in local.index:
            if float(local.loc[i]['qty']) != float(real.loc[i]['qty']):
                print('badlocal : '+str(type(local.loc[i]['qty']))+ 'x')
                print('badreal : '+str(type(real.loc[i]['qty']))+'x')
                eq=False
                break
    return Result.ok(eq)

def debugForceLocalPositions(paper=True):
    # Preparing order data to myPersist
    #current_timezone = pytz.timezone(myVariables.tz)
    #date_today = datetime.now(current_timezone)
    #date_array=[date_today]
    date_array=['temp']
    qty_array=[0]
    side='buy'
    df = pd.DataFrame({'date': date_array, side: qty_array})
    df[side] = df[side].astype('float')
    df = df.set_index('date')

    # Get real datas
    ret = getRealOpenPositions(paper=paper)
    if not ret: return ret
    real = ret.value

    # Get local data
    ret = getLocalOpenPositions()
    if not ret: return ret
    local = ret.value

    # myPersist fake record
    date_array=[datetime.now(pytz.timezone(myVariables.tz))]
    df = pd.DataFrame({'date': date_array, 'buy': [0]})
    df['buy'] = df[side].astype('float')
    df = df.set_index('date')
    for index,row in real.iterrows():

        # Goal is to keep local not present on real side
        local = local.loc[local.index != index]

        ret = myPersist.getLastTrade(ticker=index)
        if not ret: return ret
        last_trade = ret.value
        stocks_owned = 0
        if not last_trade.empty:
            stocks_owned = last_trade['remaining'][0]

        if float(row[0]) == float(stocks_owned):
            print(f' Local stocks ammount correct for ticker {index}')
            continue
        else:
            print(f' Forcing local stocks ammount for ticker {index} from {str(stocks_owned)} to {str(row[0])}')
            additional_tags = {'remaining':row[0]}
            ret = myPersist.writeData(df,index,kind='fakebuy',flavour='trade',additional_tags=additional_tags,field='buy')
            if not ret: return ret

    # Here only local stocks not on real side anymore
    for index_local,row_local in local.iterrows():
        print(f' Forcing local stocks ammount for ticker {index_local} from {str(row_local[0])} to 0')
        additional_tags = {'remaining':0}
        ret = myPersist.writeData(df,index_local,kind='fakebuy',flavour='trade',additional_tags=additional_tags,field='buy')
        if not ret: return ret
    return Result.ok()

def qtyToBuy(ticker):
    ret = myPersist.getLastRecords(ticker,freq="1h")
    if not ret: return ret
    last_record = ret.value
    if last_record.empty:
        print("Error: no data for ticker "+ticker+". Exiting ...")
        exit(1)
    close_price=last_record['close'][0]
    
    ret = myPersist.getLastBalance()
    if not ret: return ret
    local_balance = ret.value

    if str(type(local_balance)) == str(type(pd.DataFrame([]))) and local_balance.empty:
        print('Init to do !!')
        return Result.error()
    
    qty_to_buy=int(round(myVariables.mean_trade_price/close_price))

    if (qty_to_buy+1) * close_price > local_balance - myVariables.min_balance_to_keep:
        print("WARNING: local balance too low !")
        ret = myAlert.stackAlertMessage("Warning: local balance too low !")
        if not ret: return ret
        qty_to_buy=0

    return Result.ok(qty_to_buy)

def applyPositions(ticker,paper=True,test=True):
    print(f'Check data for {ticker}')
    ret = myLibrary.checkPricesAgeByTicker(ticker,delay_minutes=10,fromLastTradeHour=False)
    if not ret: return ret
    prices_age = ret.value

    # No prices or prices outdated
    if prices_age == 'noprices':
        print(f' Error: No prices for ticker {ticker}. Skipping ...')
        ret = myAlert.stackAlertMessage(f'Skipping {ticker}: no prices')
        if not ret: return ret
        return Result.ok(False)
    elif prices_age > 0:
        print(f' Error: Prices for ticker {ticker} are not up to date. Skipping ...')
        ret = myAlert.stackAlertMessage(f'Skipping {ticker}: prices have {round(prices_age,1)}h')
        if not ret: return ret
        return Result.ok(False)
    
    ret = myLibrary.checkPositionsFilledByTicker(ticker)
    if not ret: return ret
    filled_bool = ret.value

    # No positions or positions have to be filled
    if not filled_bool:
        print(f' Positions are not filled for ticker {ticker}. Skipping ...')
        ret = myAlert.stackAlertMessage(f'Skipping {ticker}: pos not filled')
        if not ret: return ret
        return Result.ok(False)

    ret=myPersist.getLastPositionHourly(ticker)
    if not ret: return ret
    last_position = ret.value

    print(f' Checking actions to do for ticker {ticker} ...')
    ret=getLocalOpenPositionByTicker(ticker)
    if not ret: return ret
    open_positions = ret.value
    stocks_owned = 0
    if not open_positions.empty:
        stocks_owned = open_positions['qty'][0]
    # Computed position is to sell
    if last_position['position'][0] == 0:
        # We have stocks => we sell
        if stocks_owned > 0:
            ret = sellStock(ticker=ticker,qty=stocks_owned,paper=paper,test=test)
            if not ret: return ret
            ret = waitOrdersPassed(paper=paper)
            if not ret: return ret
            ret = getBalance(paper=paper)
            if not ret: return ret

    # Computed position is to buy
    elif last_position['position'][0] == 1:
        # We don't have stocks => we buy
        if stocks_owned == 0:
            # Compute how many stocks have to be bought
            ret=qtyToBuy(ticker)
            if not ret: return ret
            qty_to_buy = ret.value
            if qty_to_buy > 0:
                ret = buyStock(ticker=ticker,qty=qty_to_buy,paper=paper,test=test)
                if not ret: return ret
                ret = waitOrdersPassed(paper=paper)
                if not ret: return ret
                ret = getBalance(paper=paper)
                if not ret: return ret

    return Result.ok()

def main(tickers=None):
    print(f'===================== APPLY TRADES ====================')
    print(f'Checking no orders are pending ...')
    ret = getOrders(paper=True)
    if not ret: return ret
    orders_value = ret.value
    if not orders_value.empty:
        print(f' ALERT: Previous orders pending.')
        ret = myAlert.stackAlertMessage(f'Alert: Previous orders pending')
        if not ret: return ret
        return Result.error(msg='Previous orders are pending')
    else:
        print(f' All previous orders passed !')

    print(f'Checking stocks number consistence ...')
    ret = checkStocksNumberConsistence(paper=True)
    if not ret: return ret
    stocksNumberConsistence = ret.value
    if not stocksNumberConsistence:
        print(f' ALERT: Trades data are not consistent.')
        ret = myAlert.stackAlertMessage(f'Alert: Trades data not consistent')
        if not ret: return ret
        return Result.error(msg='Trades data are not consistent')
    else:
        print(f' Stocks number consistent !')

    if tickers is None:
        ret = myPersist.getMeasurements(less_than_one_hour=True)
        if not ret: return ret
        tickers=ret.value
    
    if len(tickers) == 0:
        ret = myAlert.stackAlertMessage(f'No data less than 1 hour for tickers')
        if not ret: return ret

    #tickers = ['SBUX','AAPL','NKE'] #test

    for ticker in tickers:
        ret = applyPositions(ticker,paper=True,test=False)
        if not ret: return ret
    return Result.ok()

if __name__ == "__main__":
    main()