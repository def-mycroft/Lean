"""Dynamic Breakout II Strategy

Taken circa 21K19 from [this page][1]. The below is copied from the web page:

```
In this tutorial we will take a close look at the Dynamic Breakout II strategy
based on the book Building Winning Trading Systems.

First we decide the look-back period based on the change rate of volatility,
then we make trading decisions based on the highest high and lowest low from the
look back period as well as a Bollinger Bands indicator. It is an auto adaptive
trading system that can adjust its buy and sell rules depending on the
performance of these rules in the past. In addition to Forex markets it is
widely used in future and equity markets. You can refer to this video to learn
more about dynamic break out II.

The original Dynamic Break Out system was developed by George Pruitt for Futures
Magazine in 1996. The logic behind the dynamic breakout system is that the
volatility component changes the lookback period, then the enter and exit points
are decided by the highest high and lowest low price over the lookback period.
The newer version of the Dynamic Break Out is just like the original, except we
introduce the Bollinger Band and adjust the number of look back days using the
market volatility, so different market conditions perform better with different
parameters. In addition, the stop loss signal is fixed in version one, but in
version two the liquidate point is based on the moving average indicator and the
length of moving average is dynamically changed with the look-back period.

We backtested the strategy on EURUSD and GBPUSD over 6 years period.  The result
suggests a drawdown of 20% and the strategy caught the market turning points. It
is especially profitable in a trending market.
```

[1]:https://www.quantconnect.com/tutorials/strategy-library/the-dynamic-breakout-ii-strategy

"""
from datetime import datetime
import decimal
import numpy as np


class DynamicBreakoutAlgorithm(QCAlgorithm):
    
    def Initialize(self):
        self.SetStartDate(2010,1,15)
        self.SetEndDate(2016,2,15)
        self.SetCash(100000)
        fx = self.AddForex("EURUSD", Resolution.Hour, Market.Oanda)
        self.syl = fx.Symbol
        self.Schedule.On(self.DateRules.EveryDay(self.syl),
                         self.TimeRules.BeforeMarketClose(self.syl,1),
                         Action(self.SetSignal))
        self.numdays = 20
        self.ceiling,self.floor = 60,20
        self.buypoint, self.sellpoint= None, None
        self.longLiqPoint, self.shortLiqPoint, self.yesterdayclose= None, None, None
        self.SetBenchmark(self.syl)
        self.Bolband = self.BB(self.syl, self.numdays, 2, MovingAverageType.Simple, Resolution.Daily)
   
    def SetSignal(self):
        
        close = self.History(self.syl, 31, Resolution.Daily)['close']
        todayvol = np.std(close[1:31])
        yesterdayvol = np.std(close[0:30])
        deltavol = (todayvol - yesterdayvol) / todayvol
        self.numdays = int(round(self.numdays * (1 + deltavol)))

        if self.numdays > self.ceiling:
           self.numdays = self.ceiling
        elif self.numdays < self.floor:
            self.numdays = self.floor
        
        self.high = self.History(self.syl, self.numdays, Resolution.Daily)['high']
        self.low = self.History(self.syl, self.numdays, Resolution.Daily)['low']      

        self.buypoint = max(self.high)
        self.sellpoint = min(self.low)
        historyclose = self.History(self.syl, self.numdays, Resolution.Daily)['close'] 
        self.longLiqPoint = np.mean(historyclose)
        self.shortLiqPoint = np.mean(historyclose)
        self.yesterdayclose = historyclose.iloc[-1]
        
        # wait for our BollingerBand to fully initialize
        if not self.Bolband.IsReady: return

        holdings = self.Portfolio[self.syl].Quantity
    
        if self.yesterdayclose > self.Bolband.UpperBand.Current.Value and self.Portfolio[self.syl].Price >= self.buypoint:
            self.SetHoldings(self.syl, 1)
        elif self.yesterdayclose < self.Bolband.LowerBand.Current.Value and self.Portfolio[self.syl].Price <= self.sellpoint:
            self.SetHoldings(self.syl, -1)

        if holdings > 0 and self.Portfolio[self.syl].Price <= self.shortLiqPoint:
            self.Liquidate(self.syl)
        elif holdings < 0 and self.Portfolio[self.syl].Price >= self.shortLiqPoint:
            self.Liquidate(self.syl)
      
        self.Log(str(self.yesterdayclose)+(" # of days ")+(str(self.numdays)))
        
    def OnData(self,data):
        pass
