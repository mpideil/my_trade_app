#!/bin/python
import _4generate_report
import _1grab_data
import _2process_positions
import _3apply_trades
import myAlert

import myVariables
import traceback

import sys
import myLibrary
import os
import datetime

from Result import Result
import myPersist
from _1grab_data_folder import myDownload
from _2process_positions_folder import myStrategie,myReport
import pytz
import pdb

import pandas as pd

def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == 'init':
            ret = _3apply_trades.getBalance(paper=True)
            if not ret: return ret
        elif sys.argv[1] == 'debug':
            pdb.set_trace()
        elif sys.argv[1] == 'local_positions':
            ret = _3apply_trades.debugForceLocalPositions()
            if not ret: return ret
        elif sys.argv[1] == 'report':
            ret = _4generate_report.main()
            if not ret: return ret
            res=ret.value
            #print(res)
        elif sys.argv[1] == 'test':
            # ret = myPersist.getData(ticker='NFLX',flavour="computed",kind="position",field='position')
            # if not ret: return ret
            # print(ret.value)
            # exit()

            ticker='SBUX'
            #ret = _1grab_data.main(tickers)
            #if not ret:return ret
            ret = _2process_positions.process(ticker)
            if not ret:return ret
            exit()
        else:
            print('Bad argument')
    else:
        ret = myAlert.initStackAlertMessage()
        if not ret: return ret
        try:
            myAlert.stackAlertMessage(f'==== GRAB DATA ====')
            ret = _1grab_data.main()
            if not ret:
                myAlert.stackAlertMessage('Error: Running grab_data : ' + str(ret))
        except Exception as err:
            myAlert.stackAlertMessage(traceback.format_exc())
        try:
            myAlert.stackAlertMessage(f'==== PROCESS POSITIONS ====')
            ret = _2process_positions.main()
            if not ret:
                myAlert.stackAlertMessage('Error: Running process_positions : ' + str(ret))
        except Exception as err:
            myAlert.stackAlertMessage(traceback.format_exc())
        try:
            myAlert.stackAlertMessage(f'==== APPLY TRADES ====')
            ret = _3apply_trades.main()
            if not ret:
                myAlert.stackAlertMessage('Error: Running apply_trades : ' + str(ret))
        except Exception as err:
            myAlert.stackAlertMessage(traceback.format_exc())
        try:
            ret = myAlert.alert(myVariables.stacked_alert_messages)
            if not ret: return ret
        except:
            basename = "logfile"
            suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            filename = "_".join([basename, suffix]) # e.g. 'mylogfile_120508_171442'
            f = open(filename, "a")
            f.write(myVariables.stacked_alert_messages)
            f.close()

main()

