---

SPY-VIX Quantopian Trading Algortim
=========
# Quantopian Trading Algorithm 

This is a python trading Algorithm using the Quantopian codebase (https://www.quantopian.com/help) for algorithmic stock trading and automatic deployment to a live broker (Interactive Brokers).

Quantopian utilizes the Zipline framework (https://github.com/quantopian/zipline).

###### Setup:

algo.py can be used directly on quantopian.com or through the Zipline API (http://www.zipline.io/appendix.html). If using zipline, proper data streams must be set up to get stock and backtesting data. Also some code moditifcation might need to be adopted to be used on Zipline. Also automatic deployment to live broker is not supported through zipline.

###### Summary:

The algorithm try’s to estimate the existence of a daily VPR (VRP is a measure of excess volatility in the market).
* Excess VRP is usually a sign to go short volatility or "LONG" the market (buy stocks)
* Negative VRP is usually a sign to go long volatility or "SHORT" the market (sell stocks / buy bonds)


Credit: the Algorithm was adopted from page 17 of the finance paper (http://www.naaim.org/wp-content/uploads/2013/10/00R_Easy-Volatility-Investing-+-Abstract-Tony-Cooper.pdf) 

###### Strategy:

HVOL15S – current VIX price minus average of the historical volatility calculated over the
last 15 business days respectively with a smoothing 5 day moving
average applied to each historical volatility calculation. If calculation is positive, buy Stock (leverage Stock ETF) else buy Bond (Leverage bond ETF).
Repeat Daily.


###### Result:

TimeRange:
12/31/2010 to 10/18/2018
* Return 516.84% (Strategy) vs 156.455 (Benchmark (SPY))
* CAGR: 26.2%
* Sharpe: 1.05
* Alpha: .08 (utilizing CAPM) 
* Beta: 1.38 (utilizing CAPM)


###### ResultView
[![image](https://github.com/aaronchu415/SPY-VIX-TradingAlgo/blob/master/ScreenShot/Result.png)](#capture)

<div class="footer">
* Disclosure: I am/we are long QLD, UBT

Additional disclosure: I wrote the above myself, and it expresses my own opinions. I am not receiving compensation for it. I have no business relationship with any company whose stock is mentioned above. 

Past performance may not be indicative of future results. Different types of investments involve varying
degrees of risk. Therefore, it should not be assumed that future performance of any specific investment
or investment strategy  will be profitable or equal the corresponding indicated performance level(s). 
Moreover, you should not assume that any of the above content serves as the receipt of, or as a substitute for, personalized investment advice. Historical performance results for investment indices and/or categories have been provided for general
comparison purposes only. * </div>
