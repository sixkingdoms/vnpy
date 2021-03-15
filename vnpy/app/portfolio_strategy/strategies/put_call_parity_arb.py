from typing import List, Dict

from vnpy.app.portfolio_strategy import StrategyTemplate, StrategyEngine
from vnpy.trader.utility import BarGenerator, ArrayManager
from vnpy.trader.object import TickData, BarData
from datetime import datetime


class PutCallParityArb(StrategyTemplate):
    call_ticker = ""
    put_ticker = ""
    hedge_ticker = ""
    strike_price = 0
    risk_free_rate = 0
    time_2_expiry = 0
    tick_dict = {}
    synthetic_underlying = 0
    underlying = 0
    underlying_spread = 0

    futures_pos = 0
    call_pos = 0
    put_pos = 0
    futures_target = 0
    call_target = 0
    put_target = 0

    calc_benchmark = 'mid'
    parameters = [
        "call_ticker",
        "put_ticker",
        "hedge_ticker",
        "strike_price"
    ]
    variables = [
        "calc_benchmark",
        "synthetic_underlying",
        "hedge_ticker",
        "underlying_spread"
    ]

    def __init__(
            self,
            strategy_engine: StrategyEngine,
            strategy_name: str,
            vt_symbols: List[str],
            setting: dict
    ):
        """"""
        super().__init__(strategy_engine, strategy_name, vt_symbols, setting)
        self.bgs: Dict[str, BarGenerator] = {}
        self.last_tick_time: datetime = None

        self.vt_symbol = vt_symbols[0]
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.write_log(self.vt_symbols)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.synthetic_underlying = 0
        self.tick_dict[self.call_ticker] = None
        self.tick_dict[self.put_ticker] = None
        self.tick_dict[self.hedge_ticker] = None

        for key, value in self.tick_dict.items():
            self.pos[key] = self.get_pos(key)

        self.load_bars(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def calc_synthetic_undelrying(self):
        if self.calc_benchmark == 'mid':
            for key, value in self.tick_dict.items():
                value.mid = 0.5 * (value.ask_price_1 + value.bid_price_1)
            self.synthetic_underlying = self.tick_dict[self.call_ticker].mid - \
                                        self.tick_dict[self.put_ticker].mid + self.strike_price
            self.underlying_spread = self.synthetic_underlying - self.tick_dict[self.hedge_ticker].mid
        self.write_log('%s syn: %.2f  fut: %.2f  spd: %.2f' % (self.hedge_ticker, self.synthetic_underlying,
                                                             self.tick_dict[self.hedge_ticker].mid,
                                                             self.underlying_spread))
        # update gui variables
        self.strategy_engine.put_strategy_event(self)

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """

        if tick.vt_symbol not in self.tick_dict.keys():
            self.write_log('invalid ticker : %s' % tick.vt_symbol)

        # self.write_log('%s %.2f %.2f'%(tick.vt_symbol, tick.ask_price_1, tick.bid_price_1))

        self.tick_dict[tick.vt_symbol] = tick
        for key, value in self.tick_dict.items():
            if value is None:
                self.write_log('%s is not updated' % key)
                return
        self.underlying = self.tick_dict[self.hedge_ticker]
        self.last_tick_time = tick.datetime
        self.calc_synthetic_undelrying()

        # bg: BarGenerator = self.bgs[tick.vt_symbol]
        # self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        bars = {bar.vt_symbol: bar}
        self.on_bars(bars)

    def on_bars(self, bars: Dict[str, BarData]):
        """"""
        pass
