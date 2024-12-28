#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  4 08:51:32 2023
@title: "file title goes here"
@description: "file description"
@details: "file description"
@author: Alex Kahl

"""
import os
import re
import datetime
import pandas as pd
from bbccode.core.timestatics import DATE_FORMAT
from bbccode.account.daily_files import resolve_fund_search_path
from bbccode.database import DBConnection

DATABASE = "POSTGRES_LOCAL"


FUND = "UCITS"

IGNORE_FILES = [".DS_STORE"]


    
def check_date_string(datestr):
    pattern = r"(\d+)-(\d+)-(\d+)"
    
    check = re.match(pattern, datestr) is not None
    
    return check
    

def get_last_report_date(fund:str="UCITS"):
    """
    get last import report date for fund

    Returns
    -------
    last_date 

    """
    
    with DBConnection(DATABASE) as conn:
        sql_query = f"""SELECT MAX(pd.report_date) FROM reporting_portfoliodata as pd
                     INNER JOIN reporting_portfolio as p ON p.id = pd.portfolio_id
                     INNER JOIN reporting_fund as f ON f.id = p.fund_id
                     WHERE f.fund_name_short = '{fund}'"""
        date = pd.read_sql_query(sql_query, conn).iloc[0, 0]

    last_date = datetime.datetime(date.year, date.month, date.day)

    return last_date


def get_reporting_folders(fund:str, last_date:datetime.datetime):
    
    
    fund_directory = resolve_fund_search_path(fund)

    to_datetime = lambda x: datetime.datetime.strptime(x, DATE_FORMAT)    
    date_dirs = (to_datetime(date) for date in os.listdir(fund_directory)
                 if check_date_string(date))
    
    sel_dates = [date for date in date_dirs if date > last_date]
    
    
    reporting_folders = [(date, os.path.join(fund_directory, str(date.date()))) 
                          for date in sel_dates]
    
    return reporting_folders
    



last_date = get_last_report_date(FUND)

folders = get_reporting_folders(FUND, last_date)



def read_reporting_files()