from quantopian.pipeline import Pipeline
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline.factors import CustomFactor
from quantopian.pipeline.data.quandl import cboe_vix
from quantopian.pipeline.factors import BusinessDaysSincePreviousEvent
import pandas as pd
import numpy as np
import math


def initialize(context):
    
    #schedule rebalance function at every 5 minutes after market open
    schedule_function(func=rebal, date_rule=date_rules.every_day(), 
                      time_rule=time_rules.market_open(minutes=5))
    
    #schedule close order function to run 1 minute before market close
    schedule_function(close_open_order,date_rules.every_day(), 
                      time_rules.market_close(minutes=1))
      
    
    #set up pipline
    pipe = Pipeline()
    attach_pipeline(pipe, 'vix_pipeline')
    
    #set up vix factor, add to pipline
    v = Get_VIX()     
    pipe.add(v, 'vix')

    #set data lookback
    context.lookback_days = 20
    
    #set up security list and stock variables
    context.security_list = [sid(32270),sid(39154)]
    context.spy = sid(8554)
    #context.sso = sid(32270)
    #context.ubt = sid(39154)

    #set up intital varaiables
    context.short_vol_count = 0
    context.total_count = 0
    
    context.vix_check = []
    
    context.sso_shares = 0
    context.ubt_shares = 0
    context.time = 0    


class Get_VIX(CustomFactor): 
    #custom factor for Vix price
    
    inputs = [cboe_vix.vix_close]
    window_length = 1    
    def compute(self, today, assets, out, vix):
        out[:] = vix[-1]      

def before_trading_start(context, data):
    #set pipline output to variable
    output = pipeline_output('vix_pipeline')
    
    #dropna data
    output = output.dropna()
    
    #get prior day vix price
    context.vix = output['vix'][0]
    
    #append prior day vix price to vix check list, to be used in rebal function. Keep only the lastest two prices
    context.vix_check.append(context.vix)
    context.vix_check = context.vix_check[-2:]

    
    #for tracking function below
    context.total_count += 1
    
    context.start_handle_data = False    
    
def handle_data(context,data):
    
    #if variable is set to true (which can only happen once rebal is run)
    #than execute remaining code, else return
    if context.start_handle_data:
        pass
    else:
        return
    
    #on each execution of handle_data (starting 6:35am) increase time by 1
    #when time is 6:37am execute remaining code, else return
    context.time += 1
    if context.time >= 2 and context.time <= 12:
        pass
    else:
        return
    
   #for each stock in security list, if current price is different by 9% or greater vs starting day price, than return error, else continue
    
    for i, stock in enumerate(context.security_list):
        current_price = data.current(stock, 'price')
        starting_day_price = context.stock_price_test[i]
        change = (current_price / starting_day_price - 1) * float(100)

        if abs(change) > 9:
            log.error("%s possibe flash crash, current price (%s) is greater than 9" 
                      " percent vs starting day price (%s)"  
                      % (stock.symbol, current_price, starting_day_price))
            return
        else:
            pass
    
    #for each stock in security list, get open orders, if there are open orders
    #close orders
    close_open_order(context, data)    
    
    #for each stock in security list, subtract shares desired by current shares owned
    #this gets us shares to order. 
    for i, stock in enumerate(context.security_list):                    
        stock_desired = context.desired_shares[i]
        stock_current = int(round(context.portfolio.positions[stock].amount))
        shares_to_order = int(stock_desired - stock_current)
        stock_current_price = int(data.current(stock, 'price'))
        
    #if shares to order is not zero and we need to buy shares, than limit price is 3% 
    #higher than current price. else limit price is 3% lower
        if shares_to_order is not 0:

            if shares_to_order > 0:
                limit_price = stock_current_price * 1.03
            if shares_to_order < 0:
                limit_price = stock_current_price * .97

    #send order to buy shares wiht limit price                
            o_id_stock = order(stock, shares_to_order,
                               style=LimitOrder(limit_price))
    #log stock purchase
            if o_id_stock:
                log.info("Ordering %s shares of %s. Current price %s" %
                    (get_order(o_id_stock).amount,
                    stock.symbol, data.current(stock, 'price')
                    ))            
    



def vix_check(context,data):
    
    # Check valilidy of VIX Data.
    
    #if there is only one price in vix_check list than pass
    if len(context.vix_check) == 1:
        return True
    #check if prior day vix price is same as prior prior day vix price.
    #check if prior day vix price is nan.
    #if above is true than return data error,
    
    elif len(context.vix_check) > 1:
        if context.vix_check[-1] == context.vix_check[-2]:
            log.error("Data Error: Vix same price as prior day")
            print context.vix
            return False
        if math.isnan(context.vix_check[-1]):
            log.error("Data Error: Vix price is nan")
            return False

def flash_crash_check(context,data):
    
    #get current price and prior day price
    current = data.current(context.spy, 'price')
    data = data.history(context.spy, 'price', 5, '1d')
    
    
    prior = data[-2]
    price_change = (current/prior-1) * 100
    
    #if the change between current price and prior price is greater than 15%
    #than return error: Potential flash crash
    if price_change < -15:
        log.error("Flash Crash: SPY Dropped over 15% from prior day")
        return False
    else:
        return True
    

def rebal(context,data):
    
    #Check Valilidy of Vix Data
    if vix_check(context,data) == False:     
        return
    
    #Check if Flash Crash  
    if flash_crash_check(context,data) == False:     
        return    
    
    #set varaible to hold spy_stdev
    spy_five_stdev = []
    
    #get spy percent change for 20 days
    spy_history = data.history(context.spy, 'price', context.lookback_days,'1d')
    
    print spy_history
    
    spy_history = spy_history.pct_change().dropna()
    
    print spy_history

    #Check Valilidy of SPY Data
    #if there are not 19 data points in history than return error
    if len(spy_history) is not 19:
        log.error("Data Error:  SPY percent is not 19")
        return
    
    #get 15 day stdev and append to spy_five_stdev
    for x in range(5):
        return_list = []
        
        for i in range(x,15+x):
            return_list.append(spy_history[i])
            
        stdev_spy = np.std(list(return_list))
        stdev_spy_annualize = stdev_spy * math.sqrt(252)
        spy_five_stdev.append(stdev_spy_annualize)
            
    #get average of the 5 stdev
    spy_five_stdev_average = sum(spy_five_stdev) / len(spy_five_stdev) * 100

      

    #if vix is greater than average of the 5 spy stdev
    #than go long stock, else long bond
    if context.vix > spy_five_stdev_average:
        weights = [1,0]
        context.short_vol_count += 1
    else:     
        weights = [0,1]
    
    #set varaible to Desired shares to hold for stock and bond  
    context.desired_shares = []
    
    #buy stock based on weight and log order ID
    #also keep track of desired shares and append to desired_shares
    for i, stock in enumerate(context.security_list):
        order_id = order_for_IB(context,data,stock, weights[i])
        if order_id:
            log.info("Ordering %s shares of %s. Current price %s" %
                (get_order(order_id).amount,
                stock.symbol, data.current(stock, 'price')
                ))
            
            #desired shares is amount in portfolio plus shares ordered
            desired = int(round(context.portfolio.positions[stock].amount + 
                                get_order(order_id).amount))
            context.desired_shares.append(desired)
        else:
            #if no order than desired shares is just amount in portfolio
            desired = int(round(context.portfolio.positions[stock].amount))
            context.desired_shares.append(desired)
                     
      
    #keeps track of percentage of times we went long stock vs total 
    percent = float(context.short_vol_count) / float(context.total_count)
    
    #record variables
    record(vix=context.vix, average=spy_five_stdev_average, 
           leverage=context.account.leverage, short_vol_percent=percent)

    #split up desired_shares list created above                
    context.sso_shares = context.desired_shares[0]
    context.ubt_shares = context.desired_shares[1]     
    
    #print desired stock vs desired bond  
    print "Desired SSO " + str(context.sso_shares)
    print "Desired UBT " + str(context.ubt_shares)
    
    #timing for handle data function, set to zero until rebal runs                          
    context.time = 0
    context.start_handle_data = True
    
    
    ##for stock price check    
    context.stock_price_test = []
    
    for stock in context.security_list:
        price = data.current(stock, 'price')
        context.stock_price_test.append(price)
        
    


def valid_portfolio_value(context, security):

    valid_portfolio_value = context.portfolio.cash
    
    for s in context.security_list:
        # Calculate dollar amount of each position in context.assets
        # that we currently hold
        if s in context.portfolio.positions:
            position = context.portfolio.positions[s]
            valid_portfolio_value += position.last_sale_price * \
                position.amount

    return valid_portfolio_value * .90


def get_percent_held(context, security):
    

    valid_portfoliovalue = valid_portfolio_value(context, security)  
    
    
    """
    This calculates the percentage of each security that we currently
    hold in the portfolio.
    """
    if security in context.portfolio.positions:
        position = context.portfolio.positions[security]
        value_held = position.last_sale_price * position.amount
        percent_held = value_held/float(valid_portfoliovalue)
        return percent_held
    else:
        # If we don't hold any positions, return 0%
        return 0.0



def order_for_IB(context, data, security, weight):
    """
    This is a custom order method for this particular algorithm and
    places orders based on:
    (1) How much of each position in context.assets we currently hold
    (2) How much cash we currently hold

    This means that if you have existing positions (e.g. AAPL),
    your positions in that security will not be taken into
    account when calculating order amounts.

    The portfolio value that we'll be ordering on is labeled 
    `valid_portfolio_value`.
    
    If you'd like to use a Stop/Limit/Stop-Limit Order please follow the
    following format:
    STOP - order_style = StopOrder(stop_price)
    LIMIT - order_style = LimitOrder(limit_price)
    STOPLIMIT - order_style = StopLimitOrder(limit_price=x, stop_price=y)
    """
    valid_portfoliovalue = valid_portfolio_value(context, security) 
 
    # Calculate the percent of each security that we want to hold
    percent_to_order = weight - get_percent_held(context,
                                                 security)
    
    # If within 1% of target weight, ignore.
    if abs(percent_to_order) < .01:
        return

    # Calculate the dollar value to order for this security
    value_to_order = percent_to_order * valid_portfoliovalue
    
    current_price = data.current(security, 'price')
 
    # if value to order is positive than limit price is 3% higher than current price
    # else limit price is 3% lower than current price
    if value_to_order > 0: 
        limit_price = current_price * 1.03
    elif value_to_order < 0: 
        limit_price = current_price * .97
    

    return order_value(security, value_to_order,
                       style=LimitOrder(limit_price))


def close_open_order(context, data):
    
    #for each stock in security list, get open orders.
    #if there are open orders, than close order
    for i, stock in enumerate(context.security_list):
        orders = get_open_orders(stock)  
        if orders:  
            for o in orders:
                message = 'Canceling order for {amount} shares in {stock}'  
                message = message.format(amount=o.amount, 
                                         stock=stock.symbol)  
                log.info(message)            
                cancel_order(o)