


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


class GeminiTradeDCAPostOnly:
    
    def __init__(self, _trade_side):
        TradeSide = _trade_side
        pass
    
    def getPrice(self):
        print("getting price for side: " + self.TradeSide)
        
        if(self.TradeSide=="buy"):
            return geminiAPIHelper.getTickerBid(self)
        elif(self.TradeSide=="sell"):
            return geminiAPIHelper.getTickerAsk(self)
        else:
            raise ValueError('invalid TradeSide')
    
    def getPriceAfterDiscountOrPremium(self):
        if(self.TradeSide=="buy"):
            return bidValueCostPerCoin * (1.0000-self.DesiredDiscount)  #Buying subtracts desired discount
        elif(self.TradeSide=="sell"):
            return lastValueCostPerCoin * (1.0000+self.DesiredPremium)   #Selling adds desired premium
        else:
            raise ValueError('invalid TradeSide')
        
    def getOrderIdPrefix(self):
        if(self.TradeSide=="buy"):
            return "PYCA-BUY|"
        elif(self.TradeSide=="sell"):
            return "PYCA-SEL|"
        else:
            raise ValueError('invalid TradeSide')
        
    def checkMaxProgressToOrder(self):
        #reduce to max if above max
        if(self.CurrentProgressToOrderQuantityInFiat >= self.OrderQuantityMaxInFiatPerOrder):
            print("CurrentProgressToOrderQuantityInFiat exceeds max per order, reducing to max")
            self.CurrentProgressToOrderQuantityInFiat = self.OrderQuantityMaxInFiatPerOrder
    
    def checkMaxProgressToProcess(self):
        #reduce to max if above max
        if(self.CurrentProgressToProcessActiveOrders >= 1.0):
            print("CurrentProgressToOrderQuantityInFiat exceeds max per order, reducing to max")
            self.CurrentProgressToProcessActiveOrders = 1.0
            
            
    #resubmits stale orders at a worse price
    def processActiveOrders(self):

        orderTimeoutTimedelta = datetime.timedelta(minutes=self.NumberOfMinutesToConsiderOrderStale)
        
        oldestAllowedDateTime = datetime.datetime.now() - orderTimeoutTimedelta
        if(GLOBAL_VARS.DETAILED_LOGGING_MODE):
            print("oldestAllowedDateTime:"+str(oldestAllowedDateTime))
        
        #check previous purchases & merge previous orders if very old
        orders =  __main__.geminiClient.client.get_active_orders()
        
        if(GLOBAL_VARS.DETAILED_LOGGING_MODE):
            print(orders)
            
        print("# orders:"+str(len(orders)))
        for order in orders:
            if(getOrderIdPrefix()  in str(order["client_order_id"])):
                orderId = order["id"]
                print(" orderId:" + orderId)
                clientOrderId = clientOrderIdObj.clientOrderIdObj(getOrderIdPrefix(), str(order["client_order_id"]))
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
