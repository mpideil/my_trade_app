#!/bin/python
import requests
import myVariables
from Result import Result

import pytz
from datetime import datetime,timedelta

def alert(message):
    return alertSlack(message)

def alertSlack(message):
    data = {"text": message}
    response = requests.post(myVariables.slack_web_hook,
        json=data,
    )
    return Result.ok()

def stackAlertMessage(message):
    """
    # With time infos
    current_timezone = pytz.timezone(myVariables.tz)
    current_datetime = datetime.now(current_timezone)
    time_prefix = current_datetime.strftime('%d-%b-%Y (%H:%M:%S)')
    myVariables.stacked_alert_messages = myVariables.stacked_alert_messages + time_prefix + ':\n' + message + '\n'
    """
    myVariables.stacked_alert_messages = myVariables.stacked_alert_messages + message + '\n'

    return Result.ok()

def initStackAlertMessage():
    current_timezone = pytz.timezone(myVariables.tz)
    current_datetime = datetime.now(current_timezone)
    time_prefix = current_datetime.strftime('%d-%b-%Y (%H:%M:%S)')
    myVariables.stacked_alert_messages = myVariables.stacked_alert_messages + '**** ' + time_prefix + ' ****\n'
    return Result.ok()

def printStackAlertMessage():
    print(f'----- Printing stack alert message -----')
    print(myVariables.stacked_alert_messages)
    print(f'----- End stack alert message -----')
    return Result.ok()
