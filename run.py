from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from vnpy.gateway.ctp import CtpGateway
from vnpy.gateway.sopt import SoptGateway
from vnpy.gateway.sopttest import SopttestGateway
from vnpy.app.cta_strategy import CtaStrategyApp
from vnpy.app.cta_backtester import CtaBacktesterApp
from vnpy.app.option_master import OptionMasterApp
from vnpy.app.portfolio_manager import PortfolioManagerApp
from vnpy.app.portfolio_strategy import PortfolioStrategyApp
from vnpy.app.risk_manager import RiskManagerApp
from vnpy.app.algo_trading import AlgoTradingApp
def main():
    """Start VN Trader"""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)


    main_engine.add_gateway(SoptGateway)
    main_engine.add_app(OptionMasterApp)
    main_engine.add_app(RiskManagerApp)
    # main_engine.add_app(PortfolioManagerApp)
    # main_engine.add_app(PortfolioStrategyApp)
    main_engine.add_gateway(CtpGateway)
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(AlgoTradingApp)
    main_engine.add_app(OptionMasterApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()




if __name__ == "__main__":
    main()
