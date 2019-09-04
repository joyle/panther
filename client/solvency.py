#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
@version: ??
@author: li
@file: solvency.py
@time: 2019-09-04 17:28
"""

import sys
sys.path.append('../')
sys.path.append('../../')
sys.path.append('../../../')
import time
import collections
import argparse
import pandas as pd
from datetime import datetime, timedelta
from factor import factor_solvency
from client.engines.sqlengine import sqlEngine
from client.utillities.sync_util import SyncUtil

from client.dbmodel.model import BalanceMRQ, BalanceTTM, BalanceReport
from client.dbmodel.model import CashFlowMRQ, CashFlowTTM, CashFlowReport
from client.dbmodel.model import IndicatorReport, IndicatorMRQ, IndicatorTTM
from client.dbmodel.model import IncomeMRQ, IncomeReport, IncomeTTM

from vision.vision.db.signletion_engine import *
# from ultron.cluster.invoke.cache_data import cache_data
pd.set_option('display.max_columns', None)


def get_trade_date(trade_date, n):
    """
    获取当前时间前n年的时间点，且为交易日，如果非交易日，则往前提取最近的一天。
    :param trade_date: 当前交易日
    :param n:
    :return:
    """
    syn_util = SyncUtil()
    trade_date_sets = syn_util.get_all_trades('001002', '19900101', trade_date)
    trade_date_sets = trade_date_sets['TRADEDATE'].values

    time_array = datetime.strptime(str(trade_date), "%Y%m%d")
    time_array = time_array - timedelta(days=365) * n
    date_time = int(datetime.strftime(time_array, "%Y%m%d"))
    if str(date_time) < min(trade_date_sets):
        # print('date_time %s is out of trade_date_sets' % date_time)
        return str(date_time)
    else:
        while str(date_time) not in trade_date_sets:
            date_time = date_time - 1
        # print('trade_date pre %s year %s' % (n, date_time))
        return str(date_time)


def get_basic_data(trade_date):
    """
    获取cash flow所需要的因子
    :param trade_date:
    :return:
    """
    engine = sqlEngine()
    maplist = {
        # cash flow
        'MANANETR': 'net_operate_cash_flow',  # 经营活动现金流量净额
        'FINALCASHBALA': 'cash_and_equivalents_at_end',  # 期末现金及现金等价物余额

        # income
        'TOTPROFIT':'total_profit',  # 利润总额
        'FINEXPE':'financial_expense',  # 财务费用
        'INTEINCO':'interest_income',  # 利息收入

        # balance
        'TOTLIAB': 'total_liability',  # 负债合计
        'TOTALCURRLIAB': 'total_current_liability',  # 流动负债合计
        'TOTCURRASSET': 'total_current_assets',  # 流动资产合计
        'INVE': 'inventories',  # 存货
        'CURFDS': 'cash_equivalents',  # 货币资金
        'TRADFINASSET': 'trading_assets',  # 交易性金融资产
        'NOTESRECE': 'bill_receivable',  # 应收票据
        'ACCORECE': 'account_receivable',  # 应收账款
        'OTHERRECE': 'other_receivable',  # 其他应收款
        'PARESHARRIGH': 'equities_parent_company_owners', # 归属于母公司股东权益合计
        'INTAASSET': 'intangible_assets',  # 无形资产
        'DEVEEXPE': 'development_expenditure',  # 开发支出
        'GOODWILL': 'good_will',  # 商誉
        'LOGPREPEXPE': 'long_deferred_expense',  # 长期待摊费用
        'DEFETAXASSET': 'deferred_tax_assets',  # 递延所得税资产
        '':'non_current_liability_in_one_year', # 一年内到期的非流动负债
        'SHORTTERMBORR': 'shortterm_loan',  # 短期借款
        'LONGBORR': 'longterm_loan',  # 长期借款
        'BDSPAYA': 'bonds_payable',  # 应付债券
        'INTEPAYA': 'interest_payable',  # 应付利息
        'TOTALNONCLIAB': 'total_non_current_liability',  # 非流动负债合计
        'TOTALNONCASSETS': 'total_non_current_assets', # 非流动资产合计
        'FIXEDASSENET': 'fixed_assets', # 固定资产
        'RIGHAGGR': 'total_owner_equities', # 所有者权益（或股东权益）合计
        'TOTASSET': 'total_assets',  # 资产总计

        # indicator
        'NDEBT': 'net_liability',  # 净负债

        # valuation
        '':'market_cap', # 总市值
        }
    columns = ['COMPCODE', 'PUBLISHDATE', 'ENDDATE', 'symbol', 'company_id', 'trade_date']
    # report data
    cash_flow_sets = engine.fetch_fundamentals_pit_extend_company_id(CashFlowReport,
                                                                     [CashFlowReport.MANANETR,  # 经营活动现金流量净额
                                                                      ], dates=[trade_date]).drop(columns, axis=1)
    cash_flow_sets = cash_flow_sets.rename(columns={'MANANETR': 'net_operate_cash_flow',  # 经营活动现金流量净额
                                                    })

    balance_sets = engine.fetch_fundamentals_pit_extend_company_id(BalanceReport,
                                                                   [BalanceReport.BDSPAYA,
                                                                    BalanceReport.TOTASSET,
                                                                    BalanceReport.TOTALNONCLIAB,
                                                                    BalanceReport.TOTCURRASSET,
                                                                    BalanceReport.TOTALCURRLIAB,
                                                                    BalanceReport.TOTLIAB,
                                                                    BalanceReport.FIXEDASSENET,
                                                                    BalanceReport.PARESHARRIGH,
                                                                    BalanceReport.SHORTTERMBORR,
                                                                    BalanceReport.non_current_liability_in_one_year,
                                                                    BalanceReport.LONGBORR,
                                                                    BalanceReport.BDSPAYA,
                                                                    BalanceReport.INTEPAYA,
                                                                    BalanceReport.RIGHAGGR,
                                                                    BalanceReport.TOTALNONCASSETS,
                                                                    BalanceReport.INVE,
                                                                    BalanceReport.INTAASSET,
                                                                    BalanceReport.DEVEEXPE,
                                                                    BalanceReport.GOODWILL,
                                                                    BalanceReport.LOGPREPEXPE,
                                                                    BalanceReport.DEFETAXASSET,
                                                                    BalanceReport.CURFDS,
                                                                    BalanceReport.TRADFINASSET,
                                                                    BalanceReport.NOTESRECE,
                                                                    BalanceReport.ACCORECE,
                                                                    BalanceReport.OTHERRECE,
                                                                    ],
                                                                   dates=[trade_date]).drop(columns, axis=1)

    balance_sets = balance_sets.rename(columns={
        'TOTLIAB': 'total_liability',  # 负债合计
        'TOTALCURRLIAB': 'total_current_liability',  # 流动负债合计
        'TOTCURRASSET': 'total_current_assets',  # 流动资产合计
        'INVE': 'inventories',  # 存货
        'CURFDS': 'cash_equivalents',  # 货币资金
        'TRADFINASSET': 'trading_assets',  # 交易性金融资产
        'NOTESRECE': 'bill_receivable',  # 应收票据
        'ACCORECE': 'account_receivable',  # 应收账款
        'OTHERRECE': 'other_receivable',  # 其他应收款
        'PARESHARRIGH': 'equities_parent_company_owners',  # 归属于母公司股东权益合计
        'INTAASSET': 'intangible_assets',  # 无形资产
        'DEVEEXPE': 'development_expenditure',  # 开发支出
        'GOODWILL': 'good_will',  # 商誉
        'LOGPREPEXPE': 'long_deferred_expense',  # 长期待摊费用
        'DEFETAXASSET': 'deferred_tax_assets',  # 递延所得税资产
        '': 'non_current_liability_in_one_year',  # 一年内到期的非流动负债
        'SHORTTERMBORR': 'shortterm_loan',  # 短期借款
        'LONGBORR': 'longterm_loan',  # 长期借款
        'BDSPAYA': 'bonds_payable',  # 应付债券
        'INTEPAYA': 'interest_payable',  # 应付利息
        'TOTALNONCLIAB': 'total_non_current_liability',  # 非流动负债合计
        'TOTALNONCASSETS': 'total_non_current_assets',  # 非流动资产合计
        'FIXEDASSENET': 'fixed_assets',  # 固定资产
        'RIGHAGGR': 'total_owner_equities',  # 所有者权益（或股东权益）合计
        'TOTASSET': 'total_assets',  # 资产总计
        'FINALCASHBALA': 'cash_and_equivalents_at_end',  # 期末现金及现金等价物余额
    })

    tp_solvency = pd.merge(cash_flow_sets, balance_sets, on='security_code')

    # MRQ data
    cash_flow_mrq_sets = engine.fetch_fundamentals_pit_extend_company_id(CashFlowMRQ,
                                                                         [CashFlowMRQ.MANANETR,
                                                                          ], dates=[trade_date]).drop(columns, axis=1)

    balance_mrq_sets = engine.fetch_fundamentals_pit_extend_company_id(BalanceMRQ,
                                                                       [BalanceMRQ.TOTALCURRLIAB
                                                                        ], dates=[trade_date]).drop(columns, axis=1)
    mrq_solvency = pd.merge(cash_flow_mrq_sets, balance_mrq_sets, on='security_code')

    # ttm data
    balance_ttm_sets = engine.fetch_fundamentals_pit_extend_company_id(BalanceTTM,
                                                                       [BalanceTTM.TOTCURRASSET,      # 流动资产合计
                                                                        BalanceTTM.TOTLIAB,
                                                                        BalanceTTM.TOTALCURRLIAB,
                                                                        BalanceTTM.INTEPAYA,
                                                                        BalanceTTM.BDSPAYA,
                                                                        BalanceTTM.LONGBORR,
                                                                        BalanceTTM.SHORTTERMBORR,
                                                                        BalanceTTM.non_current_liability_in_one_year
                                                                        ], dates=[trade_date]).drop(columns, axis=1)

    balance_ttm_sets = balance_ttm_sets.rename(columns={
        'TOTCURRASSET': 'total_current_assets',  # 流动资产合计
        'TOTLIAB': 'total_liability',  # 负债合计
        'TOTALCURRLIAB': 'total_current_liability',  # 流动负债合计
        '': 'non_current_liability_in_one_year',  # 一年内到期的非流动负债
        'SHORTTERMBORR': 'shortterm_loan',  # 短期借款
        'LONGBORR': 'longterm_loan',  # 长期借款
        'BDSPAYA': 'bonds_payable',  # 应付债券
        'INTEPAYA': 'interest_payable',  # 应付利息
    })

    cash_flow_ttm_sets = engine.fetch_fundamentals_pit_extend_company_id(CashFlowTTM,
                                                                         [CashFlowTTM.MANANETR,       # 经营活动现金流量净额
                                                                          CashFlowTTM.FINALCASHBALA,  # 期末现金及现金等价物余额
                                                                          ], dates=[trade_date]).drop(columns, axis=1)
    cash_flow_ttm_sets = cash_flow_ttm_sets.rename(columns={
        'MANANETR': 'net_operate_cash_flow',  # 经营活动现金流量净额
        'FINALCASHBALA': 'cash_and_equivalents_at_end',  # 期末现金及现金等价物余额
    })

    income_ttm_sets = engine.fetch_fundamentals_pit_extend_company_id(IncomeTTM,
                                                                      [IncomeTTM.TOTPROFIT,
                                                                       IncomeTTM.FINEXPE,
                                                                       IncomeTTM.INTEINCO,
                                                                       ], dates=[trade_date]).drop(columns, axis=1)
    income_ttm_sets = income_ttm_sets.rename(columns={
        'TOTPROFIT': 'total_profit',  # 利润总额
        'FINEXPE': 'financial_expense',  # 财务费用
        'INTEINCO': 'interest_income',  # 利息收入
    })

    indicator_ttm_sets = engine.fetch_fundamentals_pit_extend_company_id(IndicatorTTM,
                                                                         [IndicatorTTM.NDEBT,
                                                                          ], dates=[trade_date]).drop(columns, axis=1)
    indicator_ttm_sets = indicator_ttm_sets.rename(columns={
        'NDEBT': 'net_liability',  # 净负债
    })

    ttm_solvency = pd.merge(balance_ttm_sets, cash_flow_ttm_sets, on="security_code")
    ttm_solvency = pd.merge(income_ttm_sets, ttm_solvency, on="security_code")
    ttm_solvency = pd.merge(indicator_ttm_sets, ttm_solvency, on="security_code")

    return tp_solvency, ttm_solvency, mrq_solvency


def prepare_calculate_local(trade_date):
    # 本地计算
    tic = time.time()
    tp_solvency, ttm_solvency, mrq_solvency = get_basic_data(trade_date)
    print('len_tp_cash_flow: %s' % len(tp_solvency))
    print('len_ttm_cash_flow: %s' % len(ttm_solvency))
    print('tp_cash_flow: \n%s' % tp_solvency.head())
    print('ttm_cash_flow: \n%s' % ttm_solvency.head())

    if len(tp_solvency) <= 0 or len(ttm_solvency) <= 0 or len(mrq_solvency) <= 0:
        print("%s has no data" % trade_date)
        return
    else:
        factor_solvency.calculate(trade_date, tp_solvency, ttm_solvency, mrq_solvency)
    end = time.time()
    print('cash_flow_cal_time:{}'.format(end - tic))


def prepare_calculate_remote(trade_date):
    # 远程计算
    tp_solvency, ttm_solvency, mrq_solvency = get_basic_data(trade_date)
    print('len_tp_cash_flow: %s' % len(tp_solvency))
    print('len_ttm_cash_flow: %s' % len(ttm_solvency))
    print('tp_cash_flow: \n%s' % tp_solvency.head())
    print('ttm_cash_flow: \n%s' % ttm_solvency.head())

    if len(tp_solvency) <= 0 or len(ttm_solvency) <= 0 or len(mrq_solvency) <= 0:
        print("%s has no data" % trade_date)
        return
    else:
        tic = time.time()
        session = str(int(time.time() * 1000000 + datetime.now().microsecond))
        cache_data.set_cache(session + str(trade_date) + "1", trade_date, tp_solvency.to_json(orient='records'))
        cache_data.set_cache(session + str(trade_date) + "2", trade_date, ttm_solvency.to_json(orient='records'))
        cache_data.set_cache(session + str(trade_date) + "3", trade_date, mrq_solvency.to_json(orient='records'))
        factor_solvency.factor_calculate(date_index=trade_date, session=session)
        time4 = time.time()
        print('cash_flow_cal_time:{}'.format(time4 - tic))


def do_update(start_date, end_date, count):
    # 读取交易日
    syn_util = SyncUtil()
    trade_date_sets = syn_util.get_trades_ago('001002', start_date, end_date, count, order='DESC')
    trade_date_sets = trade_date_sets['TRADEDATE'].values
    print('交易日：%s' % trade_date_sets)
    for trade_date in trade_date_sets:
        print('因子计算日期： %s' % trade_date)
        prepare_calculate_local(trade_date)
    print('----->')


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--start_date', type=int, default=20070101)
    # parser.add_argument('--end_date', type=int, default=0)
    # parser.add_argument('--count', type=int, default=1)
    # parser.add_argument('--rebuild', type=bool, default=False)
    # parser.add_argument('--update', type=bool, default=False)
    # parser.add_argument('--schedule', type=bool, default=False)
    #
    # args = parser.parse_args()
    # if args.end_date == 0:
    #     end_date = int(datetime.now().date().strftime('%Y%m%d'))
    # else:
    #     end_date = args.end_date
    # if args.rebuild:
    #     processor = factor_cash_flow.FactorCashFlow('factor_cash_flow')
    #     processor.create_dest_tables()
    #     do_update(args.start_date, end_date, args.count)
    # if args.update:
    #     do_update(args.start_date, end_date, args.count)
    do_update('20190819', '20190823', 10)