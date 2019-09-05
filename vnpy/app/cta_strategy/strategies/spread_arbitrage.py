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

from vnpy.trader.object import ContractData, SpreadData


class SpreadArbitrage(CtaTemplate):
    author = 'g_liu'

    leg1 = ''
    leg2 = ''
    basis_indicator = 0
    limit = 0
    upper_limit = 200
    lower_limit = 0

    spread: SpreadData
    vt_symbol_list = []

    parameters = ['leg1', 'leg2', 'limit', 'basis_indicator']
    variables = ['upper_limit', 'lower_limit']

    def __init__(self, cta_engine, strategy_name, spreadTicker, setting):
        super(SpreadArbitrage, self).__init__(
            cta_engine, strategy_name, spreadTicker, setting
        )
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def convert_spread_ticker(self):
        # spreadTicker/self.vt_symbol: SPC_fu2001.SHFE&fu2005.SHFE
        spc, contracts = self.vt_symbol.split('_')

        if len(contracts.split('&')) != 2:
            self.write_log('2 contracts expected')
            raise ValueError('2 contracts expected. %d given: %s'
                             % (len(contracts.split('&')), self.vt_symbol))

        self.vt_symbol_list = contracts.split('&')
        self.write_log('contracts: %s' % (' '.join(self.vt_symbol_list)))
        leg1 = self.vt_symbol_list[0]
        leg2 = self.vt_symbol_list[1]
        self.spread = SpreadData(ticker=self.vt_symbol, leg1Ticker=leg1,
                                 leg2Ticker=leg2)

    def on_init(self):
        self.write_log('Init Strategy')
        # self.put_event()
        self.convert_spread_ticker()

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
        self.spread.update_basis_on_tick(tick)
        if self.spread.spreadTick is not None:
            self.write_log('%s(%.1f): %.1f * %.1f' % (self.spread.spreadTick.vt_symbol, self.spread.spreadTick.last_price,
                                                      self.spread.spreadTick.bid_price_1, self.spread.spreadTick.ask_price_1))

            self.bg.update_tick(self.spread.spreadTick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
