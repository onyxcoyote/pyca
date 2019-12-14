'''
    This file is part of pyca.

    pyca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pyca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with pyca.  If not, see <https://www.gnu.org/licenses/>.
'''


import time
import random
import traceback
import datetime
import string


from __init__ import GLOBAL_VARS
import __main__
import config
import clientOrderIdObj
import geminiAPIHelper


ORDER_ID_PREFIX = "PYCA-SEL|"
ORDER_OPTIONS=['maker-or-cancel']


TRADE_SIDE='sell'



def getGeminiSellDCAPostOnly():
    configFile = config.getConfig()

    strEnabled = configFile.get('GeminiSellDCAPostOnly', 'Enabled')
    if(strEnabled=="False"):
        Enabled = False
    elif(strEnabled=="True"):
        Enabled = True
    else:
        raise ValueError('invalid value for GeminiSellDCAPostOnly.Enabled')
        
    OrdersPerDay = configFile.get('GeminiSellDCAPostOnly', 'OrdersPerDay')
    OrderQuantityPerDayInFiat = configFile.get('GeminiSellDCAPostOnly', 'OrderQuantityPerDayInFiat')
    TradeSymbol = configFile.get('GeminiSellDCAPostOnly', 'TradeSymbol')
    HardMinimumCoinPrice = float(configFile.get('GeminiSellDCAPostOnly', 'HardMinimumCoinPrice'))
    NumberOfMinutesToConsiderOrderStale = float(configFile.get('GeminiSellDCAPostOnly', 'NumberOfMinutesToConsiderOrderStale')) #note: when using sandbox mode, it's recommended to use "0" for this value
    ChanceToProceedOnOrderPerTick = float(configFile.get('GeminiSellDCAPostOnly', 'ChanceToProceedOnOrderPerTick'))
    MaxDaysCatchup = float(configFile.get('GeminiSellDCAPostOnly', 'MaxDaysCatchup'))  #recommended to be at least 1.5 to catch up in case of maintenance windows up to 12 hours.
    DesiredPremium = float(configFile.get('GeminiSellDCAPostOnly', 'DesiredPremium'))
    StartingProgressForFirstOrder = float(configFile.get('GeminiSellDCAPostOnly', 'StartingProgressForFirstOrder'))

    cfg = GeminiSellDCAPostOnly(_Enabled=Enabled, _OrdersPerDay=OrdersPerDay, _OrderQuantityPerDayInFiat=OrderQuantityPerDayInFiat, _TradeSymbol=TradeSymbol, _HardMinimumCoinPrice=HardMinimumCoinPrice, _NumberOfMinutesToConsiderOrderStale=NumberOfMinutesToConsiderOrderStale, _ChanceToProceedOnOrderPerTick=ChanceToProceedOnOrderPerTick, _MaxDaysCatchup=MaxDaysCatchup, _DesiredPremium=DesiredPremium, _StartingProgressForFirstOrder=StartingProgressForFirstOrder)
    return cfg

class GeminiSellDCAPostOnly:
    def __init__(self, _Enabled, _OrdersPerDay, _OrderQuantityPerDayInFiat, _TradeSymbol, _HardMinimumCoinPrice, _NumberOfMinutesToConsiderOrderStale, _ChanceToProceedOnOrderPerTick, _MaxDaysCatchup,  _DesiredPremium, _StartingProgressForFirstOrder):
        self.Enabled = bool(_Enabled)
        self.OrdersPerDay = float(_OrdersPerDay)
        self.OrderQuantityPerDayInFiat = float(_OrderQuantityPerDayInFiat)
        self.TradeSymbol = str(_TradeSymbol)
        self.NumberOfMinutesToConsiderOrderStale = float(_NumberOfMinutesToConsiderOrderStale)
        self.MaxDaysCatchup = _MaxDaysCatchup  #can purchase up to X times max per purchase if needed to "catch up" due to failed purchases, waiting for a better price, etc. (e.g. 2.0 = 200% max catchup single purchase)
        self.ChanceToProceedOnOrderPerTick = _ChanceToProceedOnOrderPerTick  #this value adds a random delay to purchases to mitigate exact timing prediction by an adversary
        self.DesiredPremium = _DesiredPremium  #uses a [HIGHER for selling/LOWER for buying] order price based on percent value.  The higher the number (the more the distance from market price), the less likely the order will go through soon (or at all).
        self.HardMinimumCoinPrice = float(_HardMinimumCoinPrice)
        #self.ProcessActiveOrdersFrequencyPerDay = (24*(60/5))  #every 5 minutes   #TODO: UNCOMMENT
        self.ProcessActiveOrdersFrequencyPerDay = (24*(60/1))  #every 5 minutes     #TODO: REMOVE STUB
        self.StartingProgressForFirstOrder = _StartingProgressForFirstOrder  #this value speeds up the first purchase after starting the program
        
        if((self.OrdersPerDay > 0) & (self.OrderQuantityPerDayInFiat > 0)):
            self.ProgressIncrementToOrderInFiatPerTick = (self.OrderQuantityPerDayInFiat/GLOBAL_VARS.TICKS_PER_DAY)
            self.CurrentProgressToOrderQuantityInFiat = (self.OrderQuantityPerDayInFiat/self.OrdersPerDay)*_StartingProgressForFirstOrder
            self.OrderQuantityInFiatPerOrder = round((self.OrderQuantityPerDayInFiat/self.OrdersPerDay), 2)
            self.OrderQuantityMaxInFiatPerOrder = round(self.MaxDaysCatchup * self.OrderQuantityInFiatPerOrder, 2)
            self.ProgressIncrementToProcessActiveOrdersPercentPerTick = (self.ProcessActiveOrdersFrequencyPerDay/GLOBAL_VARS.TICKS_PER_DAY)
            self.CurrentProgressToProcessActiveOrders = 0.995  #99.5%. process active orders pretty soon after starting
        else:
            self.ProgressIncrementToOrderInFiatPerTick = 0
            self.CurrentProgressToOrderQuantityInFiat = 0
            self.OrderQuantityInFiatPerOrder = 0
            self.OrderQuantityMaxInFiatPerOrder = 0
            self.ProgressIncrementToProcessActiveOrdersPercentPerTick = 0
            self.CurrentProgressToProcessActiveOrders = 0
            
        #input value checks
        if((self.OrdersPerDay < 0.0) | (self.OrdersPerDay > 7200.0)):
            raise ValueError('invalid value for GeminiSellDCAPostOnly.OrdersPerDay')
    
        if((self.OrderQuantityPerDayInFiat < 0.00) | (self.OrderQuantityPerDayInFiat > 200.00)):   #temporary maximum trade per day in fiat of 200 fiat units (e.g. 200 USD)
            raise ValueError('invalid value for GeminiSellDCAPostOnly.OrderQuantityPerDayInFiat')
        
        if(self.TradeSymbol != "btcusd"):
            raise ValueError('invalid value for GeminiSellDCAPostOnly.TradeSymbol')
        
        if((self.MaxDaysCatchup < 1.0) | (self.MaxDaysCatchup > 20.0)):
            raise ValueError('invalid value for GeminiSellDCAPostOnly.MaxDaysCatchup')
        
        if((self.ChanceToProceedOnOrderPerTick < 0.0001) | (self.ChanceToProceedOnOrderPerTick > 0.95)):
            raise ValueError('invalid value for GeminiSellDCAPostOnly.ChanceToProceedOnOrderPerTick')
        
        if((self.DesiredPremium < 0.0000) | (self.DesiredPremium > 0.1000)):  #maximum 10.0%
            raise ValueError('invalid value for GeminiSellDCAPostOnly.DesiredPremium')
        
        if((_StartingProgressForFirstOrder < 0.0) | (_StartingProgressForFirstOrder > (1*self.MaxDaysCatchup))):
            raise ValueError('invalid value for GeminiSellDCAPostOnly parameter _StartingProgressForFirstOrder')
          


    def printMe(self):
        print("==ConfigGeminiSellDCAPostOnly==")
        print("Enabled:" + str(self.Enabled))
        print("OrdersPerDay:" + str(self.OrdersPerDay))
        print("OrderQuantityPerDayInFiat:" + str(self.OrderQuantityPerDayInFiat))
        print("TradeSymbol:" + self.TradeSymbol)
        print("MaxDaysCatchup:" + str(self.MaxDaysCatchup))
        print("ChanceToProceedOnOrderPerTick:" + str(self.ChanceToProceedOnOrderPerTick))
        print("DesiredPremium:" + str(self.DesiredPremium))
        print("HardMinimumCoinPrice:" + str(self.HardMinimumCoinPrice))
        print("NumberOfMinutesToConsiderOrderStale" + str(self.NumberOfMinutesToConsiderOrderStale))
        
        print("ProgressIncrementToOrderInFiatPerTick:" + str(self.ProgressIncrementToOrderInFiatPerTick))
        print("CurrentProgressToOrderQuantityInFiat:" + str(self.CurrentProgressToOrderQuantityInFiat))       
        print("OrderQuantityInFiatPerOrder:" + str(self.OrderQuantityInFiatPerOrder))
        print("OrderQuantityMaxInFiatPerOrder:" + str(self.OrderQuantityMaxInFiatPerOrder))
        
        print("ProgressIncrementToProcessActiveOrdersPercentPerTick:" + str(self.ProgressIncrementToProcessActiveOrdersPercentPerTick))
        print("CurrentProgressToProcessActiveOrders:" + str(self.CurrentProgressToProcessActiveOrders))

    def printMinimal(self):
        print("CurrentProgressToOrderQuantityInFiat:" + str(round(self.CurrentProgressToOrderQuantityInFiat,2)) + "/" + str(self.OrderQuantityInFiatPerOrder) + "  " + str(round((self.CurrentProgressToOrderQuantityInFiat / self.OrderQuantityInFiatPerOrder) * 100, 3)) + "%.  Progress to process: " + str(round(self.CurrentProgressToProcessActiveOrders*100.0,2))+"%" )
        
    def isEnabled(self):
        return self.Enabled
        
    def doRule(self):        
        try:
            #purchase rule
            if((self.OrdersPerDay > 0) & (self.OrderQuantityPerDayInFiat > 0)):
                #increment progress to next purchase
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
                        
                
                #purchase
                if(self.CurrentProgressToOrderQuantityInFiat >= self.OrderQuantityInFiatPerOrder):
                    
                    randVal = random.random()
                    if(randVal < self.ChanceToProceedOnOrderPerTick):
                        proceedWithBuy = True
                        print("random: "+ str(randVal) + " < " + str(self.ChanceToProceedOnOrderPerTick) + " -> proceed with purchase")
                    else:
                        proceedWithBuy = False
                        print("random: "+ str(randVal) + " >= " + str(self.ChanceToProceedOnOrderPerTick) + " -> random delay on purchase")
                        
                    if(proceedWithBuy):
                        #do purchase (if applicable)
                        try:
                            print("executing purchase, fiat quantity: " + str(round(self.CurrentProgressToOrderQuantityInFiat,2)))
                            self.doNewTrade()
                            self.CurrentProgressToOrderQuantityInFiat = 0
                        except Exception as e:
                            print("GeminiSellDCAPostOnly - Error: " + str(e) + ". Traceback: " + str(traceback.print_tb(e.__traceback__)))
                            time.sleep(60)
                        
                    else:
                        #print("random delay on purchase")
                        pass            
            pass
        except Exception as e:
            print(str(e))
    

    
    def getPrice(self):
        if(TRADE_SIDE=="buy"):
            return geminiAPIHelper.getTickerBid()
        elif(TRADE_SIDE=="sell"):
            return geminiAPIHelper.getTickerAsk()
        else:
            raise ValueError('invalid TRADE_SIDE')
    
    def getPriceAfterDiscountOrPremium(self):
        if(TRADE_SIDE=="buy"):
            return bidValueCostPerCoin * (1.0000-self.DesiredDiscount)  #Buying subtracts desired discount
        elif(TRADE_SIDE=="sell"):
            return lastValueCostPerCoin * (1.0000+self.DesiredPremium)   #Selling adds desired premium
        else:
            raise ValueError('invalid TRADE_SIDE')


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
            if(ORDER_ID_PREFIX  in str(order["client_order_id"])):
                orderId = order["id"]
                print(" orderId:" + orderId)
                clientOrderId = clientOrderIdObj.clientOrderIdObj(ORDER_ID_PREFIX, str(order["client_order_id"]))
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
    
    #re-submits purchase order at a higher price (but not higher than the best bid)
    def resubmitTrade(self, _orderObj):
        
        orderId = _orderObj["id"]
        clientOrderId = clientOrderIdObj.clientOrderIdObj(str(_orderObj["client_order_id"]))
        oldOrderDateTime = clientOrderId.getOrderDateTimeFromOrderId()
        
        #cancel order
        print("cancelling: " + str(orderId))
        cancelResult = lastValueCostPerCoin = __main__.geminiClient.client.cancel_order(str(orderId))  #API call
            ##TODO: WHAT THE FUCK???
        
        #resubmit a new order
        clientOrderId.incrementAttemptNumber()
        clientOrderId.resetOrderDateTime()
        
        #calculate new discount
        if(clientOrderId.attemptNumber >= 12):  #reduce discount/premium to exactly 0, because it's practically the same as 0 anyway, and would have a better chance of successful purchase
            discount = 0
        else:
            discount = (self.DesiredPremium/clientOrderId.attemptNumber)
        
        #get price
        lastValueCostPerCoin = self.getPrice()
        
        pricePerCoin = lastValueCostPerCoin * (1.0000-discount) 
        pricePerCoin = round(pricePerCoin,2)
        print("bid/ask price:" + str(pricePerCoin) + " discount/premium: " + str(discount) + " attemptNumber:" + str(clientOrderId.attemptNumber) )
        
        #if buy
            #if(pricePerCoin > self.HardMaximumCoinPrice):
                #raise AssertionError("coin price is above hard limit")
        
        #if sell
        if(pricePerCoin < self.HardMinimumCoinPrice):
            raise AssertionError("coin price is below hard limit")
                
        #get old quantity in fiat
        _quantityInFiat = float(_orderObj["remaining_amount"]) * float(_orderObj["price"])
                
        #determine coin purchase quantity
        coinQuantity = round(_quantityInFiat / pricePerCoin,8)  #assume 8 decimal places is max resolution on coin quantity
        print("coinQuantity:" + str(coinQuantity))
        
        if(coinQuantity < 0.00001):
            print("coinQuantity: " + str(coinQuantity))
            print("purchase quantity is too low (below 0.00001), not re-submitting")
            return
        
        try:
            result = __main__.geminiClient.client.new_order(client_order_id=clientOrderId.getOrderId(), symbol=self.TradeSymbol, amount=str(coinQuantity), price=str(pricePerCoin), side='buy', type='exchange limit', options=ORDER_OPTIONS)  #API call        
            print("purchase order result: " + str(result))
        except Exception as e:
            print(str(e))
            time.sleep(60)            


    def doNewTrade(self):

        _quantityInFiat=round(self.CurrentProgressToOrderQuantityInFiat,2)
        
        #generate an order id
        clientOrderId=clientOrderIdObj.clientOrderIdObj(ORDER_ID_PREFIX)
        print(" orderId:"+clientOrderId.getOrderId())
        
        #get price
        lastValueCostPerCoin = self.getPrice()
        
        #if buy 
            #pricePerCoin = bidValueCostPerCoin * (1.0000-self.DesiredDiscount)  #Buying subtracts desired discount
        #if sell
        pricePerCoin = lastValueCostPerCoin * (1.0000+self.DesiredPremium)   #Selling adds desired premium
        
        pricePerCoin = round(pricePerCoin,2)
        print(" using trade price: " + str(pricePerCoin))
        
        if(TRADE_SIDE=="buy"):
            if(pricePerCoin > self.HardMaximumCoinPrice):   #BUY, check that price not above max
                raise AssertionError("order price greater than configured maximum")
        elif(TRADE_SIDE=="sell"):
            if(pricePerCoin < self.HardMinimumCoinPrice):   #SELL, check that price not below minimum
                raise AssertionError("order price less than configured minimum")
        else:
            raise ValueError('invalid TRADE_SIDE')
        

                
        #determine coin order quantity
        coinQuantity = round(_quantityInFiat / pricePerCoin,8)  #assume 8 decimal places is max resolution on coin quantity
        print(" coinQuantity:" + str(coinQuantity))
        
        if(coinQuantity < 0.00001):
            print("  coinQuantity: " + str(coinQuantity))
            sys.exit("order quantity is too low (below 0.00001), increase order amount or decrease order frequency")

        #note
        print("estimated trade value in fiat:" + str(pricePerCoin*coinQuantity))
            
        try:            
            #place order                                                                                                                                                                                                                                                                                                                  
            result = __main__.geminiClient.client.new_order(client_order_id=clientOrderId.getOrderId(), symbol=self.TradeSymbol, amount=str(coinQuantity), price=str(pricePerCoin), side=TRADE_SIDE, type='exchange limit', options=ORDER_OPTIONS)  #API call
            print(" order result: " + str(result))  
        except Exception as e:
            print(str(e))
            time.sleep(60)
    
    
