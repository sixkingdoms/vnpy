"""
Basic data structure used for general trading function in VN Trader.
"""

from dataclasses import dataclass
from datetime import datetime
from logging import INFO

from .constant import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType

ACTIVE_STATUSES = set([Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED])


@dataclass
class BaseData:
    """
    Any data object needs a gateway_name as source
    and should inherit base data.
    """

    gateway_name: str


@dataclass
class TickData(BaseData):
    """
    Tick data contains information about:
        * last trade in market
        * orderbook snapshot
        * intraday market statistics.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    name: str = ""
    volume: float = 0
    open_interest: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class BarData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderData(BaseData):
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """

    symbol: str
    exchange: Exchange
    orderid: str

    type: OrderType = OrderType.LIMIT
    direction: Direction = None
    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    traded: float = 0
    status: Status = Status.SUBMITTING
    datetime: datetime = None
    reference: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"

    def is_active(self) -> bool:
        """
        Check if the order is active.
        """
        if self.status in ACTIVE_STATUSES:
            return True
        else:
            return False

    def create_cancel_request(self) -> "CancelRequest":
        """
        Create cancel request object from order.
        """
        req = CancelRequest(
            orderid=self.orderid, symbol=self.symbol, exchange=self.exchange
        )
        return req


@dataclass
class TradeData(BaseData):
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str
    exchange: Exchange
    orderid: str
    tradeid: str
    direction: Direction = None

    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    datetime: datetime = None

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
        self.vt_tradeid = f"{self.gateway_name}.{self.tradeid}"
        self.dict = self.to_dict()

    def to_dict(self):
        obj_dict = {'symbol': self.symbol, 'exchange': self.exchange, 'orderid': self.orderid,
                    'tradeid': self.tradeid,
                    'offset': self.offset, 'price': self.price, 'volume': self.volume, 'time': self.time,
                    'vt_symbol': self.vt_symbol, 'direction': Direction.int(self.direction),
                    'vt_orderid': self.vt_orderid,
                    'vt_trade_id': self.vt_tradeid}

        return obj_dict


@dataclass
class PositionData(BaseData):
    """
    Positon data is used for tracking each individual position holding.
    """

    symbol: str
    exchange: Exchange
    direction: Direction

    volume: float = 0
    frozen: float = 0
    price: float = 0
    pnl: float = 0
    yd_volume: float = 0

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_positionid = f"{self.vt_symbol}.{self.direction.value}"


class SpreadPositionData(BaseData):
    """

    """
    positionDict = {}

    def __init__(self, ticker_list: list, position_list: list=[]):
        if len(position_list) == 0:
            for ticker in ticker_list:
                self.positionDict[ticker] = None
        else:
            assert(len(ticker_list) == len(position_list))
            self.positionDict = dict(zip(ticker_list, position_list))

@dataclass
class AccountData(BaseData):
    """
    Account data contains information about balance, frozen and
    available.
    """

    accountid: str

    balance: float = 0
    frozen: float = 0

    def __post_init__(self):
        """"""
        self.available = self.balance - self.frozen
        self.vt_accountid = f"{self.gateway_name}.{self.accountid}"


@dataclass
class LogData(BaseData):
    """
    Log data is used for recording log messages on GUI or in log files.
    """

    msg: str
    level: int = INFO

    def __post_init__(self):
        """"""
        self.time = datetime.now()


@dataclass
class ContractData(BaseData):
    """
    Contract data contains basic information about each contract traded.
    """

    symbol: str
    exchange: Exchange
    name: str
    product: Product
    size: float
    pricetick: float

    min_volume: float = 1           # minimum trading volume of the contract
    stop_supported: bool = False    # whether server supports stop order
    net_position: bool = False      # whether gateway uses net position volume
    history_data: bool = False      # whether gateway provides bar history data

    option_strike: float = 0
    option_underlying: str = ""     # vt_symbol of underlying contract
    option_type: OptionType = None
    option_expiry: datetime = None
    option_portfolio: str = ""
    option_index: str = ""          # for identifying options with same strike price

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class SpreadData:
    """
    Spread data contains basic info of spread. it contains :
        -  two Contracts ## spread with more than 2 legs will be handled later
        - basis: leg1 px - leg2 px
    """
    #(BaseData)
    ticker: str
    leg1: str
    leg2: str
    leg1Tick: TickData = None
    leg2Tick: TickData = None
    leg1Bar: BarData = None
    leg2Bar: BarData = None

    leg_str_list = []
    leg_tick_list = []
    leg_tick_dict = {}
    leg_coef_dict = {}
    basis: float = 0

    # vars with default value
    mode: str = 'ltp'
    coef_list = [1, -1]
    spreadTick: TickData = None
    # def __init__(self,ticker, leg1Ticker:str,leg2Ticker:str,weight_list:list):
    #     self.ticker = ticker
    #     self.leg1 = leg1Ticker
    #     self.leg2 = leg2Ticker
    #     self.weight_list = weight_list

    def __init__(self, ticker, leg_str_list:list, coef_list: list):
        self.ticker = ticker
        self.leg_str_list = leg_str_list
        self.coef_list = coef_list
        for x in self.leg_str_list:
            self.leg_tick_dict[x] = None
            self.leg_coef_dict[x] = self.coef_list[self.leg_str_list.index(x)]

    # is this still a data class with update funcs?
    def update_basis_on_tick_list(self, tick:TickData):
        if self.leg_tick_dict[tick.vt_symbol] is None:
            old_ltp = 0
            old_mid = 0
        else:
            old_ltp = self.leg_tick_dict[tick.vt_symbol].last_price
            old_mid = 0.5 * (self.leg_tick_dict[tick.vt_symbol].bid_price_1 +
                             self.leg_tick_dict[tick.vt_symbol].ask_price_1)
        self.leg_tick_dict[tick.vt_symbol] = tick

        # check if all legs are of valid tick
        none_count = 0
        for x in self.leg_tick_dict.values():
            if x is None:
                none_count += 1
        if none_count > 0:
            return 0

        # update basis based on tick change
        if self.spreadTick is None:
            self.basis = 0
            if self.mode == 'ltp':
                for leg in self.leg_tick_dict.keys():
                    self.basis += self.leg_coef_dict[leg] * self.leg_tick_dict[leg].last_price
                # self.basis += self.leg_coef_dict[tick.vt_symbol] * (tick.last_price - old_ltp)
            else:
                # default is mid:
                for leg in self.leg_tick_dict.keys():
                    self.basis += self.leg_coef_dict[tick.vt_symbol] * (0.5 * (self.leg_coef_dict[leg].ask_price_1
                                                                               + self.leg_coef_dict[leg].bid_price_1))
        else:
            if self.mode == 'ltp':
                # for leg in self.leg_tick_dict.keys():
                #     self.leg_coef_dict[leg] * self.leg_tick_dict[leg].last_price
                self.basis += self.leg_coef_dict[tick.vt_symbol] * (tick.last_price - old_ltp)
            else:
                # default is mid:
                self.basis += self.leg_coef_dict[tick.vt_symbol] * (0.5 * (tick.ask_price_1 + tick.bid_price_1)
                                                                    - old_mid)
        # active spread price
        bid_price_1 = 0 # self.leg1Tick.ask_price_1 - self.leg2Tick.bid_price_1
        ask_price_1 = 0 # self.leg1Tick.bid_price_1 - self.leg2Tick.ask_price_1
        for leg in self.leg_tick_dict.keys():
            bid_price_1 += max(0, self.leg_coef_dict[leg]) * self.leg_tick_dict[leg].ask_price_1 \
                                + min(0, self.leg_coef_dict[leg]) * self.leg_tick_dict[leg].bid_price_1

            ask_price_1 += max(0, self.leg_coef_dict[leg]) * self.leg_tick_dict[leg].bid_price_1 \
                                + min(0, self.leg_coef_dict[leg]) * self.leg_tick_dict[leg].ask_price_1

        if self.spreadTick is None:
            self.spreadTick = TickData(
                gateway_name=tick.gateway_name,
                symbol=self.ticker,
                exchange=tick.exchange,
                datetime=tick.datetime,
                last_price=self.basis,
                bid_price_1=bid_price_1,
                ask_price_1=ask_price_1,
                name=self.ticker,
                volume=0,
                open_interest=0,
                last_volume=0,
                limit_up=0,
                limit_down=0,
                open_price=0,
                high_price=0,
                low_price=0,
                pre_close=0,
                bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0,
                ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0,
                bid_volume_1=0, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0,
                ask_volume_1=0, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0,
            )
        else:
            self.spreadTick.datetime = tick.datetime
            self.spreadTick.bid_price_1 = bid_price_1
            self.spreadTick.ask_price_1 = ask_price_1
            self.spreadTick.last_price = self.basis

        return self.basis

    def update_basis_on_tick(self, tick:TickData):
        """
        update basis on tick update
        :return:
        """
        #initialize tick data

        if tick.vt_symbol == self.leg1:
            self.leg1Tick = tick
        elif tick.vt_symbol == self.leg2:
            self.leg2Tick = tick

        if self.leg1Tick is None or self.leg2Tick is None:
            return 0

        if self.mode == 'ltp':
            self.basis = self.coef_list[0] * self.leg1Tick.last_price + self.coef_list[1] * self.leg2Tick.last_price
        elif self.mode == 'mid':
            self.basis = (self.coef_list[0] * (self.leg1Tick.ask_price_1 + self.leg1Tick.bid_price_1) \
                          + self.coef_list[1] * (self.leg2Tick.ask_price_1 + self.leg2Tick.bid_price_1)) * 0.5

        # active spread price
        bid_price_1 = self.leg1Tick.ask_price_1 - self.leg2Tick.bid_price_1
        ask_price_1 = self.leg1Tick.bid_price_1 - self.leg2Tick.ask_price_1

        if self.spreadTick is None:
            self.spreadTick = TickData(
                gateway_name=tick.gateway_name,
                symbol=self.ticker,
                exchange=tick.exchange,
                datetime=tick.datetime,
                last_price=self.basis,
                bid_price_1=bid_price_1,
                ask_price_1=ask_price_1,
                name=self.ticker,
                volume=0,
                open_interest=0,
                last_volume=0,
                limit_up=0,
                limit_down=0,
                open_price=0,
                high_price=0,
                low_price=0,
                pre_close=0,
                bid_price_2=0, bid_price_3=0, bid_price_4=0, bid_price_5=0,
                ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0,
                bid_volume_1=0, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0, bid_volume_5=0,
                ask_volume_1=0, ask_volume_2=0, ask_volume_3=0, ask_volume_4=0, ask_volume_5=0,
            )
        else:
            self.spreadTick.datetime = tick.datetime
            self.spreadTick.bid_price_1 = bid_price_1
            self.spreadTick.ask_price_1 = ask_price_1
            self.spreadTick.last_price = self.basis

        return self.basis

    def update_basis_on_bar(self,bar: BarData):
        """
        update basis on bar update
        :param bar: bar data of either leg of the spread
        :return:
        """
        if self.leg1Bar.symbol == bar.symbol:
            self.leg1Bar = bar
        elif self.leg2Bar.symbol == bar.symbol:
            self.leg2Bar = bar
        self.basis = self.leg1Coeff * self.leg1Bar.close_price - self.leg2Bar.close_price
        return self.basis



@dataclass
class SubscribeRequest:
    """
    Request sending to specific gateway for subscribing tick data update.
    """

    symbol: str
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderRequest:
    """
    Request sending to specific gateway for creating a new order.
    """

    symbol: str
    exchange: Exchange
    direction: Direction
    type: OrderType
    volume: float
    price: float = 0
    offset: Offset = Offset.NONE
    reference: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

    def create_order_data(self, orderid: str, gateway_name: str) -> OrderData:
        """
        Create order data from request.
        """
        order = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=orderid,
            type=self.type,
            direction=self.direction,
            offset=self.offset,
            price=self.price,
            volume=self.volume,
            reference=self.reference,
            gateway_name=gateway_name,
        )
        return order


@dataclass
class CancelRequest:
    """
    Request sending to specific gateway for canceling an existing order.
    """

    orderid: str
    symbol: str
    exchange: Exchange

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class HistoryRequest:
    """
    Request sending to specific gateway for querying history data.
    """

    symbol: str
    exchange: Exchange
    start: datetime
    end: datetime = None
    interval: Interval = None

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
