


import sys
import time
import random
import traceback
import datetime
import string

from __init__ import GLOBAL_VARS
import __main__
import clientOrderIdObj
import geminiAPIHelper



ORDER_OPTIONS=['maker-or-cancel']


class GeminiTradeDCAPostOnly:
    
    def __init__(self, _trade_side):
        TradeSide = _trade_side
        pass
    
    
    #TODO: this could go to a generic gemini rule
    def getPrice(self):
        print("getting price for side: " + self.TradeSide)
        
        if(self.TradeSide=="buy"):
            return geminiAPIHelper.getTickerBid(self)
        elif(self.TradeSide=="sell"):
            return geminiAPIHelper.getTickerAsk(self)
        else:
            raise ValueError('invalid TradeSide')

            
    def getPremiumByAttemptNumber(self, _attemptNumber):

        if(_attemptNumber >= 12):
            return 0  #reduce discount/premium to exactly 0, because it's practically the same as 0 anyway, and would have a better chance of successful trade
        elif(self.TradeSide=="buy"):
            #note that NEGATIVE premium is the same as a discount
            return -(self.DesiredDiscount/_attemptNumber) #Buying subtracts desired discount                                                                                                                          
        elif(self.TradeSide=="sell"):                                                                                                                                                                                                 
            return (self.DesiredPremium/_attemptNumber) #Selling adds desired premium                                                                                                                                
        else:
            raise ValueError('invalid TradeSide')                                                                                                              
    
    
    #typical value for a premium might be between 0.0 and 0.10 (for a sell) or 0.0 and -0.10 (for a buy), 0 would hopefully be an "immediate" buy or sell, whereas a number farther from 0 looks for a better price at the cost of a longer wait
    def getPriceAfterDiscountOrPremium(self, _premium):
        
        valueCostPerCoin = self.getPrice()
        return valueCostPerCoin * (1.0000+_premium)  #on Sell side, premium adds a value to try to sell at a better price. On the buy side, subtracts desired discount by using a negative premium
        
        #example:
        #if(self.TradeSide=="buy"):
            #return valueCostPerCoin * (1.0000-self.DesiredDiscount)  #Buying subtracts desired discount
        #elif(self.TradeSide=="sell"):
            #return valueCostPerCoin * (1.0000+self.DesiredPremium)   #Selling adds desired premium
        #else:
            #raise ValueError('invalid TradeSide')
        
    
    
    #TODO: this could go to a generic gemini rule
    def getOrderIdPrefix(self):
        if(self.TradeSide=="buy"):
            return "PYCA-BUY|"
        elif(self.TradeSide=="sell"):
            return "PYCA-SEL|"
        else:
            raise ValueError('invalid TradeSide')
    
    
    def checkMaxProgressToOrder(self):
        #reduce to max if above max
        if(self.CurrentProgressToOrderQuantityInFiat > self.OrderQuantityMaxInFiatPerOrder):
            print("CurrentProgressToOrderQuantityInFiat exceeds max per order, reducing to max")
            self.CurrentProgressToOrderQuantityInFiat = self.OrderQuantityMaxInFiatPerOrder
    
    def checkMaxProgressToProcess(self):
        #reduce to max if above max
        if(self.CurrentProgressToProcessActiveOrders > 1.0):
            print("CurrentProgressToProcessActiveOrders exceeds max per order, reducing to max")
            self.CurrentProgressToProcessActiveOrders = 1.0
            
            
    #resubmits stale orders at a worse price
    def processActiveOrders(self):

        orderTimeoutTimedelta = datetime.timedelta(minutes=self.NumberOfMinutesToConsiderOrderStale)
        
        oldestAllowedDateTime = datetime.datetime.now() - orderTimeoutTimedelta
        if(GLOBAL_VARS.DETAILED_LOGGING_MODE):
            print("oldestAllowedDateTime:"+str(oldestAllowedDateTime))
        
        #check previous trades & merge previous orders if very old
        orders =  __main__.geminiClient.client.get_active_orders()
        
        if(GLOBAL_VARS.DETAILED_LOGGING_MODE):
            print(orders)
            
        print("# orders:"+str(len(orders)))
        for order in orders:
            if(self.getOrderIdPrefix()  in str(order["client_order_id"])):
                orderId = order["id"]
                print(" orderId:" + orderId)
                clientOrderId = clientOrderIdObj.clientOrderIdObj(self.getOrderIdPrefix(), str(order["client_order_id"]))
                print(" prefix: " + clientOrderId.order_id_prefix)
                print(" clientOrderId: " + clientOrderId.getOrderId())
                print(" price: " + str(order["price"]))
                print(" remaining amount: " + str(order["remaining_amount"]))
                print(" attempt number: " + str(clientOrderId.attemptNumber))
                #oldOrderDateTime = clientOrderId.getOrderDateTimeFromOrderId()
                print(" oldOrderDateTime: " + str(clientOrderId.getOrderDateTimeFromOrderId()))

                
                if(clientOrderId.isOrderStale(oldestAllowedDateTime)):
                    print(" order status: stale")   
                    try:
                        self.resubmitTrade(order)     #note: if order is expire, cut the "discount/premium" in half, and keep repeating until the price is reasonable.  With 12-15 halvings, the discount would reduce to almost nothing, but would try to buy at better prices first
                    except Exception as e:
                        print(str(e))
                        time.sleep(60)
                else:
                    print(" order status: fresh")
            else:
                print(" not making changes to " + str(order["client_order_id"]))
        pass


    def doRule(self):        
        try:
            #trade rule
            if((self.OrdersPerDay > 0) & (self.OrderQuantityPerDayInFiat > 0)):
                #increment progress to next trade
                self.CurrentProgressToOrderQuantityInFiat += self.ProgressIncrementToOrderInFiatPerTick
                
                #reduce to max if above max
                self.checkMaxProgressToOrder()
                
                
                #increment progress to next process/resubmit
                self.CurrentProgressToProcessActiveOrders += self.ProgressIncrementToProcessActiveOrdersPercentPerTick
                
                #reduce to max if above max
                self.checkMaxProgressToProcess()
                
                
                self.printMinimal()
                
                
                #process/resubmit existing orders
                if(self.CurrentProgressToProcessActiveOrders >= 1.0):
                    self.CurrentProgressToProcessActiveOrders = 0
                    self.processActiveOrders()
                        
                
                #probably execute the trade
                if(self.CurrentProgressToOrderQuantityInFiat >= self.OrderQuantityInFiatPerOrder):
                    
                    randVal = random.random()
                    if(randVal < self.ChanceToProceedOnOrderPerTick):
                        proceedWithTrade = True
                        print("random: "+ str(randVal) + " < " + str(self.ChanceToProceedOnOrderPerTick) + " -> proceed with trade")
                    else:
                        proceedWithTrade = False
                        print("random: "+ str(randVal) + " >= " + str(self.ChanceToProceedOnOrderPerTick) + " -> random delay on trade")
                        
                    if(proceedWithTrade):
                        #do trade (if applicable)
                        try:
                            print("executing trade, fiat quantity: " + str(round(self.CurrentProgressToOrderQuantityInFiat,2)))
                            self.doNewTrade()
                            self.CurrentProgressToOrderQuantityInFiat = 0
                        except Exception as e:
                            print("GeminiDCAPostOnly - Error: " + str(e) + ". Traceback: " + str(traceback.print_tb(e.__traceback__)))
                            time.sleep(60)
                        
                    else:
                        #print("random delay on trade")
                        pass            
            pass
        except Exception as e:
            print("Error: " + str(e) + " Traceback: " + str(traceback.print_tb(e.__traceback__)))



    #Todo: The order placing code could be put in a generic gemini rule
    #re-submits trade order at a worse price (but not better than the best competing price)
    def resubmitTrade(self, _orderObj):
        
        orderId = _orderObj["id"]
        clientOrderId = clientOrderIdObj.clientOrderIdObj(self.getOrderIdPrefix(), str(_orderObj["client_order_id"]))
        oldOrderDateTime = clientOrderId.getOrderDateTimeFromOrderId()
        
        #cancel order
        print("cancelling: " + str(orderId))
        cancelResult = __main__.geminiClient.client.cancel_order(str(orderId))  #API call
        
        #resubmit a new order
        clientOrderId.incrementAttemptNumber()
        clientOrderId.resetOrderDateTime()
        
        
        #calculate new price ask or bid
        premium = self.getPremiumByAttemptNumber(clientOrderId.attemptNumber)
        pricePerCoin = self.getPriceAfterDiscountOrPremium(premium)
                    
        pricePerCoin = round(pricePerCoin,2)
        print("bid/ask price:" + str(pricePerCoin) + " premium: " + str(premium) + " attemptNumber:" + str(clientOrderId.attemptNumber) )
        
        
        #todo: refactor, duplicate of buy method
        if(self.TradeSide=="buy"):
            if(pricePerCoin > self.HardMaximumCoinPrice):   #BUY, check that price not above max
                print("Order price greater than configured maximum, not doing a trade.")
                return
        elif(self.TradeSide=="sell"):
            if(pricePerCoin < self.HardMinimumCoinPrice):   #SELL, check that price not below minimum
                print("Order price less than configured minimum, not doing a trade.")
                return
        else:
            raise ValueError('invalid TradeSide')
        
        #get old quantity in fiat
        _quantityInFiat = float(_orderObj["remaining_amount"]) * float(_orderObj["price"])
                
        #determine coin trade quantity
        coinQuantity = round(_quantityInFiat / pricePerCoin,8)  #assume 8 decimal places is max resolution on coin quantity
        print("coinQuantity:" + str(coinQuantity))
        
        if(coinQuantity < 0.00001):
            print("coinQuantity: " + str(coinQuantity))
            print("trade quantity is too low (below 0.00001), not re-submitting")
            return
        
        try:
            result = __main__.geminiClient.client.new_order(client_order_id=clientOrderId.getOrderId(), symbol=self.TradeSymbol, amount=str(coinQuantity), price=str(pricePerCoin), side=self.TradeSide, type='exchange limit', options=ORDER_OPTIONS)  #API call        
            print("trade order result: " + str(result))
        except Exception as e:
            print("Error: " + str(e) + " Traceback: " + str(traceback.print_tb(e.__traceback__)))
            time.sleep(60)       
            
            

    #TODO: this could go to a generic gemini rule if price checks are moved elsewhere
    def doNewTrade(self):

        _quantityInFiat=round(self.CurrentProgressToOrderQuantityInFiat,2)
        
        #generate an order id
        clientOrderId=clientOrderIdObj.clientOrderIdObj(self.getOrderIdPrefix())
        print(" orderId:"+clientOrderId.getOrderId())
        
        premium = self.getPremiumByAttemptNumber(1)
        pricePerCoin = self.getPriceAfterDiscountOrPremium(premium)
        
        pricePerCoin = round(pricePerCoin,2)
        print(" using trade price: " + str(pricePerCoin))
        
        #todo: refactor
        if(self.TradeSide=="buy"):
            if(pricePerCoin > self.HardMaximumCoinPrice):   #BUY, check that price not above max
                print("Order price greater than configured maximum, not doing a trade.")
                return
        elif(self.TradeSide=="sell"):
            if(pricePerCoin < self.HardMinimumCoinPrice):   #SELL, check that price not below minimum
                #raise AssertionError("order price less than configured minimum")
                print("Order price less than configured minimum, not doing a trade.")
                return
        else:
            raise ValueError('invalid TradeSide')
        

                
        #determine coin order quantity
        coinQuantity = round(_quantityInFiat / pricePerCoin,8)  #assume 8 decimal places is max resolution on coin quantity
        print(" coinQuantity:" + str(coinQuantity))
        
        if(coinQuantity < 0.00001): #todo: configure from gemini settings
            print("  coinQuantity: " + str(coinQuantity))
            sys.exit("order quantity is too low (below 0.00001), increase order amount or decrease order frequency")

        #note
        print("estimated trade value in fiat:" + str(pricePerCoin*coinQuantity))
            
        try:            
            #place order                                                                                                                                                                                                                                                                                                                  
            result = __main__.geminiClient.client.new_order(client_order_id=clientOrderId.getOrderId(), symbol=self.TradeSymbol, amount=str(coinQuantity), price=str(pricePerCoin), side=self.TradeSide, type='exchange limit', options=ORDER_OPTIONS)  #API call
            print(" order result: " + str(result))  
        except Exception as e:
            print("Error: " + str(e) + " Traceback: " + str(traceback.print_tb(e.__traceback__)))
            time.sleep(60)
    
