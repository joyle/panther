# -*- coding: utf-8 -*-

import pdb, importlib, inspect, time, datetime, json
# from PyFin.api import advanceDateByCalendar
# from data.polymerize import DBPolymerize
from data.storage_engine import StorageEngine
import time
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
from valuation_estimation import factor_valuation_estimation

from vision.db.signletion_engine import get_fin_consolidated_statements_pit, get_fundamentals, query
from vision.table.industry_daily import IndustryDaily
from vision.table.fin_cash_flow import FinCashFlow
from vision.table.fin_balance import FinBalance
from vision.table.fin_income import FinIncome
from vision.table.fin_indicator import FinIndicator

from vision.table.fin_indicator_ttm import FinIndicatorTTM
from vision.table.fin_income_ttm import FinIncomeTTM
from vision.table.fin_cash_flow_ttm import FinCashFlowTTM

from vision.db.signletion_engine import *
from vision.table.valuation import Valuation
from vision.table.industry import Industry
from vision.table.stk_daily_price import SkDailyPrice
from data.sqlengine import sqlEngine
from utilities.sync_util import SyncUtil


# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# from ultron.cluster.invoke.cache_data import cache_data


class CalcEngine(object):
    def __init__(self, name, url, methods=[
        {'packet': 'valuation_estimation.factor_valuation_estimation', 'class': 'FactorValuationEstimation'}]):
        self._name = name
        self._methods = methods
        self._url = url

    def get_trade_date(self, trade_date, n, days=365):
        """
        获取当前时间前n年的时间点，且为交易日，如果非交易日，则往前提取最近的一天。
        :param days:
        :param trade_date: 当前交易日
        :param n:
        :return:
        """
        syn_util = SyncUtil()
        trade_date_sets = syn_util.get_all_trades('001002', '19900101', trade_date)
        trade_date_sets = trade_date_sets['TRADEDATE'].values

        time_array = datetime.strptime(str(trade_date), "%Y%m%d")
        time_array = time_array - timedelta(days=days) * n
        date_time = int(datetime.strftime(time_array, "%Y%m%d"))
        if str(date_time) < min(trade_date_sets):
            # print('date_time %s is out of trade_date_sets' % date_time)
            return str(date_time)
        else:
            while str(date_time) not in trade_date_sets:
                date_time = date_time - 1
            # print('trade_date pre %s year %s' % (n, date_time))
            return str(date_time)

    def _func_sets(self, method):
        # 私有函数和保护函数过滤
        return list(filter(lambda x: not x.startswith('_') and callable(getattr(method, x)), dir(method)))

    def loading_data(self, trade_date):

        """
        获取基础数据
        按天获取当天交易日所有股票的基础数据
        :param trade_date: 交易日
        :return:
        """
        time_array = datetime.strptime(trade_date, "%Y-%m-%d")
        trade_date = datetime.strftime(time_array, '%Y%m%d')
        engine = sqlEngine()
        trade_date_pre = self.get_trade_date(trade_date, 1, days=30)
        trade_date_1y = self.get_trade_date(trade_date, 1)
        trade_date_3y = self.get_trade_date(trade_date, 3)
        trade_date_4y = self.get_trade_date(trade_date, 4)
        trade_date_5y = self.get_trade_date(trade_date, 5)

        # report data
        columns = ['COMPCODE', 'PUBLISHDATE', 'ENDDATE', 'symbol', 'company_id', 'trade_date']
        balance_report = engine.fetch_fundamentals_pit_extend_company_id(FinBalance,
                                                                         [FinBalance.total_assets,
                                                                          ], dates=[trade_date])
        if len(balance_report) <= 0 or balance_report is None:
            balance_report = pd.DataFrame({'security_code': [], 'total_assets': []})

        for column in columns:
            if column in list(balance_report.keys()):
                balance_report = balance_report.drop(column, axis=1)
        balance_report = balance_report.rename(columns={
            'total_assets': 'total_assets_report',  # 资产总计
        })
        # valuation_report_sets = pd.merge(indicator_sets, balance_report, how='outer', on='security_code')

        # MRQ data
        cash_flow_mrq = engine.fetch_fundamentals_pit_extend_company_id(FinCashFlow,
                                                                        [FinCashFlow.cash_and_equivalents_at_end,
                                                                         ], dates=[trade_date])
        if len(cash_flow_mrq) <= 0 or cash_flow_mrq is None:
            cash_flow_mrq = pd.DataFrame({'security_code': [], 'cash_and_equivalents_at_end': []})

        for column in columns:
            if column in list(cash_flow_mrq.keys()):
                cash_flow_mrq = cash_flow_mrq.drop(column, axis=1)
        cash_flow_mrq = cash_flow_mrq.rename(columns={
            'cash_and_equivalents_at_end': 'cash_and_equivalents_at_end',  # 期末现金及现金等价物余额
        })

        balance_mrq = engine.fetch_fundamentals_pit_extend_company_id(FinBalance,
                                                                      [FinBalance.longterm_loan,  # 短期借款
                                                                       FinBalance.total_assets,  # 资产总计
                                                                       FinBalance.shortterm_loan,  # 短期借款
                                                                       FinBalance.equities_parent_company_owners,
                                                                       # 归属于母公司股东权益合计
                                                                       ], dates=[trade_date])
        if len(balance_mrq) <= 0 or balance_mrq is None:
            balance_mrq = pd.DataFrame(
                {'security_code': [], 'longterm_loan': [], 'total_assets': [], 'shortterm_loan': [],
                 'equities_parent_company_owners': []})
        for column in columns:
            if column in list(balance_mrq.keys()):
                balance_mrq = balance_mrq.drop(column, axis=1)

        balance_mrq = balance_mrq.rename(columns={
            'shortterm_loan': 'shortterm_loan',  # 短期借款
            'longterm_loan': 'longterm_loan',  # 长期借款
            'total_assets': 'total_assets',  # 资产总计
            'equities_parent_company_owners': 'equities_parent_company_owners',  # 归属于母公司股东权益合计
        })
        valuation_mrq = pd.merge(cash_flow_mrq, balance_mrq, on='security_code')

        indicator_sets = engine.fetch_fundamentals_pit_extend_company_id(FinIndicator,
                                                                         [FinIndicator.np_cut,
                                                                          ], dates=[trade_date])
        for col in columns:
            if col in list(indicator_sets.keys()):
                indicator_sets = indicator_sets.drop(col, axis=1)
        # indicator_sets = indicator_sets.rename(columns={'EBIT': 'ebit_mrq'})
        valuation_mrq = pd.merge(indicator_sets, valuation_mrq, how='outer', on='security_code')

        income_sets = engine.fetch_fundamentals_pit_extend_company_id(FinIncome,
                                                                      [FinIncome.income_tax,  # 所得税
                                                                       ], dates=[trade_date])
        for col in columns:
            if col in list(income_sets.keys()):
                income_sets = income_sets.drop(col, axis=1)
        valuation_mrq = pd.merge(income_sets, valuation_mrq, how='outer', on='security_code')

        cash_flow_sets = engine.fetch_fundamentals_pit_extend_company_id(FinCashFlow,
                                                                         [FinCashFlow.fixed_assets_depreciation,
                                                                          # 固定资产折旧
                                                                          FinCashFlow.intangible_assets_amortization,
                                                                          # 无形资产摊销
                                                                          FinCashFlow.fix_intan_other_asset_acqui_cash,
                                                                          # 购建固定资产、无形资产和其他...
                                                                          FinCashFlow.defferred_expense_amortization,
                                                                          # 长期待摊费用摊销
                                                                          FinCashFlow.borrowing_repayment,  # 偿还债务支付的现金
                                                                          FinCashFlow.cash_from_borrowing,  # 取得借款收到的现金
                                                                          FinCashFlow.cash_from_bonds_issue,
                                                                          # 发行债券所收到的现金
                                                                          ], dates=[trade_date])
        for col in columns:
            if col in list(cash_flow_sets.keys()):
                cash_flow_sets = cash_flow_sets.drop(col, axis=1)
        valuation_mrq = pd.merge(cash_flow_sets, valuation_mrq, how='outer', on='security_code')

        balance_sets = engine.fetch_fundamentals_pit_extend_company_id(FinBalance,
                                                                       [FinBalance.shortterm_loan,
                                                                        FinBalance.total_current_assets,  # 流动资产合计
                                                                        FinBalance.total_current_liability,  # 流动负债合计
                                                                        ], dates=[trade_date])
        for col in columns:
            if col in list(balance_sets.keys()):
                balance_sets = balance_sets.drop(col, axis=1)
        valuation_mrq = pd.merge(balance_sets, valuation_mrq, how='outer', on='security_code')

        balance_sets_pre = engine.fetch_fundamentals_pit_extend_company_id(FinBalance,
                                                                           [FinBalance.total_current_assets,  # 流动资产合计
                                                                            FinBalance.total_current_liability,
                                                                            # 流动负债合计
                                                                            ], dates=[trade_date_pre])

        for col in columns:
            if col in list(balance_sets_pre.keys()):
                balance_sets_pre = balance_sets_pre.drop(col, axis=1)
        balance_sets_pre = balance_sets_pre.rename(columns={
            'total_current_assets': 'total_current_assets_pre',
            'total_current_liability': 'total_current_liability_pre',
        })
        valuation_mrq = pd.merge(balance_sets_pre, valuation_mrq, how='outer', on='security_code')

        # TTM data
        # 总市值合并到TTM数据中，
        cash_flow_ttm_sets = engine.fetch_fundamentals_pit_extend_company_id(FinCashFlowTTM,
                                                                             [FinCashFlowTTM.net_operate_cash_flow,
                                                                              ], dates=[trade_date])

        if len(cash_flow_ttm_sets) <= 0 or cash_flow_ttm_sets is None:
            cash_flow_ttm_sets = pd.DataFrame({'security_code': [], 'net_operate_cash_flow': []})

        for column in columns:
            if column in list(cash_flow_ttm_sets.keys()):
                cash_flow_ttm_sets = cash_flow_ttm_sets.drop(column, axis=1)
        cash_flow_ttm_sets = cash_flow_ttm_sets.rename(columns={
            'net_operate_cash_flow': 'net_operate_cash_flow',  # 经营活动现金流量净额
        })

        indicator_ttm_sets = engine.fetch_fundamentals_pit_extend_company_id(FinIndicatorTTM,
                                                                             [FinIndicatorTTM.np_cut,
                                                                              ], dates=[trade_date_1y])
        if len(indicator_ttm_sets) <= 0 or indicator_ttm_sets is None:
            indicator_ttm_sets = pd.DataFrame({'security_code': [], 'np_cut': []})

        for column in columns:
            if column in list(indicator_ttm_sets.keys()):
                indicator_ttm_sets = indicator_ttm_sets.drop(column, axis=1)

        income_ttm_sets = engine.fetch_fundamentals_pit_extend_company_id(FinIncomeTTM,
                                                                          [FinIncomeTTM.net_profit,
                                                                           FinIncomeTTM.np_parent_company_owners,
                                                                           FinIncomeTTM.total_operating_revenue,
                                                                           FinIncomeTTM.operating_revenue,
                                                                           FinIncomeTTM.total_profit,
                                                                           ], dates=[trade_date])
        if len(income_ttm_sets) <= 0 or income_ttm_sets is None:
            income_ttm_sets = pd.DataFrame(
                {'security_code': [], 'net_profit': [], 'np_parent_company_owners': [], 'total_operating_revenue': [],
                 'operating_revenue': [], 'total_profit': []})

        for column in columns:
            if column in list(income_ttm_sets.keys()):
                income_ttm_sets = income_ttm_sets.drop(column, axis=1)
        income_ttm_sets = income_ttm_sets.rename(columns={
            'total_profit': 'total_profit',  # 利润总额 ttm
            'net_profit': 'net_profit',  # 净利润
            'np_parent_company_owners': 'np_parent_company_owners',  # 归属于母公司所有者的净利润
            'total_operating_revenue': 'total_operating_revenue',  # 营业总收入
            'operating_revenue': 'operating_revenue',  # 营业收入
        })

        income_ttm_sets_3 = engine.fetch_fundamentals_pit_extend_company_id(FinIncomeTTM,
                                                                            [FinIncomeTTM.np_parent_company_owners,
                                                                             ], dates=[trade_date_3y])
        if len(income_ttm_sets_3) <= 0 or income_ttm_sets_3 is None:
            income_ttm_sets_3 = pd.DataFrame({'security_code': [], 'np_parent_company_owners': []})

        for column in columns:
            if column in list(income_ttm_sets_3.keys()):
                income_ttm_sets_3 = income_ttm_sets_3.drop(column, axis=1)
        income_ttm_sets_3 = income_ttm_sets_3.rename(columns={
            'np_parent_company_owners': 'np_parent_company_owners_3',  # 归属于母公司所有者的净利润
        })

        income_ttm_sets_5 = engine.fetch_fundamentals_pit_extend_company_id(FinIncomeTTM,
                                                                            [FinIncomeTTM.np_parent_company_owners,
                                                                             ], dates=[trade_date_5y])
        if len(income_ttm_sets_5) <= 0 or income_ttm_sets_5 is None:
            income_ttm_sets_5 = pd.DataFrame({'security_code': [], 'np_parent_company_owners': []})

        for column in columns:
            if column in list(income_ttm_sets_5.keys()):
                income_ttm_sets_5 = income_ttm_sets_5.drop(column, axis=1)
        income_ttm_sets_5 = income_ttm_sets_5.rename(columns={
            'np_parent_company_owners': 'np_parent_company_owners_5',  # 归属于母公司所有者的净利润
        })

        valuation_ttm_sets = pd.merge(cash_flow_ttm_sets, income_ttm_sets, how='outer', on='security_code')
        valuation_ttm_sets = pd.merge(valuation_ttm_sets, indicator_ttm_sets, how='outer', on='security_code')
        valuation_ttm_sets = pd.merge(valuation_ttm_sets, income_ttm_sets_3, how='outer', on='security_code')
        valuation_ttm_sets = pd.merge(valuation_ttm_sets, income_ttm_sets_5, how='outer', on='security_code')

        # 流通市值，总市值
        column = ['trade_date']
        sk_daily_price_sets = get_fundamentals(query(SkDailyPrice.security_code,
                                                     SkDailyPrice.trade_date,
                                                     SkDailyPrice.tot_market_cap,
                                                     SkDailyPrice.circulating_market_cap
                                                     ).filter(SkDailyPrice.trade_date.in_([trade_date])))
        if len(sk_daily_price_sets) <= 0 or sk_daily_price_sets is None:
            sk_daily_price_sets = pd.DataFrame({'security_code': [],
                                                'tot_market_cap': [],
                                                'circulating_market_cap': []})
        for col in column:
            if col in list(sk_daily_price_sets.keys()):
                sk_daily_price_sets = sk_daily_price_sets.drop(col, axis=1)

        # PS, PE, PB, PCF
        column = ['trade_date']
        valuation_sets = get_fundamentals(query(Valuation.security_code,
                                                Valuation.trade_date,
                                                Valuation.pe,
                                                Valuation.ps,
                                                Valuation.pb,
                                                Valuation.pcf,
                                                ).filter(Valuation.trade_date.in_([trade_date])))
        if len(valuation_sets) <= 0 or valuation_sets is None:
            valuation_sets = pd.DataFrame({'security_code': [],
                                           'pe': [],
                                           'ps': [],
                                           'pb': [],
                                           'pcf': []})
        for col in column:
            if col in list(valuation_sets.keys()):
                valuation_sets = valuation_sets.drop(col, axis=1)

        trade_date_6m = self.get_trade_date(trade_date, 1, 180)
        trade_date_3m = self.get_trade_date(trade_date, 1, 90)
        # trade_date_2m = self.get_trade_date(trade_date, 1, 60)
        trade_date_1m = self.get_trade_date(trade_date, 1, 30)

        pe_set = get_fundamentals(query(Valuation.security_code,
                                        Valuation.trade_date,
                                        Valuation.pe,
                                        ).filter(Valuation.trade_date.in_([trade_date])))
        if len(pe_set) <= 0 or pe_set is None:
            pe_set = pd.DataFrame({'security_code': [], 'pe': []})
        for col in column:
            if col in list(pe_set.keys()):
                pe_set = pe_set.drop(col, axis=1)

        pe_sets_6m = get_fundamentals(query(Valuation.security_code,
                                            Valuation.trade_date,
                                            Valuation.pe)
                                      .filter(Valuation.trade_date.between(trade_date_6m, trade_date)))
        if len(pe_sets_6m) <= 0 or pe_sets_6m is None:
            pe_sets_6m = pd.DataFrame({'security_code': [], 'pe': []})
        for col in column:
            if col in list(pe_sets_6m.keys()):
                pe_sets_6m = pe_sets_6m.drop(col, axis=1)

        pe_sets_6m = pe_sets_6m.groupby('security_code').mean().rename(columns={'pe': 'pe_mean_6m'})

        pe_sets_3m = get_fundamentals(query(Valuation.security_code,
                                            Valuation.trade_date,
                                            Valuation.pe)
                                      .filter(Valuation.trade_date.between(trade_date_3m, trade_date)))

        if len(pe_sets_3m) <= 0 or pe_sets_3m is None:
            pe_sets_3m = pd.DataFrame({'security_code': [], 'pe': []})

        for col in column:
            if col in list(pe_sets_3m.keys()):
                pe_sets_3m = pe_sets_3m.drop(col, axis=1)

        pe_sets_3m = pe_sets_3m.groupby('security_code').mean().rename(columns={'pe': 'pe_mean_3m'})

        pe_sets_2m = get_fundamentals(query(Valuation.security_code,
                                            Valuation.trade_date,
                                            Valuation.pe)
                                      .filter(Valuation.trade_date.between(trade_date_1m, trade_date)))

        if len(pe_sets_2m) <= 0 or pe_sets_2m is None:
            pe_sets_2m = pd.DataFrame({'security_code': [], 'pe': []})

        for col in column:
            if col in list(pe_sets_2m.keys()):
                pe_sets_2m = pe_sets_2m.drop(col, axis=1)

        pe_sets_2m = pe_sets_2m.groupby('security_code').mean().rename(columns={'pe': 'pe_mean_1m'})

        pe_sets_1y = get_fundamentals(query(Valuation.security_code,
                                            Valuation.trade_date,
                                            Valuation.pe)
                                      .filter(Valuation.trade_date.between(trade_date_1y, trade_date)))

        if len(pe_sets_1y) <= 0 or pe_sets_1y is None:
            pe_sets_1y = pd.DataFrame({'security_code': [], 'pe': []})

        for col in column:
            if col in list(pe_sets_1y.keys()):
                pe_sets_1y = pe_sets_1y.drop(col, axis=1)

        pe_sets_1y = pe_sets_1y.groupby('security_code').mean().rename(columns={'pe': 'pe_mean_1y'})

        pe_sets = pd.merge(pe_sets_6m, pe_sets_3m, how='outer', on='security_code')
        pe_sets = pd.merge(pe_sets, pe_sets_2m, how='outer', on='security_code')
        pe_sets = pd.merge(pe_sets, pe_sets_1y, how='outer', on='security_code')
        pe_sets = pd.merge(pe_sets, pe_set, how='outer', on='security_code')

        industry_set = ['801010', '801020', '801030', '801040', '801050', '801080', '801110', '801120', '801130',
                        '801140', '801150', '801160', '801170', '801180', '801200', '801210', '801230', '801710',
                        '801720', '801730', '801740', '801750', '801760', '801770', '801780', '801790', '801880',
                        '801890']
        column_sw = ['trade_date', 'symbol', 'company_id']
        sw_indu = get_fundamentals_extend_internal(query(Industry.trade_date,
                                                         Industry.symbol,
                                                         Industry.isymbol)
                                                   .filter(Industry.trade_date.in_([trade_date])),
                                                   internal_type='symbol')
        for col in column_sw:
            if col in list(sw_indu.keys()):
                sw_indu = sw_indu.drop(col, axis=1)
        sw_indu = sw_indu[sw_indu['isymbol'].isin(industry_set)]
        # valuation_sets = pd.merge(valuation_sets, indicator_sets, how='outer', on='security_code')
        valuation_sets = pd.merge(valuation_sets, balance_report, how='outer', on='security_code')
        valuation_sets = pd.merge(valuation_sets, valuation_mrq, how='outer', on='security_code')
        valuation_sets = pd.merge(valuation_sets, valuation_ttm_sets, how='outer', on='security_code')
        valuation_sets = pd.merge(valuation_sets, sk_daily_price_sets, how='outer', on='security_code')

        # valuation_sets['tot_market_cap'] = valuation_sets['tot_market_cap'] * 10000
        # valuation_sets['circulating_market_cap'] = valuation_sets['circulating_market_cap'] * 10000
        return valuation_sets, sw_indu, pe_sets

    def process_calc_factor(self, trade_date, valuation_sets, pe_sets, sw_industry):
        valuation_sets = valuation_sets.set_index('security_code')
        pe_sets = pe_sets.set_index('security_code')
        historical_value = factor_valuation_estimation.FactorValuationEstimation()

        factor_historical_value = pd.DataFrame()
        factor_historical_value['security_code'] = valuation_sets.index
        factor_historical_value = factor_historical_value.set_index('security_code')

        # psindu
        factor_historical_value = historical_value.LogofMktValue(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.LogofNegMktValue(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.NLSIZE(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.MrktCapToCorFreeCashFlow(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.PBAvgOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.PBStdOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.PBIndu(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.PEToAvg6M(pe_sets, factor_historical_value)
        factor_historical_value = historical_value.PEToAvg3M(pe_sets, factor_historical_value)
        factor_historical_value = historical_value.PEToAvg1M(pe_sets, factor_historical_value)
        factor_historical_value = historical_value.PEToAvg1Y(pe_sets, factor_historical_value)
        factor_historical_value = historical_value.MktValue(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.CirMktValue(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.LogTotalAssets(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.BMInduAvgOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.BMInduSTDOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.BookValueToIndu(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.TotalAssetsToEnterpriseValue(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.LogSalesTTM(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.PCFToOptCashflowTTM(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.EPTTM(valuation_sets, factor_historical_value)
        # factor_historical_value = historical_value.PECutTTM(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.PEAvgOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.PEStdOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.PSAvgOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.PSStdOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.PCFAvgOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.PCFStdOnSW1(valuation_sets, sw_industry, factor_historical_value)
        factor_historical_value = historical_value.PEIndu(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.PSIndu(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.PCFIndu(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.TotalMrktAVGToEBIDAOnSW1(valuation_sets, sw_industry,
                                                                            factor_historical_value)
        factor_historical_value = historical_value.TotalMrktSTDToEBIDAOnSW1(valuation_sets, sw_industry,
                                                                            factor_historical_value)
        factor_historical_value = historical_value.TotalMrktToEBIDATTM(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.PEG3YTTM(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.PEG5YTTM(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.CEToPTTM(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.RevToMrktRatioTTM(valuation_sets, factor_historical_value)
        factor_historical_value = historical_value.OptIncToEnterpriseValueTTM(valuation_sets, factor_historical_value)

        # factor_historical_value = factor_historical_value.reset_index()
        factor_historical_value['trade_date'] = str(trade_date)
        factor_historical_value.replace([-np.inf, np.inf, None], np.nan, inplace=True)
        return factor_historical_value

    def local_run(self, trade_date):
        print('当前交易日； %s' % trade_date)
        tic = time.time()
        valuation_sets, sw_industry, pe_sets = self.loading_data(trade_date)
        print('data load time %s' % (time.time() - tic))
        # 保存
        storage_engine = StorageEngine(self._url)
        result = self.process_calc_factor(trade_date, valuation_sets, pe_sets, sw_industry)
        print('cal_time %s' % (time.time() - tic))
        storage_engine.update_destdb(str(self._methods[-1]['packet'].split('.')[-1]), trade_date, result)
        print('----------------->')
        # storage_engine.update_destdb('factor_valuation', trade_date, result)

    # def remote_run(self, trade_date):
    #     total_data = self.loading_data(trade_date)
    #     #存储数据
    #     session = str(int(time.time() * 1000000 + datetime.datetime.now().microsecond))
    #     cache_data.set_cache(session, 'alphax', total_data.to_json(orient='records'))
    #     distributed_factor.delay(session, json.dumps(self._methods), self._name)
    #
    # def distributed_factor(self, total_data):
    #     mkt_df = self.calc_factor_by_date(total_data,trade_date)
    #     result = self.calc_factor('alphax.alpha191','Alpha191',mkt_df,trade_date)

# @app.task
# def distributed_factor(session, trade_date, packet_sets, name):
#     calc_engines = CalcEngine(name, packet_sets)
#     content = cache_data.get_cache(session, factor_name)
#     total_data = json_normalize(json.loads(content))
#     calc_engines.distributed_factor(total_data)

# # @app.task()
# def factor_calculate(**kwargs):
#     print("history_value_kwargs: {}".format(kwargs))
#     date_index = kwargs['date_index']
#     session = kwargs['session']
#     # historical_value = Valuation('factor_historical_value')  # 注意, 这里的name要与client中新建table时的name一致, 不然回报错
#     content = cache_data.get_cache(session + str(date_index), date_index)
#     total_history_data = json_normalize(json.loads(str(content, encoding='utf8')))
#     print("len_history_value_data {}".format(len(total_history_data)))
#     calculate(date_index, total_history_data)
