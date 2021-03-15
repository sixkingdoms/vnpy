from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from datetime import datetime
from vnpy.trader.object import ContractData, SpreadData, Direction, Offset
from vnpy.trader.utility import get_folder_path
import os
import numpy as np
import pandas as pd


class SpreadArbitrage(CtaTemplate):
    author = 'g_liu'

    # leg1_coef = 1.0
    # leg2_coef = -1.0

    basis_indicator = 0
    limit = 0
    fast_window = 5
    slow_window = 10
    active_order = True
    upper_limit = 200
    lower_limit = 0
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0

    spread: SpreadData
    # comma split spread
    vt_symbols = ''
    weights = ''
    basis = 0
    vt_symbol_list = []
    weight_list = [1, -1]
    pos_list = []
    parameters = ['vt_symbols', 'weights', 'fast_window', 'slow_window']
    variables = ['basis','pos_list', 'fast_ma0', 'fast_ma1', 'slow_ma0', 'slow_ma1', 'weight_list']

    def __init__(self, cta_engine, strategy_name, spreadTicker, setting):
        super(SpreadArbitrage, self).__init__(
            cta_engine, strategy_name, spreadTicker, setting
        )
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(1)

        self.vt_symbol_list = []
        self.weight_list = []
        self.abs_weight_list = []
        self.pos_list = []
        self.trades_df = pd.DataFrame()

    def convert_spread_ticker(self):
        if self.vt_symbols != '' and self.weights != '':
            self.vt_symbol_list = self.vt_symbols.split(',')
            self.weight_list = [float(x) for x in self.weights.split(',')]
            self.abs_weight_list = [abs(x) for x in self.weight_list]
            self.vt_symbol = 'SP_%s' % self.vt_symbols

            assert (len(self.weight_list) == len(self.vt_symbol_list))
            self.write_log('converting spread ticker: %s' % (' '.join(self.vt_symbol_list)))
            self.spread = SpreadData(ticker=self.vt_symbol, leg_str_list=self.vt_symbol_list, coef_list=self.weight_list)
            self.pos_list = [0] * len(self.vt_symbol_list)

    def on_init(self):
        self.write_log('Init Strategy')
        # self.put_event()
        self.convert_spread_ticker()
        #self.load_bar(10)
        for vt_symbol in self.vt_symbol_list:
            self.contract_dict[vt_symbol] = self.cta_engine.main_engine.get_contract(vt_symbol)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("Start Strategy")
        self.put_event()

    def on_stop(self):
        # output trades df
        # TODO : need to handle this in appropriate way
        log_folder = get_folder_path('log')
        pid = os.getpid()
        trade_file = log_folder.joinpath(f'trade_{datetime.now().strftime("%Y%m%d")}_{pid}.csv')
        self.trades_df.to_csv(trade_file, index=True, mode='a')
        self.write_log(f'output trades to {trade_file}')
        self.write_log('Stop Strategy')
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        # self.bg.update_tick()
        # self.spread.update_basis_on_tick(tick)
        # self.write_log(f'update tick event on {tick.vt_symbol}')
        # self.spread.update_basis_on_tick_list(tick)
        if self.spread.spreadTick is not None:
            self.bg.update_tick(self.spread.spreadTick)
        self.calc_pl()

        self.basis = self.spread.basis
        self.write_log(f'pl {self.pl}, basis {self.basis} on tick update: {tick.vt_symbol}')
        self.put_event()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        am = self.am
        # as log shows, it takes less than 1 mili sec to finish am.update_bar().
        # however, it takes around 0.6 ~ 1.5 sec from start of a minute to on_bar invocation.
        # possibly on_tick?
        self.write_log('update bar')
        am.update_bar(bar)
        if not am.inited:
            self.write_log('am not initiated')
            return
        # fast_ma = am.sma(self.fast_window, array=True)
        # self.fast_ma0 = fast_ma[-1]
        # self.fast_ma1 = fast_ma[-2]
        #
        # slow_ma = am.sma(self.slow_window, array=True)
        # self.slow_ma0 = slow_ma[-1]
        # self.slow_ma1 = slow_ma[-2]
        #
        # cross_over = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 <= self.slow_ma1
        # cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 >= self.slow_ma1
        # print('fast_ma', fast_ma)
        # print('slow_ma', slow_ma)
        cross_over = (datetime.now().minute % 8 == 4)
        cross_below = (datetime.now().minute % 8 == 0)

        self.write_log('Bar:%s,%.1f,ma(%d):[%.1f,%.1f],ma(%d):[%.1f,%.1f],co:%d,cb:%d,%d'
                       % (self.spread.spreadTick.vt_symbol, self.spread.spreadTick.last_price,
                          self.fast_window, self.fast_ma0, self.fast_ma1,
                          self.slow_window, self.slow_ma0, self.slow_ma1,
                          cross_over, cross_below, self.pos))

        if cross_over:
            if self.pos == 0:
                self.buy_spread(bar.close_price, 1)
            elif self.pos < 0:
                self.cover_spread(bar.close_price, self.pos)
                self.buy_spread(bar.close_price, 1)

        if cross_below:
            if self.pos == 0:
                self.short_spread(bar.close_price, 1)
            elif self.pos > 0:
                self.sell_spread(bar.close_price, self.pos)
                self.short_spread(bar.close_price, 1)

        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        we examine the position of each legs, and convert that into position of position of spread
        """
        spread_pos = {}
        # for idx in range(len(self.vt_symbol_list)):
        #     spread_pos[self.vt_symbol_list[idx]] = self.pos_list[idx] * 1.0 / self.weight_list[idx]

        converted_pos = np.divide(self.pos_list, self.weight_list)
        self.pos = self.pos_list[np.argmax([abs(x) for x in converted_pos])]
        # self.write_log(f'AfterTrade: {trade.orderid}, pos({self.pos}): {self.pos_list}, orderids: {self.vt_orderids}')
        self.trim_leg_imb()
        self.trades_df = pd.DataFrame.from_records(self.trade_list)
        self.put_event()

    def calc_pl(self):
        # TODO we can probably move this to converter.PositionHolding.
        # and have [PositionHolding:(net pos, pl)]
        if self.trades_df.shape[0] == 0 or 'vt_symbol' not in self.trades_df.columns:
            return
        groups = self.trades_df.groupby(by='vt_symbol')
        for vt_symbol, df in groups:
            last_price = self.spread.leg_tick_dict[vt_symbol].last_price
            self.pl_dict[vt_symbol] = sum(df.direction * (last_price - df.price) * df.volume *
                                          self.contract_dict[vt_symbol].size)
        self.pl = sum(self.pl_dict.values())

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def get_vt_symbol_index(self, vt_symbol:str):
        try:
            idx = self.vt_symbol_list.index(vt_symbol)
        except ValueError:
            # vt_symbol not in list
            return None
        return idx

    def check_leg_imbalance(self):
        active_orders = []
        if len(self.vt_orderids) != 0:
            for vt_orderid in self.vt_orderids:
                order = self.cta_engine.main_engine.get_order(vt_orderid)
                if order.is_active():
                    active_orders.append(order)
        if len(active_orders) != 0:
            return None, None
        self.write_log(f'no live orders: {self.vt_orderids}. checking leg imbalance')
        leg_imbalance = -1 * np.dot(self.abs_weight_list, self.pos_list)
        if leg_imbalance == 0:
            return None, None
        idx_to_trade = np.argmin([abs(x) for x in self.pos_list])
        vt_symbol = self.vt_symbol_list[idx_to_trade]
        return vt_symbol, leg_imbalance
        # self.trim_leg_imb(vt_symbol, leg_imbalance)

    def trim_leg_imb(self):
        vt_symbol, volume = self.check_leg_imbalance()
        if vt_symbol is None:
            return
        direction = Direction.SHORT
        if volume > 0:
            direction = Direction.LONG
        price = 0
        if self.active_order:
            if volume > 0:
                price = self.spread.leg_tick_dict[vt_symbol].ask_price_1
            else:
                price = self.spread.leg_tick_dict[vt_symbol].bid_price_1
        else:
            if volume > 0:
                price = self.spread.leg_tick_dict[vt_symbol].bid_price_1
            else:
                price = self.spread.leg_tick_dict[vt_symbol].ask_price_1

        self.cta_engine.send_order(strategy=self, direction=direction, offset=Offset.OPEN,
                                   price=price, volume=abs(volume), stop=False, lock=False,
                                   vt_symbol=vt_symbol)
        self.write_log(f'position: {self.pos_list}, order: {self.vt_orderids} > trim leg imbalance {vt_symbol} {volume} {price}')

    # def get_data(self):
    #     """
    #     Get strategy data.
    #     """
    #     strategy_data = {
    #         "strategy_name": self.strategy_name,
    #         "vt_symbol": self.vt_symbol,
    #         "vt_symbol_list": self.vt_symbol_list,
    #         "position_list": self.pos_list,
    #         "class_name": self.__class__.__name__,
    #         "author": self.author,
    #         "parameters": self.get_parameters(),
    #         "variables": self.get_variables(),
    #     }
    #     return strategy_data
