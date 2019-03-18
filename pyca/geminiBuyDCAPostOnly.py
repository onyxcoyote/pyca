import random
import traceback
import uuid
import datetime
import string

from __init__ import GLOBAL_VARS
import __main__
import config

orderIdPrefix = "PYCA#"
orderIdDateFormat = "%Y-%m-%d %H:%M:%S.%f"

def getGeminiBuyDCAPostOnly(isSandbox):
    configFile = config.getConfig(isSandbox)

    PurchasesPerDay = configFile.get('GeminiBuyDCAPostOnly', 'PurchasesPerDay')
    PurchaseQuantityPerDayInFiat = configFile.get('GeminiBuyDCAPostOnly', 'PurchaseQuantityPerDayInFiat')
    PurchaseSymbol = configFile.get('GeminiBuyDCAPostOnly', 'PurchaseSymbol')
    #_DesiredDiscount 0.0004
    #_ChanceToProceedOnPurchasePerTick 0.02
    #todo: add other parameters

    cfg = GeminiBuyDCAPostOnly(PurchasesPerDay, PurchaseQuantityPerDayInFiat, PurchaseSymbol)
    return cfg

class GeminiBuyDCAPostOnly:
    def __init__(self, _PurchasesPerDay, _PurchaseQuantityPerDayInFiat, _PurchaseSymbol, _MaxDaysCatchup = 10.0, _ChanceToProceedOnPurchasePerTick = 0.95, _DesiredDiscount = 0.1000, _HardMaximumCoinPrice = 8000, _StartingProgressForFirstPurchase = 0.99995):
        self.PurchasesPerDay = float(_PurchasesPerDay)
        self.PurchaseQuantityPerDayInFiat = float(_PurchaseQuantityPerDayInFiat)
        self.PurchaseSymbol = str(_PurchaseSymbol)
        self.MaxDaysCatchup = _MaxDaysCatchup  #can purchase up to X times max per purchase if needed to "catch up" due to failed purchases, waiting for a better price, etc. (e.g. 2.0 = 200% max catchup single purchase)
        self.ChanceToProceedOnPurchasePerTick = _ChanceToProceedOnPurchasePerTick  #this value adds a random delay to purchases to mitigate exact timing prediction by an adversary
        self.DesiredDiscount = _DesiredDiscount  #uses a lower purchase price based on percent value.  The more the discount, the less likely the purchase will go through soon (or at all).
        self.HardMaximumCoinPrice = _HardMaximumCoinPrice
        # _StartingProgressForFirstPurchase  #this value speeds up the first purchase
        
        if((self.PurchasesPerDay > 0) & (self.PurchaseQuantityPerDayInFiat > 0)):
            self.ProgressIncrementInFiatPerTick = (self.PurchaseQuantityPerDayInFiat/GLOBAL_VARS.TICKS_PER_DAY)
            self.CurrentProgressToPurchaseQuantityInFiat = (self.PurchaseQuantityPerDayInFiat/self.PurchasesPerDay)*_StartingProgressForFirstPurchase
            self.PurchaseQuantityInFiatPerPurchase = round((self.PurchaseQuantityPerDayInFiat/self.PurchasesPerDay), 2)
            self.PurchaseQuantityMaxInFiatPerPurchase = round(self.MaxDaysCatchup * self.PurchaseQuantityInFiatPerPurchase, 2)
        else:
            self.ProgressIncrementInFiatPerTick = 0
            self.CurrentProgressToPurchaseQuantityInFiat = 0
            self.PurchaseQuantityInFiatPerPurchase = 0
            self.PurchaseQuantityMaxInFiatPerPurchase = 0
            
        #input value checks
        if((self.PurchasesPerDay < 0.0) | (self.PurchasesPerDay > 7200.0)):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.PurchasesPerDay')
    
        if((self.PurchaseQuantityPerDayInFiat < 0.00) | (self.PurchaseQuantityPerDayInFiat > 100.00)):   #temporary maximum purchase per day in fiat of 100 fiat units (e.g. 100 USD)
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.PurchaseQuantityPerDayInFiat')
        
        if(self.PurchaseSymbol != "btcusd"):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.PurchaseSymbol')
        
        if((self.MaxDaysCatchup < 1.0) | (self.MaxDaysCatchup > 20.0)):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.MaxDaysCatchup')
        
        if((self.ChanceToProceedOnPurchasePerTick < 0.0001) | (self.ChanceToProceedOnPurchasePerTick > 0.95)):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.ChanceToProceedOnPurchasePerTick')
        
        if((self.DesiredDiscount < 0.0000) | (self.DesiredDiscount > 0.005)):  #maximum 0.5% discount
            raise ValueError('invalid value for GeminiBuyDCAPostOnly.DesiredDiscount')
        
        if((_StartingProgressForFirstPurchase < 0.0) | (_StartingProgressForFirstPurchase > (1*self.MaxDaysCatchup))):
            raise ValueError('invalid value for GeminiBuyDCAPostOnly parameter _StartingProgressForFirstPurchase')
          


    def printMe(self):
        print("==ConfigGeminiBuyDCAPostOnly==")
        print("PurchasesPerDay:" + str(self.PurchasesPerDay))
        print("PurchaseQuantityPerDayInFiat:" + str(self.PurchaseQuantityPerDayInFiat))
        print("PurchaseSymbol:" + self.PurchaseSymbol)
        print("MaxDaysCatchup:" + str(self.MaxDaysCatchup))
        print("ChanceToProceedOnPurchasePerTick:" + str(self.ChanceToProceedOnPurchasePerTick))
        print("DesiredDiscount:" + str(self.DesiredDiscount))
        print("self.HardMaximumCoinPrice:" + str(self.HardMaximumCoinPrice))
        
        print("ProgressIncrementInFiatPerTick:" + str(self.ProgressIncrementInFiatPerTick))
        print("CurrentProgressToPurchaseQuantityInFiat:" + str(self.CurrentProgressToPurchaseQuantityInFiat))       
        print("PurchaseQuantityInFiatPerPurchase:" + str(self.PurchaseQuantityInFiatPerPurchase))
        print("PurchaseQuantityMaxInFiatPerPurchase:" + str(self.PurchaseQuantityMaxInFiatPerPurchase))

    def printMinimal(self):
        print("CurrentProgressToPurchaseQuantityInFiat:" + str(round(self.CurrentProgressToPurchaseQuantityInFiat,2)) + "/" + str(self.PurchaseQuantityInFiatPerPurchase) + "  " + str(round((self.CurrentProgressToPurchaseQuantityInFiat / self.PurchaseQuantityInFiatPerPurchase) * 100, 3)) + "%" )
        
    def doRule(self):        
        #purchase rule
        if((self.PurchasesPerDay > 0) & (self.PurchaseQuantityPerDayInFiat > 0)):
            #increment progress to next purchase
            self.CurrentProgressToPurchaseQuantityInFiat += self.ProgressIncrementInFiatPerTick
            
            #reduce to max if above max
            self.checkMaxProgressToPurchase()
            
            self.printMinimal()
            
            if(self.CurrentProgressToPurchaseQuantityInFiat >= self.PurchaseQuantityInFiatPerPurchase):
                
                randVal = random.random()
                if(randVal < self.ChanceToProceedOnPurchasePerTick):
                    proceedWithBuy = True
                    print("random: "+ str(randVal) + " < " + str(self.ChanceToProceedOnPurchasePerTick) + " -> proceed with purchase")
                else:
                    proceedWithBuy = False
                    print("random: "+ str(randVal) + " >= " + str(self.ChanceToProceedOnPurchasePerTick) + " -> random delay on purchase")
                    
                if(proceedWithBuy):
                    #do purchase (if applicable)
                    try:
                        print("executing purchase, fiat quantity: " + str(round(self.CurrentProgressToPurchaseQuantityInFiat,2)))
                        self.doPurchase(_orderOptions=['maker-or-cancel'])
                    except Exception as e:
                        print("GeminiBuyDCAPostOnly - Error: " + str(e) + ". Traceback: " + str(traceback.print_tb(e.__traceback__)))
                    
                    self.CurrentProgressToPurchaseQuantityInFiat = 0
                else:
                    #print("random delay on purchase")
                    pass            
        pass
    
    def getTickerBid(self):
        result = __main__.geminiClient.client.get_ticker(self.PurchaseSymbol)   #API call
        #print("ticker: " + str(result))  #e.g. dict value of:  {'bid': '3976.83', 'volume': {'BTC': '6.0073562', 'timestamp': 1552863000000, 'USD': '23832.206809991'}, 'ask': '3976.84', 'last': '3975.00'}
        print("ticker bid: " + result.get("bid"))
        return float(result.get("bid"))
        
    def getOrderDateTimeFromOrderId(self,_orderId):
        return datetime.datetime.strptime(_orderId.replace(orderIdPrefix,"",1),orderIdDateFormat)
        
    def processActiveOrders(self):
        ###
        #if order is X hours old, assume it won't get filled
        oldestAllowedDateTime = datetime.datetime.now() - datetime.timedelta(hours=0, minutes=0)  #TODO  should be  datetime.timedelta(hours=4, minutes=0) except maybe sandbox
        print("oldestAllowedDateTime:"+str(oldestAllowedDateTime))
        
        #check previous purchases & merge previous orders if very old
        orders =  __main__.geminiClient.client.get_active_orders()
        print(orders)
        print("# orders:"+str(len(orders)))
        for order in orders:
            if(orderIdPrefix  in str(order["client_order_id"])):
                orderId = order["id"]
                print(" orderId:" + orderId)
                clientOrderId = str(order["client_order_id"])
                print(" clientOrderId: " + clientOrderId)
                print(" remaining amount: " + str(order["remaining_amount"]))
                oldOrderDateTime = self.getOrderDateTimeFromOrderId(clientOrderId)
                print(" oldOrderDateTime: " + str(oldOrderDateTime))
                if(oldOrderDateTime < oldestAllowedDateTime):
                    print(" order status: stale")
                    self.refreshOrder(order)
                else:
                    print(" order status: fresh")

        #test convert orderID back to a datetime
        
        
        #note: with 12-15 halvings, the discount would reduce to almost nothing
        
        #todo: move items above here into "order processing"
        ###
    
    
    def checkMaxProgressToPurchase(self):
        #reduce to max if above max
        if(self.CurrentProgressToPurchaseQuantityInFiat >= self.PurchaseQuantityMaxInFiatPerPurchase):
            print("CurrentProgressToPurchaseQuantityInFiat exceeds max per purchase, reducing to max")
            self.CurrentProgressToPurchaseQuantityInFiat = self.PurchaseQuantityMaxInFiatPerPurchase
    
    ### cancel and re-submit order with a different price
    def refreshOrder(self, _orderObj):
        orderId = _orderObj["id"]
        clientOrderId = str(_orderObj["client_order_id"])
        oldOrderDateTime = self.getOrderDateTimeFromOrderId(clientOrderId)
        
        #cancel order
        print("cancelling: " + str(orderId))
        cancelResult = bidValueCostPerCoin = __main__.geminiClient.client.cancel_order(str(orderId))  #API call
        
        #add remaining value to current progress
        remainingValueInFiat = (float(_orderObj["remaining_amount"]) * float(_orderObj["price"]))
        print("adding remaining value of old order to current progress")
        print("remainingValueInFiat: " + str(remainingValueInFiat))
        print("self.CurrentProgressToPurchaseQuantityInFiat: " + str(self.CurrentProgressToPurchaseQuantityInFiat))
        self.CurrentProgressToPurchaseQuantityInFiat += remainingValueInFiat
        #reduce to max if above max
        self.checkMaxProgressToPurchase()
        print("self.CurrentProgressToPurchaseQuantityInFiat: " + str(self.CurrentProgressToPurchaseQuantityInFiat))
    
    
    #do a bunch of stuff, and then probably make a buy order
    #TODO: rename function
    def doPurchase(self, _orderOptions):
                      
        self.processActiveOrders()  #TODO: don't put this here. instead put it elsewhere and execute no more than once per hour?
        
        _quantityInFiat=round(self.CurrentProgressToPurchaseQuantityInFiat,2)
        
        #get price
        bidValueCostPerCoin = self.getTickerBid()
        pricePerCoin = bidValueCostPerCoin * (1.0000-self.DesiredDiscount) 
        pricePerCoin = round(pricePerCoin,2)
        print("bid price:" + str(pricePerCoin))
        if(pricePerCoin > self.HardMaximumCoinPrice):
            raise AssertionError("GeminiBuyDCAPostOnly coin price exceeds hard maximum")
                
        #determine coin purchase quantity
        coinQuantity = round(_quantityInFiat / pricePerCoin,8)  #assume 8 decimal places is max resolution on coin quantity
        print("coinQuantity:" + str(coinQuantity))
        
        if(coinQuantity < 0.00001):
            print("coinQuantity: " + str(coinQuantity))
            sys.exit("purchase quantity is too low (below 0.00001), increase purchase amount or decrease purchase frequency")

        #note
        print("estimated cost in fiat:" + str(pricePerCoin*coinQuantity))
        
        #order ID
        #orderId=str(uuid.uuid4())
        
        
        orderId=orderIdPrefix +datetime.datetime.now().strftime(orderIdDateFormat)
        print("orderId:"+orderId)
        
  
        
        #orderOptions=['maker-or-cancel']
        
        #place buy order                                                                                                                                                                                                                                                                                                                  
        result = __main__.geminiClient.client.new_order(client_order_id=orderId, symbol=self.PurchaseSymbol, amount=str(coinQuantity), price=str(pricePerCoin), side='buy', type='exchange limit', options=_orderOptions)  #API call
        print("purchase result: " + str(result))  
    
        
