#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
@version: 0.1
@author: li
@file: factor_valuation.py
@time: 2019-01-28 11:33
"""
import sys
sys.path.append("..")
import json
import math
import numpy as np
import pandas as pd
from pandas.io.json import json_normalize
import pdb
# from factor import app
from factor.factor_base import FactorBase
from factor.utillities.calc_tools import CalcTools
# from ultron.cluster.invoke.cache_data import cache_data
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

class Valuation(FactorBase):
    """
    估值
    """

    def __init__(self, name):
        super(Valuation, self).__init__(name)

    # 构建因子表
    def create_dest_tables(self):
        """
        创建数据库表
        :return:
        """
        drop_sql = """drop table if exists `{0}`""".format(self._name)

        create_sql = """create table `{0}`(
                    `id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO INCREMENT,
                    `security_code` varchar(24) NOT NULL,
                    `trade_date` date NOT NULL,
                    `LogofMktValue` decimal(19,4) NOT NULL,
                    `LogofNegMktValue` decimal(19,4),
                    `NLSIZE` decimal(19,4),
                    `MrktCapToCorFreeCashFlow` decimal(19,4),
                    `PBAvgOnSW1` decimal(19, 4),
                    `PBStdOnSW1` decimal(19,4),
                    `PEToAvg6M` decimal(19,4),
                    `PEToAvg3M` decimal(19,4),
                    `PEToAvg1M` decimal(19,4),
                    `PEToAvg1Y` decimal(19,4),
                    `TotalAssets` decimal(19,4),
                    `MktValue` decimal(19,4),
                    `CirMktValue` decimal(19,4),
                    `LogTotalAssets` decimal(19,4),
                    `BMInduAvgOnSW1` decimal(19,4),
                    `BMInduSTDOnSW1` decimal(19,4),
                    `BookValueToIndu` decimal(19,4),
                    `TotalAssetsToEnterpriseValue` decimal(19,4),
                    `LogSalesTTM` decimal(19,4),
                    `PCFToOptCashflowTTM` decimal(19,4),
                    `EPTTM` decimal(19,4),
                    `PEAvgOnSW1` decimal(19,4),
                    `PEStdOnSW1` decimal(19,4),
                    `PSAvgOnSW1` decimal(19,4),
                    `PSStdOnSW1` decimal(19,4),
                    `PCFAvgOnSW1` decimal(19,4),
                    `PCFStdOnSW1` decimal(19,4),
                    `PEIndu` decimal(19,4),
                    `PEIndu` decimal(19,4),
                    `PCFIndu` decimal(19,4),
                    `TotalMrktAVGToEBIDAOnSW1` decimal(19,4),
                    `TotalMrktSTDToEBIDAOnSW1` decimal(19,4),
                    `BookValueToIndu` decimal(19,4),
                    `PEG3YChgTTM` decimal(19,4),
                    `PEG5YChgTTM` decimal(19,4),
                    `CEToPTTM` decimal(19,4),
                    `RevToMrktRatioTTM` decimal(19,4),
                    `OptIncToEnterpriseValueTTM` decimal(19,4),
                    constraint {0} uindex
                    unique (`trade_date`,`security_code`)
                    )ENGINE=InnoDB DEFAULT CHARSET=utf8;""".format(self._name)
        super(Valuation, self)._create_tables(create_sql, drop_sql)

    @staticmethod
    def lcap(valuation_sets, factor_historical_value, dependencies=['market_cap']):
        """
        总市值的对数
        # 对数市值 即市值的对数
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """

        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: math.log(abs(x)) if x is not None and x != 0 else None

        historical_value['LogofMktValue'] = historical_value['market_cap'].apply(func)
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")
        # factor_historical_value['historical_value_lcap_latest'] = historical_value['historical_value_lcap_latest']
        return factor_historical_value

    @staticmethod
    def lflo(valuation_sets, factor_historical_value, dependencies=['circulating_market_cap']):
        """
        流通总市值的对数
        # 对数市值 即流通市值的对数
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """

        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: math.log(abs(x)) if x is not None and x != 0 else None

        historical_value['LogofNegMktValue'] = historical_value['circulating_market_cap'].apply(func)
        historical_value = historical_value.drop(columns=['circulating_market_cap'], axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")
        return factor_historical_value

    @staticmethod
    def nlsize(valuation_sets, factor_historical_value, dependencies=['market_cap']):
        """
        对数市值开立方
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """

        # 对数市值
        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: pow(math.log(abs(x)), 1/3.0) if x is not None and x != 0 else None
        historical_value['NLSIZE'] = historical_value['market_cap'].apply(func)
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")
        return factor_historical_value

    @staticmethod
    def market_cap_to_corporate_free_cash_flow(valuation_sets, factor_historical_value, dependencies=['market_cap', 'enterprise_fcfps']):
        """
        市值/企业自由现金流
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]

        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None

        historical_value['MrktCapToCorFreeCashFlow'] = historical_value.apply(func, axis=1)
        # historical_value = historical_value.drop(columns=['total_operating_revenue'], axis=1)
        # factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")
        factor_historical_value['MrktCapToCorFreeCashFlow'] = historical_value['MrktCapToCorFreeCashFlow']
        return factor_historical_value

    @staticmethod
    def pb_avg(valuation_sets, sw_industry, factor_historical_value=None, dependencies=['pb']):
        """
        pb 均值
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]
        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')
        historical_value_tmp = historical_value_tmp.mean().rename(columns={"pb": "PBAvgOnSW1"})

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def pb_std(valuation_sets, sw_industry, factor_historical_value=None, dependencies=['pb']):
        """
        pb 标准差
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]
        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')
        historical_value_tmp = historical_value_tmp.std().rename(columns={"pb": "PBStdOnSW1"})

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def pb_indu(valuation_sets, factor_historical_value, dependencies=['pb']):
        """
        # (Pb – Pb 的行业均值)/Pb 的行业标准差
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')

        factor_historical_value['PBIndu'] = (factor_historical_value['pb'] - factor_historical_value['PBAvgOnSW1']) / factor_historical_value["PBStdOnSW1"]
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def pe_to_pe_avg_over_6m(valuation_sets, factor_historical_value, dependencies=['pe', 'pe_mean_6m']):
        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None

        historical_value['PEToAvg6M'] = historical_value.apply(func, axis=1)
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")

        return factor_historical_value

    @staticmethod
    def pe_to_pe_avg_over_6m(valuation_sets, factor_historical_value, dependencies=['pe', 'pe_mean_6m']):
        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None

        historical_value['PEToAvg6M'] = historical_value.apply(func, axis=1)
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")

        return factor_historical_value

    @staticmethod
    def pe_to_pe_avg_over_3m(valuation_sets, factor_historical_value, dependencies=['pe', 'pe_mean_3m']):
        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None

        historical_value['PEToAvg3M'] = historical_value.apply(func, axis=1)
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")

        return factor_historical_value

    @staticmethod
    def pe_to_pe_avg_over_2m(valuation_sets, factor_historical_value, dependencies=['pe', 'pe_mean_2m']):
        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None

        historical_value['PEToAvg1M'] = historical_value.apply(func, axis=1)
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")

        return factor_historical_value

    @staticmethod
    def pe_to_pe_avg_over_1y(valuation_sets, factor_historical_value, dependencies=['pe', 'pe_mean_1y']):
        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None

        historical_value['PEToAvg1Y'] = historical_value.apply(func, axis=1)
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")

        return factor_historical_value

    @staticmethod
    def total_assert(valuation_sets, factor_historical_value, dependencies=['total_assets_report']):
        historical_value = valuation_sets.loc[:, dependencies]
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.rename(columns={"total_assets_report": "TotalAssets"})

        return factor_historical_value

    @staticmethod
    def market_value(valuation_sets, factor_historical_value, dependencies=['market_cap']):
        historical_value = valuation_sets.loc[:, dependencies]
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.rename(columns={"market_cap": "MktValue"})
        return factor_historical_value

    @staticmethod
    def circulating_market_value(valuation_sets, factor_historical_value, dependencies=['circulating_market_cap']):
        historical_value = valuation_sets.loc[:, dependencies]
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.rename(columns={"circulating_market_cap": "CirMktValue"})
        return factor_historical_value

    # MRQ
    @staticmethod
    def log_total_asset_mrq(valuation_sets, factor_historical_value, dependencies=['total_assets']):
        """
        对数总资产MRQ
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: math.log(abs(x)) if x is not None and x != 0 else None

        historical_value['LogTotalAssets'] = historical_value['total_assets'].apply(func)
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")
        # factor_historical_value['LogTotalAssets'] = historical_value['LogTotalAssets']
        return factor_historical_value

    @staticmethod
    def book_to_mrkt_to_indu_avg_value(valuation_sets, sw_industry, factor_historical_value,
                                       dependencies=['equities_parent_company_owners', 'market_cap']):
        """
        归属于母公司的股东权益（MRQ) / 总市值
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]

        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None
        valuation_sets['tmp'] = valuation_sets.apply(func, axis=1)

        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')

        historical_value_tmp = historical_value_tmp.mean().rename(columns={"tmp": "BMInduAvgOnSW1"})
        historical_value_tmp = historical_value_tmp['BMInduAvgOnSW1']

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol', 'tmp']
        historical_value = historical_value.drop(dependencies, axis=1)
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')

        return factor_historical_value

    @staticmethod
    def book_to_mrkt_to_indu_std_value(valuation_sets, sw_industry, factor_historical_value,
                                       dependencies=['equities_parent_company_owners', 'market_cap']):
        """
        归属于母公司的股东权益（MRQ) / 总市值
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]

        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None
        valuation_sets['tmp'] = valuation_sets.apply(func, axis=1)

        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')

        historical_value_tmp = historical_value_tmp.std().rename(columns={"tmp": "BMInduSTDOnSW1"})
        historical_value_tmp = historical_value_tmp['BMInduSTDOnSW1']

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol', 'tmp']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)
        return factor_historical_value

    @staticmethod
    def book_to_mrkt_to_indu(valuation_sets, factor_historical_value,
                             dependencies=['equities_parent_company_owners', 'market_cap']):
        """
        归属于母公司的股东权益（MRQ) / 总市值(行业)
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]

        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None
        valuation_sets['tmp'] = valuation_sets.apply(func, axis=1)

        factor_historical_value = pd.merge(valuation_sets, factor_historical_value, how='outer', on='security_code')

        factor_historical_value['BookValueToIndu'] = (factor_historical_value['tmp'] - factor_historical_value['BMInduAvgOnSW1'])\
                                                     / factor_historical_value["BMInduSTDOnSW1"]
        dependencies = dependencies + ['tmp']
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)
        return factor_historical_value

    @staticmethod
    def total_assets_to_enterprise(valuation_sets, factor_historical_value, dependencies=['total_assets_report',
                                                                                          'shortterm_loan',
                                                                                          'longterm_loan',
                                                                                          'market_cap',
                                                                                          'cash_and_equivalents_at_end',
                                                                                          ]):
        """
        资产总计/企业价值 MRQ
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]
        fuc = lambda x: x[1] + x[2] + x[3] - x[4]

        historical_value['temp'] = historical_value[dependencies].apply(fuc, axis=1)

        historical_value['TotalAssetsToEnterpriseValue'] = np.where(CalcTools.is_zero(historical_value['temp']), 0,
                                                                    historical_value['total_assets_report'] /
                                                                    historical_value['temp'])

        factor_historical_value['TotalAssetsToEnterpriseValue'] = historical_value['TotalAssetsToEnterpriseValue']
        return factor_historical_value

    # TTM
    @staticmethod
    def log_sales_ttm(valuation_sets, factor_historical_value, dependencies=['total_operating_revenue']):
        """
        对数营业收入(TTM)
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]

        func = lambda x: math.log(abs(x)) if x is not None and x != 0 else None
        historical_value['LogSalesTTM'] = historical_value['total_operating_revenue'].apply(func)
        historical_value = historical_value.drop(columns=dependencies, axis=1)

        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")
        # factor_historical_value['LogSalesTTM'] = historical_value['LogSalesTTM']
        return factor_historical_value

    @staticmethod
    def pcf_to_operating_cash_flow_ttm(valuation_sets, factor_historical_value, dependencies=['market_cap', 'net_operate_cash_flow']):
        """
        市现率PCF(经营现金流TTM)
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]
        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None
        historical_value['PCFToOptCashflowTTM'] = historical_value[dependencies].apply(func, axis=1)
        factor_historical_value['PCFToOptCashflowTTM'] = historical_value['PCFToOptCashflowTTM']
        return factor_historical_value

    @staticmethod
    def etop(valuation_sets, factor_historical_value, dependencies=['net_profit', 'market_cap']):
        """
        收益市值比= 净利润TTM/总市值
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """

        historical_value = valuation_sets.loc[:, dependencies]

        historical_value['EPTTM'] = np.where(CalcTools.is_zero(historical_value['market_cap']), 0,
                                             historical_value['net_profit'] /
                                             historical_value['market_cap'])
        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")
        # factor_historical_value['EPTTM'] = historical_value['EPTTM']
        return factor_historical_value

    @staticmethod
    def pe_deduction_ttm(valuation_sets, factor_historical_value, dependencies=['market_cap', 'net_profit_cut_pre']):
        """
        市盈率PE(TTM)（扣除）
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]

        historical_value['PECutTTM'] = np.where(CalcTools.is_zero(historical_value['net_profit_cut_pre']), 0,
                                                historical_value['market_cap'] /
                                                historical_value['net_profit_cut_pre'])

        factor_historical_value['PECutTTM'] = historical_value['PECutTTM']
        return factor_historical_value

    @staticmethod
    def pe_avg(valuation_sets, sw_industry, factor_historical_value, dependencies=['pe']):
        """
        pe 均值
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]
        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')
        historical_value_tmp = historical_value_tmp.mean().rename(columns={"pe": "PEAvgOnSW1"})
        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def pe_std(valuation_sets, sw_industry, factor_historical_value, dependencies=['pe']):
        """
        pe 标准差
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]
        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')
        historical_value_tmp = historical_value_tmp.std().rename(columns={"pe": "PEStdOnSW1"})
        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def ps_avg(valuation_sets, sw_industry, factor_historical_value, dependencies=['ps']):
        """
        ps 均值 TTM
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]
        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')
        historical_value_tmp = historical_value_tmp.mean().rename(columns={"ps": "PSAvgOnSW1"})

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def ps_std(valuation_sets, sw_industry, factor_historical_value, dependencies=['ps']):
        """
        ps 标准差 TTM
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]
        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')
        historical_value_tmp = historical_value_tmp.std().rename(columns={"ps": "PSStdOnSW1"})

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def pcf_avg(valuation_sets, sw_industry, factor_historical_value, dependencies=['pcf']):
        """
        pcf 均值
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]
        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')
        historical_value_tmp = historical_value_tmp.mean().rename(columns={"pcf": "PCFAvgOnSW1"})

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def pcf_std(valuation_sets, sw_industry, factor_historical_value, dependencies=['pcf']):
        """
        pcf 标准差
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]
        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')
        historical_value_tmp = historical_value_tmp.std().rename(columns={"pcf": "PCFStdOnSW1"})

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def pe_indu(tp_historical_value, factor_historical_value, dependencies=['pe']):
        """
        (PE – PE 的行业均值)/PE 的行业标准差 TTM
        :param dependencies:
        :param tp_historical_value:
        :param factor_historical_value:
        :return: PEIndu
        """

        historical_value = tp_historical_value.loc[:, dependencies]
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')

        factor_historical_value['PEIndu'] = (factor_historical_value['pe'] - factor_historical_value['PEAvgOnSW1']) / factor_historical_value["PEStdOnSW1"]
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def ps_indu(valuation_sets, factor_historical_value, dependencies=['ps']):
        """
        # (Ps – Ps 的行业均值)/Ps 的行业标准差 TTM
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')

        factor_historical_value['PSIndu'] = (factor_historical_value['ps'] - factor_historical_value['PSAvgOnSW1']) / factor_historical_value["PSStdOnSW1"]
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def pcf_indu(valuation_sets, factor_historical_value, dependencies=['pcf']):
        """
        # (Pcf – Pcf 的行业均值)/Pcf 的行业标准差 TTM
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')

        factor_historical_value['PCFIndu'] = (factor_historical_value['pcf'] - factor_historical_value['PCFAvgOnSW1']) / factor_historical_value["PCFStdOnSW1"]
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def total_mkt_avg_to_ebidta(valuation_sets, sw_industry, factor_historical_value,
                                dependencies=['market_cap', 'total_profit']):
        """
        总市值/ 利润总额TTM
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]

        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None
        valuation_sets['tmp'] = valuation_sets.apply(func, axis=1)

        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')

        historical_value_tmp = historical_value_tmp.mean().rename(columns={"tmp": "TotalMrktAVGToEBIDAOnSW1"})
        historical_value_tmp = historical_value_tmp['TotalMrktAVGToEBIDAOnSW1']

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol', 'tmp']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)

        return factor_historical_value

    @staticmethod
    def total_mkt_std_to_ebidta(valuation_sets, sw_industry, factor_historical_value,
                                dependencies=['market_cap', 'total_profit']):
        """
        总市值/ 利润总额TTM
        :param valuation_sets:
        :param sw_industry:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]

        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None
        valuation_sets['tmp'] = valuation_sets.apply(func, axis=1)

        valuation_sets = pd.merge(valuation_sets, sw_industry, how='outer', on='security_code')

        historical_value_tmp = valuation_sets.groupby('isymbol')

        historical_value_tmp = historical_value_tmp.std().rename(columns={"tmp": "TotalMrktSTDToEBIDAOnSW1"})
        historical_value_tmp = historical_value_tmp['TotalMrktSTDToEBIDAOnSW1']

        historical_value = pd.merge(valuation_sets, historical_value_tmp, how='outer', on='isymbol')

        dependencies = dependencies + ['isymbol', 'tmp']
        factor_historical_value = pd.merge(historical_value, factor_historical_value, how='outer', on='security_code')
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)
        return factor_historical_value

    @staticmethod
    def total_mkt_std_to_ebidta_indu(valuation_sets, factor_historical_value,
                                     dependencies=['market_cap', 'total_profit']):

        """
        总市值/ 利润总额TTM
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        valuation_sets = valuation_sets.loc[:, dependencies]

        func = lambda x: x[0] / x[1] if x[1] is not None and x[1] != 0 else None
        valuation_sets['tmp'] = valuation_sets.apply(func, axis=1)

        factor_historical_value = pd.merge(valuation_sets, factor_historical_value, how='outer', on='security_code')

        factor_historical_value['BookValueToIndu'] = (factor_historical_value['tmp'] - factor_historical_value['TotalMrktAVGToEBIDAOnSW1'])\
                                                     / factor_historical_value["TotalMrktSTDToEBIDAOnSW1"]
        dependencies = dependencies + ['tmp']
        factor_historical_value = factor_historical_value.drop(dependencies, axis=1)
        return factor_historical_value

    @staticmethod
    def peg_3y(valuation_sets, factor_historical_value, dependencies=['pe', 'np_parent_company_owners', 'np_parent_company_owners_3']):
        """
        # 市盈率/归属于母公司所有者净利润 3 年复合增长率
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """

        historical_value = valuation_sets.loc[:, dependencies]

        tmp = np.where(CalcTools.is_zero(historical_value['np_parent_company_owners_3']), 0,
                       (historical_value['np_parent_company_owners'] / historical_value['np_parent_company_owners_3']))
        historical_value['PEG3YChgTTM'] = tmp / abs(tmp) * pow(abs(tmp), 1 / 3.0) - 1

        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")
        return factor_historical_value

    @staticmethod
    def peg_5y(valuation_sets, factor_historical_value, dependencies=['pe', 'np_parent_company_owners', 'np_parent_company_owners_5']):
        """
        # 市盈率/归属于母公司所有者净利润 5 年复合增长率
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """

        historical_value = valuation_sets.loc[:, dependencies]

        tmp = np.where(CalcTools.is_zero(historical_value['np_parent_company_owners_5']), 0,
                       (historical_value['np_parent_company_owners'] / historical_value['np_parent_company_owners_5']))
        historical_value['PEG5YChgTTM'] = tmp / abs(tmp) * pow(abs(tmp), 1 / 5.0) - 1

        historical_value = historical_value.drop(columns=dependencies, axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, how='outer', on="security_code")
        # factor_historical_value['PEG5YChgTTM'] = historical_value['PEG5YChgTTM']
        return factor_historical_value

    @staticmethod
    def cetop(valuation_sets, factor_historical_value, dependencies=['net_operate_cash_flow', 'market_cap']):
        """
        现金收益滚动收益与市值比
        经营活动产生的现金流量净额与市值比
        :param dependencies:
        :param valuation_sets:
        :param factor_historical_value:
        :return:
        """

        historical_value = valuation_sets.loc[:, dependencies]

        historical_value['CEToPTTM'] = np.where(CalcTools.is_zero(historical_value['market_cap']), 0,
                                                historical_value['net_operate_cash_flow'] /
                                                historical_value['market_cap'])

        historical_value = historical_value.drop(columns=['net_operate_cash_flow', 'market_cap'], axis=1)
        factor_historical_value = pd.merge(factor_historical_value, historical_value, on="security_code")

        return factor_historical_value

    @staticmethod
    def revenue_to_market_ratio_ttm(valuation_sets, factor_historical_value, dependencies=['operating_revenue',
                                                                                           'market_cap']):
        """
        营收市值比(TTM)
        营业收入（TTM）/总市值
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]

        historical_value['RevToMrktRatioTTM'] = np.where(CalcTools.is_zero(historical_value['market_cap']), 0,
                                                historical_value['operating_revenue'] /
                                                historical_value['market_cap'])

        factor_historical_value['RevToMrktRatioTTM'] = historical_value['RevToMrktRatioTTM']
        return factor_historical_value

    @staticmethod
    def operating_to_enterprise_ttm(valuation_sets, factor_historical_value, dependencies=['operating_revenue',
                                                                                           'shortterm_loan',
                                                                                           'longterm_loan',
                                                                                           'market_cap',
                                                                                           'cash_and_equivalents_at_end',
                                                                                           ]):
        """
        营业收入(TTM)/企业价值
        企业价值= 长期借款+ 短期借款+ 总市值- 现金及现金等价物
        :param valuation_sets:
        :param factor_historical_value:
        :param dependencies:
        :return:
        """
        historical_value = valuation_sets.loc[:, dependencies]

        fuc = lambda x: x[1] + x[2] + x[3] - x[4]

        historical_value['temp'] = historical_value[dependencies].apply(fuc, axis=1)

        historical_value['OptIncToEnterpriseValueTTM'] = np.where(CalcTools.is_zero(historical_value['temp']), 0,
                                                                  historical_value['operating_revenue'] /
                                                                  historical_value['temp'])

        factor_historical_value['OptIncToEnterpriseValueTTM'] = historical_value['OptIncToEnterpriseValueTTM']
        return factor_historical_value


def calculate(trade_date, valuation_sets, sw_industry, pe_sets):
    """
    :param pe_sets:
    :param sw_industry:
    :param valuation_sets:
    :param trade_date:
    :return:
    """
    valuation_sets = valuation_sets.set_index('security_code')
    pe_sets = pe_sets.set_index('security_code')
    historical_value = Valuation('factor_historical_value')

    factor_historical_value = pd.DataFrame()
    factor_historical_value['security_code'] = valuation_sets.index
    factor_historical_value = factor_historical_value.set_index('security_code')

    # psindu
    factor_historical_value = historical_value.lcap(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.lflo(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.nlsize(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.market_cap_to_corporate_free_cash_flow(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.pb_avg(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.pb_std(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.pb_indu(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.total_assert(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.market_value(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.circulating_market_value(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.log_total_asset_mrq(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.book_to_mrkt_to_indu_avg_value(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.book_to_mrkt_to_indu_std_value(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.book_to_mrkt_to_indu(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.pe_to_pe_avg_over_6m(pe_sets, factor_historical_value)
    factor_historical_value = historical_value.pe_to_pe_avg_over_3m(pe_sets, factor_historical_value)
    factor_historical_value = historical_value.pe_to_pe_avg_over_2m(pe_sets, factor_historical_value)
    factor_historical_value = historical_value.pe_to_pe_avg_over_1y(pe_sets, factor_historical_value)
    factor_historical_value = historical_value.total_assets_to_enterprise(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.log_sales_ttm(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.pcf_to_operating_cash_flow_ttm(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.etop(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.pe_deduction_ttm(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.pe_avg(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.pe_std(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.ps_avg(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.ps_std(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.pcf_avg(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.pcf_std(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.pe_indu(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.ps_indu(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.pcf_indu(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.total_mkt_avg_to_ebidta(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.total_mkt_std_to_ebidta(valuation_sets, sw_industry, factor_historical_value)
    factor_historical_value = historical_value.total_mkt_std_to_ebidta_indu(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.peg_3y(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.peg_5y(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.cetop(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.revenue_to_market_ratio_ttm(valuation_sets, factor_historical_value)
    factor_historical_value = historical_value.operating_to_enterprise_ttm(valuation_sets, factor_historical_value)

    # etp5 因子没有提出， 使用该部分的时候， 数据库字段需要添加
    # factor_historical_value = factor_historical_value[['security_code', 'PSIndu',
    #                                                    'historical_value_etp5_ttm',
    #                                                    'EPTTM',
    #                                                    'PEIndu', 'PEG3YChgTTM',
    #                                                    'PEG5YChgTTM', 'PBIndu',
    #                                                    'historical_value_lcap_latest',
    #                                                    'historical_value_lflo_latest',
    #                                                    'historical_value_nlsize_latest',
    #                                                    'PCFIndu',
    #                                                    'CEToPTTM',
    #                                                    'historical_value_ctop_latest',
    #                                                    'historical_value_ctop5_latest']]
    # factor_historical_value = factor_historical_value[['security_code',
    #                                                    'PSIndu',
    #                                                    'EPTTM',
    #                                                    'PEIndu',
    #                                                    'PEG3YChgTTM',
    #                                                    'PEG5YChgTTM',
    #                                                    'PBIndu',
    #                                                    'PCFIndu',
    #                                                    'CEToPTTM',
    #                                                    ]]

    factor_historical_value['id'] = factor_historical_value['security_code'] + str(trade_date)
    factor_historical_value['trade_date'] = str(trade_date)
    # historical_value._storage_data(factor_historical_value, trade_date)


# @app.task()
def factor_calculate(**kwargs):
    print("history_value_kwargs: {}".format(kwargs))
    date_index = kwargs['date_index']
    session = kwargs['session']
    # historical_value = Valuation('factor_historical_value')  # 注意, 这里的name要与client中新建table时的name一致, 不然回报错
    content = cache_data.get_cache(session + str(date_index), date_index)
    total_history_data = json_normalize(json.loads(str(content, encoding='utf8')))
    print("len_history_value_data {}".format(len(total_history_data)))
    calculate(date_index, total_history_data)

