#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 16:29:02 2022
@title: "file title goes here"
@description: "file description"
@details: "file description"
@author: Alex Kahl

"""

import pdb
import pandas as pd
from bbccode.processing import get_trades, load_portfolio_data
from bbccode.account import Portfolio, Trade
from bbccode.database.dbconnection import DBConnection
from sqlalchemy import create_engine
import datetime
from pandas import NaT
from collections import Counter
import numpy as np


fund = "UCITS"

DATABASE_ID = "POSTGRES_PROD"


pfdata = load_portfolio_data(fund=fund, cutoff_date=None)




def get_raw_posdata(pfdata:dict):
    """
    unravel position data into workable format

    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function
        
    Returns
    -------
    posdata_raw : pd.DataFrame


    """
    
    trades = pfdata["trade_meta"]

    position_data = pfdata["pos_files_contents"]

    pos_trade_map = {posid: trade_id for trade_id, trade in trades.items()
                     for posid in trade["positions"].keys()
                     }
    
    posdata_raw = position_data.unstack().dropna()
    posdata_raw = posdata_raw.reset_index()

    posdata_raw.columns = ["posid", "field", "date", "value"]
    posdata_raw["trade_id"] = posdata_raw["posid"].map(pos_trade_map)

    return posdata_raw



###############################################################################
###############################################################################
#
#           1) write fund table
#
###############################################################################
###############################################################################



def make_fund_table_content(pfdata:dict, fund):
    """
    create fund table content from old structure

    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function

    Returns
    -------
    fund_table : pd.DataFrame

    """

    fund_data = pfdata["nav_files_contents"]

    pfids = fund_data.columns.get_level_values(0).drop_duplicates()
    
    fund_info = fund_data[pfids[0]]
    
    funds = fund_info[['FUND_ID', 'FUND_NAME']].drop_duplicates().dropna()
    
    funds.columns = ["bbc_fund_id", "fund_name"]
    
    funds["is_active"] = True
    
    funds["fund_name_short"] = fund
    
    bbc_fund_id = funds["bbc_fund_id"].iloc[0]
    
    fund_table = funds
    
    return fund_table



    
fund_table = make_fund_table_content(pfdata, fund)


bbc_fund_id = fund_table["bbc_fund_id"].iloc[0]

if False:
    with DBConnection(DATABASE_ID) as conn:
        fund_table.to_sql(name="reporting_fund", con=conn,
                     schema="public", index=False,
                     if_exists='append')


def get_fund_id(bbc_fund_id:str):
    """
    load fund id

    Parameters
    ----------
    bbc_fund_id : str

    Returns
    -------
    int

    """
    
    with DBConnection(DATABASE_ID) as conn:
        sql_query = f"select id from reporting_fund where fund_name_short = '{bbc_fund_id}'"
        info = pd.read_sql_query(sql_query, conn)
        fund_id = info["id"].iloc[0]
    
    return fund_id


fund_id = get_fund_id(fund)


###############################################################################
###############################################################################
#
#           2) write portfolio table
#
###############################################################################
###############################################################################


def make_portfolio_table_content(pfdata:dict, fund_id:int):
    """
    create portfolio table content from old structure

    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function

    fund_id : int
        id of fund table in database
        
        
    Returns
    -------
    portfolio_table : pd.DataFrame
        

    """
    
    fund_data = pfdata["nav_files_contents"]
    
    pfids = fund_data.columns.get_level_values(0).drop_duplicates()
    
    field_map = {"FUND_ID": "bbc_fund_id",
                 "SHARE_CLASS_NAME": "share_class",
                 "SHARE_CLASS_CURRENCY": "currency",
                 "FUND_NAME": "fund_name"}
    
    pf_list = []
    for pfid in pfids:
        fund_info = fund_data[pfid]
    
        tmpdata = fund_info[field_map.keys()].drop_duplicates().dropna()
        tmpdata["isin"] = pfid
        pf_list.append(tmpdata)
    
    pdata = pd.concat(pf_list)
    
    field_map["isin"] = "isin"
    
    pdata.columns = pdata.columns.map(field_map)
    
    pdata["fund_name"] = pdata["fund_name"].apply(lambda x: x.split("-")[0].strip())
    pdata["portfolio_name"] = pdata["fund_name"] + " - " + pdata["share_class"]
    pdata["is_active"] = True
    pdata["fund_id"] = fund_id
    
    selfields = ["currency", "isin", "portfolio_name", "fund_id", "is_active"]
    portfolio_table = pdata[selfields]
    
    
    return portfolio_table


portfolio_table = make_portfolio_table_content(pfdata, fund_id)


if False:
    with DBConnection(DATABASE_ID) as conn:
        portfolio_table.to_sql(name="reporting_portfolio", con=conn,
                               schema="public", index=False,
                               if_exists='append')

###############################################################################
###############################################################################
#
#           3) write trade table
#
###############################################################################
###############################################################################


def make_trade_table_content(pfdata:dict, fund_id:int):
    """
    create trade table content from old structure

    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function

    fund_id : int
        id of fund table in database

    Returns
    -------
    trade_table : pd.DataFrame
        DESCRIPTION.

    """
    
    trades = pfdata["trade_meta"]
    trade_results = []
    fields = ["direction", "label", "bucket", "asset_class"]
    
    posdata_raw = get_raw_posdata(pfdata)
    trade_startdates = posdata_raw.groupby("trade_id")["date"].min().to_dict()
    
    for trade_id, info in trades.items():
    
        tmpdata = {field: info[field] for field in fields}
        tmpdata["bbc_trade_id"] = trade_id
    
        positions = info["positions"]
    
        tmpdata["positions"] = list(positions.keys())
    
        start_dates = []
        end_dates = []
    
        date_func = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")
    
        tmpdata["start_date"] = trade_startdates[trade_id]
    
        for pos, posinfo in positions.items():
    
            if "end_date" in posinfo:
    
                end = posinfo["end_date"]
                try:
                    end_date = date_func(end)
                    end_dates.append(end_date)
                except:
                    pass
    
        tmpdata["end_date"] = None if len(end_dates) == 0 else max(end_dates)
    
        trade_results.append(tmpdata)


    tdata = pd.DataFrame(trade_results)
    
    tdata.columns = [col if col != "label" else "name" for col in tdata.columns]
    
    today = datetime.datetime.now()
    
    is_active = lambda x, date=today: True if x is NaT else x > date
    tdata["is_active"] = tdata["end_date"].apply(is_active)
    tdata["fund_id"] = fund_id
    selcols = [col for col in tdata.columns if col != "positions"]
    
    trade_table = tdata[selcols]
    
    return trade_table

trade_table = make_trade_table_content(pfdata, fund_id)

if False:
    with DBConnection(DATABASE_ID) as conn:
        trade_table.to_sql(name="reporting_trade", con=conn,
                     schema="public", index=False,
                     if_exists='append')

###############################################################################
###############################################################################
#
#           4) write trade clips table
#
###############################################################################
###############################################################################


CP_IDENTIFIERS = {
    "BANK OF": "BOFA",
    "BOFA": "BOFA",
    "CREDIT SUISSE": "CS",
    "GOLDMAN SACHS": "GS",
    "JP MORGAN": "JPM",
    "J.P.": "JPM",
    "BNP": "BNP",
    "CITI": "CITI",
    "MERRILL LYNCH": "BOFA",
    "MORGAN STANLEY": "MS",
    "NORMURA": "NM",
    "DEUTSCHE BANK": "DB",
    "SOCIETE": "SOC",
    "SOC": "SOC",
    "UBS": "UBS",
    "NOMURA": "NM",
    "BARCLAYS": "BARC",
    "CS": "CS"
}

def clean_cp(cp, indentifier=CP_IDENTIFIERS):
    cp = cp.upper().strip()

    for key, value in indentifier.items():

        if cp.startswith(key):
            return value

    return cp


def make_trade_clips_table_content(pfdata:dict, cp_map=CP_IDENTIFIERS):
    """
    create trade clips table content from old structure

    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function
    
    cp_map : dict, optional
        The default is CP_IDENTIFIERS.

    Returns
    -------
    clip_table
        

    """
        
    posdata_raw = get_raw_posdata(pfdata)
    

    cpdata = posdata_raw.loc[posdata_raw.field == "COUNTERPARTY"]
    cpdata = cpdata[["posid", "trade_id", "value"]].drop_duplicates()
    cpdata.columns = ["posid", "trade_id", "counterparty"]

    cpdata["counterparty"] = cpdata["counterparty"].apply(clean_cp)

    # all other trade clips without counterparty are listed
    
    selidx = ~posdata_raw.posid.isin(cpdata.posid)
    
    listed_data = posdata_raw.loc[selidx, ["posid", "trade_id"]].drop_duplicates()
    
    listed_data["counterparty"] = "Listed"
    listed_data = listed_data.dropna()
    
    
    cpdata = pd.concat([cpdata, listed_data])
    
    pos_start_date_map = posdata_raw.groupby("posid").date.min().to_dict()
    pos_end_date_map = posdata_raw.groupby("posid").date.max().to_dict()
    
    cpdata["start_date"] = cpdata.posid.map(pos_start_date_map)
    cpdata["expiry_date"] = cpdata.posid.map(pos_end_date_map)
    
    last_date = posdata_raw.date.max()
    
    cpdata["expiry_date"] = cpdata["expiry_date"].apply(lambda x: x if x != last_date else np.nan)
    
    cpdata = cpdata.sort_values(["trade_id", "start_date"])

    trade_clip_details = []
    for trade_id, info in cpdata.groupby(["trade_id"]):
        cp_counter = Counter(info.counterparty)
    
        clip_map = {cp: i for i, cp in enumerate(cp_counter, start=1)}
    
        info["clip_id"] = info.counterparty.map(clip_map).astype("str")
    
        trade_clip_details.append(info)
    
    clipdata_final = pd.concat(trade_clip_details)


    with DBConnection(DATABASE_ID) as conn:
        sql_query = f"select id as trade_id, bbc_trade_id from reporting_trade where fund_id = {fund_id}"
        tinfo = pd.read_sql_query(sql_query, conn)


    def helper(data):
        expdates = data["expiry_date"].dropna()
    
        expdate = expdates.max() if len(expdates) > 0 else NaT
    
        return pd.Series({"trade_date": data["start_date"].min(),
                          "expiry_date": expdate})
    
    
    clipres = clipdata_final.groupby(["trade_id", "clip_id", "counterparty"]).apply(helper)
    
    clipres = clipres.reset_index()
    
    clipres.columns = [col if col != "trade_id" else "bbc_trade_id" for col in clipres.columns]
    
    clipres = clipres.merge(tinfo, on="bbc_trade_id")
    
    clipres["is_active"] = clipres["expiry_date"].apply(lambda x: x is NaT)
    
    clip_table = clipres[[col for col in clipres.columns if col != "bbc_trade_id"]]
    clip_table["risk_models"] = "[]"
    
    return clip_table, clipdata_final



clip_table, clipdata_final = make_trade_clips_table_content(pfdata)


if False:
    with DBConnection(DATABASE_ID) as conn:
        clip_table.to_sql(name="reporting_tradeclip", con=conn,
                     schema="public", index=False,
                     if_exists='append')

###############################################################################
###############################################################################
#
#           5) write trade positions table
#
###############################################################################
###############################################################################



def make_position_table_content(pfdata:dict, clipdata_final:pd.DataFrame):
    """
    create position table content from old structure

    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function

    clipdata_final : pd.DataFrame
    
    Returns
    -------
    position_table


    """
    

    fld_map = {'TRADE_DATE': 'start_date',
               'CONTRACT_NUMBER': 'contract_number',
               'MATURITY_DATE': 'end_date',
               'T4S_CONTRACT_NUMBER': 't4s_contract_number',
               'POSITION_DESCRIPTION': 'name',
               'PRICE_TYPE': 'price_type',
               'TRANSACTION_TYPE': 'transaction_type',
               'ISIN': 'isin',
               'CUSIP': 'cusip',
               'INSTRUMENT_CURRENCY': 'instrument_currency'}
    
    
    posdata_raw = get_raw_posdata(pfdata)
    
    selidx = posdata_raw.field.isin(fld_map.keys())
    
    static_data = posdata_raw.loc[selidx, ["posid", "field", "value"]]
    
    static_data = static_data.groupby(["posid", "field"])["value"].last().reset_index()
    
    static_posdata = static_data.pivot(index="posid", columns="field", values="value")
    
    static_posdata.columns = static_posdata.columns.map(fld_map)
    
    static_posdata.index.name = "bbc_position_id"
    
    stable_data = static_posdata.reset_index()
    
    
    def date_helper(value):
        if isinstance(value, str):
    
            if "-" in value:
                return datetime.datetime.strptime(value, "%Y-%m-%d")
            if "/" in value:
                return datetime.datetime.strptime(value, "%d/%m/%Y")
        return value
    
    
    with DBConnection(DATABASE_ID) as conn:
        sql_query = f"""select c.id as trade_clip_id, c.clip_id, 
                        t.bbc_trade_id as trade_id from reporting_tradeclip as c
                        inner join reporting_trade as t on t.id=c.trade_id"""
        cinfo = pd.read_sql_query(sql_query, conn)
    
    pos_clips = clipdata_final[["posid", "trade_id", "clip_id"]]
    
    pos_clip_data = pos_clips.merge(cinfo, on=["trade_id", "clip_id"])
    
    pos_clip_data.columns = [col if col != "posid" else "bbc_position_id" for col in pos_clip_data.columns]
    
    iddata = pos_clip_data[["bbc_position_id", "trade_clip_id"]]
    
    static_final_table = stable_data.merge(iddata, on=["bbc_position_id"])
    
    static_final_table = static_final_table.drop_duplicates()
    
    static_final_table.start_date = static_final_table.start_date.apply(date_helper)
    static_final_table.end_date = static_final_table.end_date.apply(date_helper)
    
    selidx = ~static_final_table.bbc_position_id.duplicated()
    position_table = static_final_table.loc[selidx].copy()
    
    for int_field in ["t4s_contract_number", "contract_number"]:
        round_int = lambda x: x if np.isnan(x) else int(x)
        position_table[int_field] = position_table[int_field].apply(round_int)
    
    return position_table


position_table = make_position_table_content(pfdata, clipdata_final)

if False:
    with DBConnection(DATABASE_ID) as conn:
        position_table.to_sql(name="reporting_tradeposition", con=conn,
                                  schema="public", index=False,
                                  if_exists='append')

###############################################################################
###############################################################################
#
#           6) write position data
#
###############################################################################
###############################################################################



def get_posids_fund(fund_id: int):
    """
    read position ids from database for a given fund
    SQL query assumes that positions are unique for a given fund
    in the old structure this is also the case    
    
    Parameters
    ----------
    fund_id : int
        DESCRIPTION.

    Returns
    -------
    posinfo

    """
    
    
    with DBConnection(DATABASE_ID) as conn:
        sql_query = f"""select pos.id as trade_position_id, pos.bbc_position_id
                        from reporting_tradeposition as pos
                        inner join reporting_tradeclip as c ON c.id = pos.trade_clip_id
                        inner join reporting_trade as t ON t.id = c.trade_id
                        inner join reporting_fund as f ON f.id = t.fund_id
                        where f.id = {fund_id}"""
                                         
        posinfo = pd.read_sql_query(sql_query, conn)

    return posinfo




def make_position_data_table_content(pfdata:dict, fund_id:int):
    """

    create position data content from old structure
    
    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function
    
    fund_id : int
        id of fund table in database

    Returns
    -------
    position_data_table : TYPE
        DESCRIPTION.

    """
    
    
    
    
    posdata_raw = get_raw_posdata(pfdata)

    fld_map = {'BBC PNL': 'bbc_pnl',
               'MARKET_VALUE_INSTRUMENT_CCY': 'market_value_local',
               'MARKET_VALUE_FUND_CURRENCY': 'market_value_base',
               'ACCRUEDINTEREST_INSTRUMENT_CCY': 'accrued_interest_local',
               'ACCRUED_INTEREST_FUND_CCY': 'accrued_interest_base',
               'EXCHANGE_RATE': 'exchange_rate',
               'NEXT_COUPON_DATE': 'next_coupon_date',
               'UNITS': 'units'}
    
    tmpdata = posdata_raw.loc[posdata_raw.field.isin(fld_map.keys()), ["posid", "field", "value", "date"]]
    posts = tmpdata.pivot(index=["posid", "date"], columns="field", values="value")
    
    posts.columns = posts.columns.map(fld_map)
    
    posts.index.names = ["bbc_position_id", "report_date"]
    posts = posts.reset_index()
                            
    pinfo = get_posids_fund(fund_id)
    
    ptstable = posts.merge(pinfo, on="bbc_position_id")
    
    ptstable = ptstable[[col for col in ptstable.columns if col != "bbc_position_id"]]
    
    position_data_table = ptstable
    
    def date_helper(value):
        if isinstance(value, str):
    
            if "-" in value:
                return datetime.datetime.strptime(value, "%Y-%m-%d")
            if "/" in value:
                return datetime.datetime.strptime(value, "%d/%m/%Y")
        return value
    
    next_coupons = position_data_table.next_coupon_date.apply(date_helper)
    
    position_data_table["next_coupon_date"] = next_coupons
    
    return position_data_table

position_data_table = make_position_data_table_content(pfdata, fund_id)

if False:
    with DBConnection(DATABASE_ID) as conn:
        position_data_table.to_sql(name="reporting_positiondata", con=conn,
                        schema="public", index=False,
                        if_exists='append')

###############################################################################
###############################################################################
#
#           6) write portfolio data
#
###############################################################################
###############################################################################


def make_portfolio_data_table_content(pfdata:dict, fund_id:int):
    """

    create position data content from old structure
    
    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function
    
    fund_id : int
        id of fund table in database

    Returns
    -------
    portfolio_data_table : pd.DataFrame

    """
    
    fld_map = {'NAV_DATE': 'report_date',
               'NET_ASSET_VALUE_UNSWUNG': 'portfolio_value',
               'NAV_PERFORMANCE_PCT': 'nav_performance_pct',
               'CLEAN_PRICE': 'clean_price'}
    
    fund_data = pfdata["nav_files_contents"]
    tmpdata = fund_data.unstack().reset_index()
    
    tmpdata.columns = ["isin", "field", "report_date", "value"]
    
    tmpdata = tmpdata.loc[tmpdata.field.isin(fld_map)]
    
    tmpdata = tmpdata.pivot(index=["isin", "report_date"], columns="field", values="value")
    
    tmpdata = tmpdata.dropna()
    
    tmpdata.columns = tmpdata.columns.map(fld_map)
    
    with DBConnection(DATABASE_ID) as conn:
        sql_query = f"""select id as portfolio_id, isin from reporting_portfolio where fund_id={fund_id};"""
        pinfo = pd.read_sql_query(sql_query, conn)
    
    pfts_table = tmpdata.merge(pinfo, on="isin")
    
    pfts_table = pfts_table[[col for col in pfts_table.columns if col != "isin"]]
    
    pfts_table = pfts_table.melt(id_vars=["report_date", "portfolio_id"])
    
    pfts_table.columns = ["report_date", "portfolio_id", "field", "value"]
    
    portfolio_data_table = pfts_table.drop_duplicates()

    return portfolio_data_table


portfolio_data_table = make_portfolio_data_table_content(pfdata, fund_id)



if False:
    with DBConnection(DATABASE_ID) as conn:
        portfolio_data_table.to_sql(name="reporting_portfoliodata", con=conn,
                          schema="public", index=False,
                          if_exists='append')

###############################################################################
###############################################################################
#
#           6) write non-market return data
#
###############################################################################
###############################################################################


def make_nmr_data_table_content(pfdata:dict, fund_id:int):
    """

    create non market return data content from old structure
    
    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function
    
    fund_id : int
        id of fund table in database

    Returns
    -------
    nmr_table : pd.DataFrame

    """
    
    
    trades = pfdata["trade_meta"]
    
    nmr_rets = []
    for trade_id, trade_info in trades.items():
    
        if "non_market_returns" in trade_info:
    
            rets = trade_info["non_market_returns"]
    
            for pid, ret_info in rets.items():
                tmpdata = {"date": ret_info.keys(), "non_market_return": ret_info.values()}
    
                tmpdata = pd.DataFrame(tmpdata)
    
                tmpdata["bbc_position_id"] = pid
    
            nmr_rets.append(tmpdata)
    
    nmrdata = pd.concat(nmr_rets)
    
    pinfo = get_posids_fund(fund_id)
    
    nmrdata = nmrdata.merge(pinfo, on="bbc_position_id")
    
    nmrdata.columns = [col if col != "date" else "report_date" for col in nmrdata.columns]
    
    nmr_data_table = nmrdata[[col for col in nmrdata.columns if col != "bbc_position_id"]]
    
    return nmr_data_table


nmr_data_table = make_nmr_data_table_content(pfdata, fund_id)
    

if False:
    with DBConnection(DATABASE_ID) as conn:
        nmr_data_table.to_sql(name="reporting_nmrdata", con=conn,
                       schema="public", index=False,
                       if_exists='append')



###############################################################################
###############################################################################
#
#           6) write cash account table
#
###############################################################################
###############################################################################

def map_account_type(desc:str):
    """
    mapping account types for database import
    """
    if "CASH CURRENT ACCOUNT" in desc:
        return "CURRENT ACCOUNT"
    
    elif "COLLAT" in desc:
        return "COLLATERAL"
    
    return "OTHER"


def make_cash_account_table_content(pfdata:dict, fund_id):
    """
    create position table content from old structure

    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function

    clipdata_final : pd.DataFrame
    
    Returns
    -------
    position_table


    """
    

    fld_map = {
               'FUND_ID': 'bbc_fund_id',
               "INSTRUMENT_CURRENCY": 'currency',
               "POSITION_DESCRIPTION": "description",
               "ASSET_TYPE": "asset_type",
               "TRANSACTION_TYPE": "transaction_type",
               "CUSTODY_ACCOUNT_NUMBER": "custody_account"
               }
    
    posdata_raw = get_raw_posdata(pfdata)
    
    selidx = posdata_raw.field.isin(fld_map.keys())
    
    static_data = posdata_raw.loc[selidx, ["posid", "field", "value"]]
    
    
    static_data = static_data.groupby(["posid", "field"])["value"].last().reset_index()
    
    static_cashdata = static_data.pivot(index="posid", columns="field", values="value")
    
    static_cashdata.columns = static_cashdata.columns.map(fld_map)
    static_cashdata.index.name = "bbc_position_id"
    
    static_cashdata = static_cashdata.reset_index()

    static_cashdata["account_type"] = static_cashdata.description.apply(map_account_type)
    static_cashdata["fund_id"] = fund_id
    
    
    sel_cash_pos = static_cashdata.transaction_type == 'CO'
    sel_liquidity = static_cashdata.asset_type == "LIQUIDITY_AT_SIGHT"
        
    # only import trading positions here - Cash Accounts will be handled seperately
    cashdata = static_cashdata.loc[sel_cash_pos & sel_liquidity]
    # exclude payables, receivables
    cashdata = cashdata.loc[cashdata.account_type != "OTHER"]
    
    def make_counterparty(desc): 
        return "CS" if desc.startswith("CASH") else desc.split(" - ")[1]
    
    cashdata["counterparty"] = cashdata.description.apply(make_counterparty)
    cashdata["counterparty"] = cashdata["counterparty"].map(clean_cp)

    
    cashids = cashdata.bbc_position_id
    
    selidx = posdata_raw.posid.isin(cashids)
    
    enddates = posdata_raw.loc[selidx].groupby("posid")["date"].max()
    
    active_accounts = enddates >= enddates.max()
    
    cashdata["is_active"] = active_accounts.values
    

    EXCLUDE_FIELDS = ['asset_type', 'bbc_fund_id', 'transaction_type']
    selcols = [col for col in cashdata.columns if col not in EXCLUDE_FIELDS]
    cashdata = cashdata[selcols]
        
    
    
    return cashdata



cash_account_table = make_cash_account_table_content(pfdata, fund_id)



if False:
    with DBConnection(DATABASE_ID) as conn:
        cash_account_table.to_sql(name="reporting_cashaccount", con=conn,
                       schema="public", index=False,
                       if_exists='append')



###############################################################################
###############################################################################
#
#           6) write cash data table
#
###############################################################################
###############################################################################


def get_cash_account_ids(fund_id):
    
    
    with DBConnection(DATABASE_ID) as conn:
        sql_query = f"""select id as cash_account_id, bbc_position_id from reporting_cashaccount where fund_id={fund_id};"""
        cinfo = pd.read_sql_query(sql_query, conn)

    return cinfo

cash_info = get_cash_account_ids(fund_id)





def make_cash_data_table_content(pfdata:dict, fund_id):
    """
    create position table content from old structure

    Parameters
    ----------
    pfdata : dict
        dictionary containing all infos for from old load_portfolio_data function

    clipdata_final : pd.DataFrame
    
    Returns
    -------
    position_table


    """
    cash_info = get_cash_account_ids(fund_id)

    fld_map = {
               'MARKET_VALUE_INSTRUMENT_CCY': 'market_value_local',
               'MARKET_VALUE_FUND_CURRENCY': 'market_value_base',
               'ACCRUEDINTEREST_INSTRUMENT_CCY': 'accrued_interest_local',
               'ACCRUED_INTEREST_FUND_CCY': 'accrued_interest_base',
               'NEXT_COUPON_DATE': 'next_coupon_date',
               'EXCHANGE_RATE': 'exchange_rate',
               'MARKET_VALUE_AS_PERCENT_TO_NAV': 'nav_percent',
               'POSITION_DESCRIPTION': 'description'
               }
    
    posdata_raw = get_raw_posdata(pfdata)

    tmpdata = posdata_raw.loc[posdata_raw.field == "ASSET_TYPE"]
    tmpdata = tmpdata.loc[tmpdata.value=="LIQUIDITY_AT_SIGHT"]
    posids = tmpdata.posid.drop_duplicates()
    
    selidx = posdata_raw.field.isin(fld_map.keys())
    cashdata = posdata_raw.loc[selidx, ["posid", "field", "value", "date"]]
    
    selidx = cashdata.posid.isin(posids)
    cashdata = cashdata.loc[selidx]
    
    def prep_cashts(posid, data):
        
        csts = data.pivot(index="date", columns="field", values="value")
        
        csts["ID"] = posid
        
        return csts.reset_index()
    
    account_data_gen = (prep_cashts(posid, data) for posid, data in cashdata.groupby("posid"))
    
    
    account_data = pd.concat(account_data_gen)
    
    fld_map["ID"] = "bbc_position_id"
    fld_map["date"] = "report_date"
    
    account_data.columns = account_data.columns.map(fld_map)
    
        
    account_data = account_data.merge(cash_info, on="bbc_position_id", how="inner")
    
    
    EXCLUDE_COLS = ["description", "bbc_position_id"]
    
    cols = [col for col in account_data.columns if col not in EXCLUDE_COLS]
    
    account_data = account_data[cols]
        
    return account_data




cash_data_table = make_cash_data_table_content(pfdata, fund_id)





if False:
    with DBConnection(DATABASE_ID) as conn:
        cash_data_table.to_sql(name="reporting_cashdata", con=conn,
                       schema="public", index=False,
                       if_exists='append')


