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

import sys
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
import geminiTradeDCAPostOnly


ORDER_ID_PREFIX = "PYCA-BUY|"  #TODO: move to another class and derive from trade_side
ORDER_OPTIONS=['maker-or-cancel']


TRADE_SIDE='buy'



def getGeminiBuyDCAPostOnly():
    configFile = config.getConfig()

    strEnabled = configFile.get('GeminiBuyDCAPostOnly', 'Enabled')
    if(strEnabled=="False"):
        Enabled = False
    elif(strEnabled=="True"):
        Enabled = True
    else:
        raise ValueError('invalid value for GeminiBuyDCAPostOnly.Enabled')
    
    OrdersPerDay = configFile.get('GeminiBuyDCAPostOnly', 'OrdersPerDay')
    OrderQuantityPerDayInFiat = configFile.get('GeminiBuyDCAPostOnly', 'OrderQuantityPerDayInFiat')
    TradeSymbol = configFile.get('GeminiBuyDCAPostOnly', 'TradeSymbol')
    HardMaximumCoinPrice = float(configFile.get('GeminiBuyDCAPostOnly', 'HardMaximumCoinPrice'))
    NumberOfMinutesToConsiderOrderStale = float(configFile.get('GeminiBuyDCAPostOnly', 'NumberOfMinutesToConsiderOrderStale')) #note: when using sandbox mode, it's recommended to use "0" for this value
    ChanceToProceedOnOrderPerTick = float(configFile.get('GeminiBuyDCAPostOnly', 'ChanceToProceedOnOrderPerTick'))
    MaxDaysCatchup = float(configFile.get('GeminiBuyDCAPostOnly', 'MaxDaysCatchup'))  #recommended to be at least 1.5 to catch up in case of maintenance windows up to 12 hours.
    DesiredDiscount = float(configFile.get('GeminiBuyDCAPostOnly', 'DesiredDiscount'))
    StartingProgressForFirstOrder = float(configFile.get('GeminiBuyDCAPostOnly', 'StartingProgressForFirstOrder'))

    cfg = GeminiBuyDCAPostOnly(_Enabled=Enabled, _OrdersPerDay=OrdersPerDay, _OrderQuantityPerDayInFiat=OrderQuantityPerDayInFiat, _TradeSymbol=TradeSymbol, _HardMaximumCoinPrice=HardMaximumCoinPrice, _NumberOfMinutesToConsiderOrderStale=NumberOfMinutesToConsiderOrderStale, _ChanceToProceedOnOrderPerTick=ChanceToProceedOnOrderPerTick, _MaxDaysCatchup=MaxDaysCatchup, _DesiredDiscount=DesiredDiscount, _StartingProgressForFirstOrder=StartingProgressForFirstOrder)
    return cfg

class GeminiBuyDCAPostOnly(geminiTradeDCAPostOnly.GeminiTradeDCAPostOnly):
    def __init__(self, _Enabled, _OrdersPerDay, _OrderQuantityPerDayInFiat, _TradeSymbol, _HardMaximumCoinPrice, _NumberOfMinutesToConsiderOrderStale, _ChanceToProceedOnOrderPerTick, _MaxDaysCatchup,  _DesiredDiscount, _StartingProgressForFirstOrder):
        self.TradeSide = TRADE_SIDE
        self.Enabled = bool(_Enabled)
        self.OrdersPerDay = float(_OrdersPerDay)
        self.OrderQuantityPerDayInFiat = float(_OrderQuantityPerDayInFiat)
        self.TradeSymbol = str(_TradeSymbol)
        self.NumberOfMinutesToConsiderOrderStale = float(_NumberOfMinutesToConsiderOrderStale)
        self.MaxDaysCatchup = _MaxDaysCatchup  #can purchase up to X times max per purchase if needed to "catch up" due to failed purchases, waiting for a better price, etc. (e.g. 2.0 = 200% max catchup single purchase)
        self.ChanceToProceedOnOrderPerTick = _ChanceToProceedOnOrderPerTick  #this value adds a random delay to purchases to mitigate exact timing prediction by an adversary
        self.DesiredDiscount = _DesiredDiscount  #uses a lower purchase price based on percent value.  The more the discount, the less likely the purchase will go through soon (or at all).
        self.HardMaximumCoinPrice = float(_HardMaximumCoinPrice)
        #self.ProcessActiveOrdersFrequencyPerDay = (24*(60/5))  #every 5 minutes   #TODO: UNCOMMENT
        self.ProcessActiveOrdersFrequencyPerDay = (24*(60/1))  #every 5 minutes     #TODO: REMOVE STUB
        self.StartingProgressForFirstOrder = _StartingProgressForFirstOrder  #this value speeds up the first purchase after starting the program
        
        if((self.OrdersPerDay > 0) & (self.OrderQuantityPerDayInFiat > 0)):
            self.ProgressIncrementToPurchaseInFiatPerTick = (self.OrderQuantityPerDayInFiat/GLOBAL_VARS.TICKS_PER_DAY)
            self.CurrentProgressToOrderQuantityInFiat = (self.OrderQuantityPerDayInFiat/self.OrdersPerDay)*_StartingProgressForFirstOrder
            self.OrderQuantityInFiatPerOrder = round((self.OrderQuantityPerDayInFiat/self.OrdersPerDay), 2)
            self.OrderQuantityMaxInFiatPerOrder = round(self.MaxDaysCatchup * self.OrderQuantityInFiatPerOrder, 2)
            self.ProgressIncrementToProcessActiveOrdersPercentPerTick = (self.ProcessActiveOrdersFrequencyPerDay/GLOBAL_VARS.TICKS_PER_DAY)
            self.CurrentProgressToProcessActiveOrders = 0.995  #99.5%. process active orders pretty soon after starting
        else:
            self.ProgressIncrementToPurchaseInFiatPerTick = 0
            self.CurrentProgressToOrderQuantityInFiat = 0
            self.OrderQuantityInFiatPerOrder = 0
            self.OrderQuantityMaxInFiatPerOrder = 0
            self.ProgressIncrementToProcessActiveOrdersPercentPerTick = 0
            self.CurrentProgressToProcessActiveOrders = 0
            
        #input value checks
        if((self.OrdersPerDay < 0.0) | (self.OrdersPerDay > 7200.0)):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.OrdersPerDay')
    
        if((self.OrderQuantityPerDayInFiat < 0.00) | (self.OrderQuantityPerDayInFiat > 200.00)):   #temporary maximum purchase per day in fiat of 200 fiat units (e.g. 200 USD)
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.OrderQuantityPerDayInFiat')
        
        if(self.TradeSymbol != "btcusd"):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.TradeSymbol')
        
        if((self.MaxDaysCatchup < 1.0) | (self.MaxDaysCatchup > 20.0)):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.MaxDaysCatchup')
        
        if((self.ChanceToProceedOnOrderPerTick < 0.0001) | (self.ChanceToProceedOnOrderPerTick > 0.95)):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.ChanceToProceedOnOrderPerTick')
        
        if((self.DesiredDiscount < 0.0000) | (self.DesiredDiscount > 0.1000)):  #maximum 10.0% discount
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.DesiredDiscount')
        
        if((_StartingProgressForFirstOrder < 0.0) | (_StartingProgressForFirstOrder > (1*self.MaxDaysCatchup))):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly parameter _StartingProgressForFirstOrder')
          


    def printMe(self):
        print("==ConfigGeminiBuyDCAPostOnly==")
        print("Enabled:" + str(self.Enabled))
        print("OrdersPerDay:" + str(self.OrdersPerDay))
        print("OrderQuantityPerDayInFiat:" + str(self.OrderQuantityPerDayInFiat))
        print("TradeSymbol:" + self.TradeSymbol)
        print("MaxDaysCatchup:" + str(self.MaxDaysCatchup))
        print("ChanceToProceedOnOrderPerTick:" + str(self.ChanceToProceedOnOrderPerTick))
        print("DesiredDiscount:" + str(self.DesiredDiscount))
        print("HardMaximumCoinPrice:" + str(self.HardMaximumCoinPrice))
        print("NumberOfMinutesToConsiderOrderStale" + str(self.NumberOfMinutesToConsiderOrderStale))
        
        print("ProgressIncrementToPurchaseInFiatPerTick:" + str(self.ProgressIncrementToPurchaseInFiatPerTick))
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
                self.CurrentProgressToOrderQuantityInFiat += self.ProgressIncrementToPurchaseInFiatPerTick
                
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
                            self.doNewPurchase()
                            self.CurrentProgressToOrderQuantityInFiat = 0
                        except Exception as e:
                            print("GeminiBuyDCAPostOnly - Error: " + str(e) + ". Traceback: " + str(traceback.print_tb(e.__traceback__)))
                            time.sleep(60)
                        
                    else:
                        #print("random delay on purchase")
                        pass            
            pass
        except Exception as e:
            print(" Error: " + str(e) + " Traceback: " + str(traceback.print_tb(e.__traceback__)))
    
       
    #re-submits purchase order at a higher price (but not higher than the best bid)
    def resubmitPurchase(self, _orderObj):
        
        orderId = _orderObj["id"]
        clientOrderId = clientOrderIdObj.clientOrderIdObj(ORDER_ID_PREFIX, str(_orderObj["client_order_id"]))
        oldOrderDateTime = clientOrderId.getOrderDateTimeFromOrderId()
        
        #cancel order
        print("cancelling: " + str(orderId))
        cancelResult = __main__.geminiClient.client.cancel_order(str(orderId))  #API call
        
        #resubmit a new order
        clientOrderId.incrementAttemptNumber()
        clientOrderId.resetOrderDateTime()
        
        #calculate new discount
        if(clientOrderId.attemptNumber >= 12):  #reduce discount to exactly 0, because it's practically the same as 0 anyway, and would have a better chance of successful purchase
            discount = 0
        else:
            discount = (self.DesiredDiscount/clientOrderId.attemptNumber)
        
        #get price
        lastValueCostPerCoin = self.getPrice()
        pricePerCoin = lastValueCostPerCoin * (1.0000-discount) 
        pricePerCoin = round(pricePerCoin,2)
        print("bid price:" + str(pricePerCoin) + " discount: " + str(discount) + " attemptNumber:" + str(clientOrderId.attemptNumber) )
        if(pricePerCoin > self.HardMaximumCoinPrice):
            raise AssertionError("GeminiBuyDCAPostOnly coin price exceeds hard maximum")
                
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
            print(" Error: " + str(e) + " Traceback: " + str(traceback.print_tb(e.__traceback__)))
            time.sleep(60)            


    def doNewPurchase(self):

        _quantityInFiat=round(self.CurrentProgressToOrderQuantityInFiat,2)
        
        #generate an order id
        clientOrderId=clientOrderIdObj.clientOrderIdObj(ORDER_ID_PREFIX)
        print(" orderId:"+clientOrderId.getOrderId())
        
        #get price
        lastValueCostPerCoin = self.getPrice()
        pricePerCoin = lastValueCostPerCoin * (1.0000-self.DesiredDiscount)  #Note that this logic only should be used for purchase and not sale! (in that case add "premium" instead of "discount")
        pricePerCoin = round(pricePerCoin,2)
        print(" bid price: " + str(pricePerCoin))
        if(pricePerCoin > self.HardMaximumCoinPrice):
            raise AssertionError("GeminiBuyDCAPostOnly coin price exceeds hard maximum")
                
        #determine coin purchase quantity
        coinQuantity = round(_quantityInFiat / pricePerCoin,8)  #assume 8 decimal places is max resolution on coin quantity
        print(" coinQuantity:" + str(coinQuantity))
        
        if(coinQuantity < 0.00001):
            print("  coinQuantity: " + str(coinQuantity))
            sys.exit("purchase quantity is too low (below 0.00001), increase purchase amount or decrease purchase frequency")

        #note
        print("estimated cost in fiat:" + str(pricePerCoin*coinQuantity))
            
        try:            
            #place buy order                                                                                                                                                                                                                                                                                                                  
            result = __main__.geminiClient.client.new_order(client_order_id=clientOrderId.getOrderId(), symbol=self.TradeSymbol, amount=str(coinQuantity), price=str(pricePerCoin), side=TRADE_SIDE, type='exchange limit', options=ORDER_OPTIONS)  #API call
            print(" purchase result: " + str(result))  
        except Exception as e:
            print(" Error: " + str(e) + " Traceback: " + str(traceback.print_tb(e.__traceback__)))
            time.sleep(60)
    
    
