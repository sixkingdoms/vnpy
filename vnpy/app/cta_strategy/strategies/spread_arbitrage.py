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
from vnpy.trader.object import ContractData, SpreadData


class SpreadArbitrage(CtaTemplate):
    author = 'g_liu'

    # leg1_coef = 1.0
    # leg2_coef = -1.0

    basis_indicator = 0
    limit = 0
    fast_window = 5
    slow_window = 10

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

    vt_symbol_list = []
    weight_list = [1, -1]
    pos_list = []
    parameters = ['vt_symbols', 'weights', 'fast_window', 'slow_window', 'pos_list']
    variables = ['upper_limit', 'lower_limit', 'fast_ma0', 'fast_ma1', 'slow_ma0', 'slow_ma1']

    def __init__(self, cta_engine, strategy_name, spreadTicker, setting):
        super(SpreadArbitrage, self).__init__(
            cta_engine, strategy_name, spreadTicker, setting
        )
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(5)

        self.vt_symbol_list = []
        self.weight_list = []
        self.pos_list = []

    def convert_spread_ticker(self):
        if self.vt_symbols != '' and self.weights != '':
            self.vt_symbol_list = self.vt_symbols.split(',')
            self.weight_list = [float(x) for x in self.weights.split(',')]
            self.vt_symbol = 'SP_%s' % self.vt_symbols

            assert (len(self.weight_list) == len(self.vt_symbol_list))
            self.write_log('converting spread ticker: %s' % (' '.join(self.vt_symbol_list)))
            self.spread = SpreadData(ticker=self.vt_symbol, leg_str_list=self.vt_symbol_list, coef_list=self.weight_list)
            self.pos_list = [0] * len(self.vt_symbol_list)
        # else:
        #     if len(self.vt_symbol_list) != len(self.weight_list):
        #         self.weight_list = [1, -1]
        #         # self.write_log('ERROR: nb of (contracts, coef) are not matching')
        #         # raise ValueError('ERROR: nb of (contracts, coef) are not matching : %s %s' %\
        #         #                  (self.vt_symbols, self.weights))
        #
        #     spc, contracts = self.vt_symbol.split('_')
        #     if len(contracts.split('&')) != 2:
        #         self.write_log('2 contracts expected')
        #         raise ValueError('2 contracts expected. %d given: %s'
        #                          % (len(contracts.split('&')), self.vt_symbol))
        #
        #     self.vt_symbol_list = contracts.split('&')
        #     self.weight_list = [self.leg1_coef, self.leg2_coef]
        #     self.write_log('contracts: %s' % (' '.join(self.vt_symbol_list)))
        #     self.spread = SpreadData(ticker=self.vt_symbol, leg_str_list=self.vt_symbol_list, coef_list=self.weight_list)
        #     assert(len(self.weight_list) == len(self.vt_symbol_list))

    def on_init(self):
        self.write_log('Init Strategy')
        # self.put_event()
        self.convert_spread_ticker()
        #self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("Start Strategy")
        self.put_event()

    def on_stop(self):
        self.write_log('Stop Strategy')
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        # self.bg.update_tick()
        # self.spread.update_basis_on_tick(tick)
        self.spread.update_basis_on_tick_list(tick)
        if self.spread.spreadTick is not None:
            #self.write_log('%s(%.1f)' % (self.spread.spreadTick.vt_symbol, self.spread.spreadTick.last_price))
            self.bg.update_tick(self.spread.spreadTick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            self.write_log('am not initiated')
            return
        fast_ma = am.sma(self.fast_window, array=True)
        self.fast_ma0 = fast_ma[-1]
        self.fast_ma1 = fast_ma[-2]

        slow_ma = am.sma(self.slow_window, array=True)
        self.slow_ma0 = slow_ma[-1]
        self.slow_ma1 = slow_ma[-2]

        cross_over = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 < self.slow_ma1
        cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 > self.slow_ma1
        # print('fast_ma', fast_ma)
        # print('slow_ma', slow_ma)
        # self.write_log('Bar:%s,%.1f,ma(%d):[%.1f,%.1f],ma(%d):[%.1f,%.1f],co:%d,cb:%d,%d'
        #                % (self.spread.spreadTick.vt_symbol, self.spread.spreadTick.last_price,
        #                   self.fast_window, self.fast_ma0, self.fast_ma1,
        #                   self.slow_window, self.slow_ma0, self.slow_ma1,
        #                   cross_over, cross_below, self.pos))
        # cross_over = datetime.now().minute % 2
        # cross_below = (datetime.now().minute + 1) % 2

        if cross_over:
            if self.pos == 0:
                self.buy_spread(bar.close_price, 1)
            elif self.pos < 0:
                self.cover_spread(bar.close_price, 1)
                self.buy_spread(bar.close_price, 1)

        if cross_below:
            if self.pos == 0:
                self.short_spread(bar.close_price, 1)
            elif self.pos > 0:
                self.sell_spread(bar.close_price, 1)
                self.short_spread(bar.close_price, 1)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        we examine the position of each legs, and convert that into position of position of spread
        """
        spreadPos = {}
        for idx in range(len(self.vt_symbol_list)):
            spreadPos[self.vt_symbol_list[idx]] = self.pos_list[idx] * 1.0 / self.weight_list[idx]
        pos_set = set(spreadPos.keys())
        # if all legs are filled as expected, pos should have one value only.
        # if however, legs are filled not as expected, then we have some legs not filled as expected.
        self.pos = min([abs(x) for x in list(pos_set)])
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        self.put_event()
    def get_vt_symbol_index(self,vt_symbol:str):
        try:
            idx = self.vt_symbol_list.index(vt_symbol)
        except ValueError:
            # vt_symbol not in list
            return None
        return idx

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
