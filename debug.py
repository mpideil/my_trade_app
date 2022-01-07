#!/bin/python

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


print(f' Download NFLX')
# ret = myDownload.get_data_latest('NFLX',hours=72)
# res = ret.value
from_datetime = datetime.datetime.now(pytz.timezone(myVariables.tz)) - datetime.timedelta(days=3)
ret = myPersist.getLastRecords('NFLX',since_date=from_datetime,freq="1h")
res = ret.value
print(len(res))