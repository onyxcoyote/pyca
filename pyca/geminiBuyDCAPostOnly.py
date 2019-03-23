import random
import traceback
import uuid
import datetime
import string

from __init__ import GLOBAL_VARS
import __main__
import config


#todo change param to snake case
ORDER_ID_PREFIX = "PYCA|"
ORDER_ID_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
ORDER_OPTIONS=['maker-or-cancel']



def getGeminiBuyDCAPostOnly():
    configFile = config.getConfig()

    PurchasesPerDay = configFile.get('GeminiBuyDCAPostOnly', 'PurchasesPerDay')
    PurchaseQuantityPerDayInFiat = configFile.get('GeminiBuyDCAPostOnly', 'PurchaseQuantityPerDayInFiat')
    PurchaseSymbol = configFile.get('GeminiBuyDCAPostOnly', 'PurchaseSymbol')
    HardMaximumCoinPrice = float(configFile.get('GeminiBuyDCAPostOnly', 'HardMaximumCoinPrice'))
    NumberOfMinutesToConsiderOrderStale = float(configFile.get('GeminiBuyDCAPostOnly', 'NumberOfMinutesToConsiderOrderStale')) #note: when using sandbox mode, it's recommended to use "0" for this value
    ChanceToProceedOnPurchasePerTick = float(configFile.get('GeminiBuyDCAPostOnly', 'ChanceToProceedOnPurchasePerTick'))
    MaxDaysCatchup = float(configFile.get('GeminiBuyDCAPostOnly', 'MaxDaysCatchup'))  #recommended to be at least 1.5 to catch up in case of maintenance windows up to 12 hours.
    DesiredDiscount = float(configFile.get('GeminiBuyDCAPostOnly', 'DesiredDiscount'))

    cfg = GeminiBuyDCAPostOnly(_PurchasesPerDay=PurchasesPerDay, _PurchaseQuantityPerDayInFiat=PurchaseQuantityPerDayInFiat, _PurchaseSymbol=PurchaseSymbol, _HardMaximumCoinPrice=HardMaximumCoinPrice, _NumberOfMinutesToConsiderOrderStale=NumberOfMinutesToConsiderOrderStale, _ChanceToProceedOnPurchasePerTick=ChanceToProceedOnPurchasePerTick, _MaxDaysCatchup=MaxDaysCatchup, _DesiredDiscount=DesiredDiscount)
    return cfg

class GeminiBuyDCAPostOnly:
    def __init__(self, _PurchasesPerDay, _PurchaseQuantityPerDayInFiat, _PurchaseSymbol, _HardMaximumCoinPrice, _NumberOfMinutesToConsiderOrderStale, _ChanceToProceedOnPurchasePerTick, _MaxDaysCatchup,  _DesiredDiscount, _StartingProgressForFirstPurchase = 0.99995):
        self.PurchasesPerDay = float(_PurchasesPerDay)
        self.PurchaseQuantityPerDayInFiat = float(_PurchaseQuantityPerDayInFiat)
        self.PurchaseSymbol = str(_PurchaseSymbol)
        self.NumberOfMinutesToConsiderOrderStale = float(_NumberOfMinutesToConsiderOrderStale)
        self.MaxDaysCatchup = _MaxDaysCatchup  #can purchase up to X times max per purchase if needed to "catch up" due to failed purchases, waiting for a better price, etc. (e.g. 2.0 = 200% max catchup single purchase)
        self.ChanceToProceedOnPurchasePerTick = _ChanceToProceedOnPurchasePerTick  #this value adds a random delay to purchases to mitigate exact timing prediction by an adversary
        self.DesiredDiscount = _DesiredDiscount  #uses a lower purchase price based on percent value.  The more the discount, the less likely the purchase will go through soon (or at all).
        self.HardMaximumCoinPrice = float(_HardMaximumCoinPrice)
        self.ProcessActiveOrdersFrequencyPerDay = (24*(60/5))  #every 5 minutes
        # _StartingProgressForFirstPurchase  #this value speeds up the first purchase
        
        if((self.PurchasesPerDay > 0) & (self.PurchaseQuantityPerDayInFiat > 0)):
            self.ProgressIncrementToPurchaseInFiatPerTick = (self.PurchaseQuantityPerDayInFiat/GLOBAL_VARS.TICKS_PER_DAY)
            self.CurrentProgressToPurchaseQuantityInFiat = (self.PurchaseQuantityPerDayInFiat/self.PurchasesPerDay)*_StartingProgressForFirstPurchase
            self.PurchaseQuantityInFiatPerPurchase = round((self.PurchaseQuantityPerDayInFiat/self.PurchasesPerDay), 2)
            self.PurchaseQuantityMaxInFiatPerPurchase = round(self.MaxDaysCatchup * self.PurchaseQuantityInFiatPerPurchase, 2)
            self.ProgressIncrementToProcessActiveOrdersPercentPerTick = (self.ProcessActiveOrdersFrequencyPerDay/GLOBAL_VARS.TICKS_PER_DAY)
            self.CurrentProgressToProcessActiveOrders = 0.995  #99.5%. process active orders pretty soon after starting
        else:
            self.ProgressIncrementToPurchaseInFiatPerTick = 0
            self.CurrentProgressToPurchaseQuantityInFiat = 0
            self.PurchaseQuantityInFiatPerPurchase = 0
            self.PurchaseQuantityMaxInFiatPerPurchase = 0
            self.ProgressIncrementToProcessActiveOrdersPercentPerTick = 0
            self.CurrentProgressToProcessActiveOrders = 0
            
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
        
        if((self.DesiredDiscount < 0.0000) | (self.DesiredDiscount > 0.1000)):  #maximum 10.0% discount
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
        print("HardMaximumCoinPrice:" + str(self.HardMaximumCoinPrice))
        print("NumberOfMinutesToConsiderOrderStale" + str(self.NumberOfMinutesToConsiderOrderStale))
        
        print("ProgressIncrementToPurchaseInFiatPerTick:" + str(self.ProgressIncrementToPurchaseInFiatPerTick))
        print("CurrentProgressToPurchaseQuantityInFiat:" + str(self.CurrentProgressToPurchaseQuantityInFiat))       
        print("PurchaseQuantityInFiatPerPurchase:" + str(self.PurchaseQuantityInFiatPerPurchase))
        print("PurchaseQuantityMaxInFiatPerPurchase:" + str(self.PurchaseQuantityMaxInFiatPerPurchase))
        
        print("ProgressIncrementToProcessActiveOrdersPercentPerTick:" + str(self.ProgressIncrementToProcessActiveOrdersPercentPerTick))
        print("ProgressIncrementToProcessActiveOrdersPercentPerTick:" + str(self.CurrentProgressToProcessActiveOrders))

    def printMinimal(self):
        print("CurrentProgressToPurchaseQuantityInFiat:" + str(round(self.CurrentProgressToPurchaseQuantityInFiat,2)) + "/" + str(self.PurchaseQuantityInFiatPerPurchase) + "  " + str(round((self.CurrentProgressToPurchaseQuantityInFiat / self.PurchaseQuantityInFiatPerPurchase) * 100, 3)) + "%.  Progress to process: " + str(round(self.CurrentProgressToProcessActiveOrders*100.0,2))+"%" )
        
    def doRule(self):        
        #purchase rule
        if((self.PurchasesPerDay > 0) & (self.PurchaseQuantityPerDayInFiat > 0)):
            #increment progress to next purchase
            self.CurrentProgressToPurchaseQuantityInFiat += self.ProgressIncrementToPurchaseInFiatPerTick
            
            #reduce to max if above max
            self.checkMaxProgressToPurchase()
            
            
            #increment progress to next process/resubmit
            self.CurrentProgressToProcessActiveOrders += self.ProgressIncrementToProcessActiveOrdersPercentPerTick
            
            #reduce to max if above max
            self.checkMaxProgressToProcess()
            
            
            self.printMinimal()
            
            
            #process/resubmit existing orders
            if(self.CurrentProgressToProcessActiveOrders >= 1.0):
                self.CurrentProgressToProcessActiveOrders = 0
                self.processActivePurchaseOrders()
                    
            
            #purchase
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
                        self.doNewPurchase()
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
        

    #resubmits stale orders at a worse price
    def processActivePurchaseOrders(self):

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
                clientOrderId = clientOrderIdObj(str(order["client_order_id"]))
                print(" clientOrderId: " + clientOrderId.getOrderId())
                print(" price: " + str(order["price"]))
                print(" remaining amount: " + str(order["remaining_amount"]))
                print(" attempt number: " + str(clientOrderId.attemptNumber))
                #oldOrderDateTime = clientOrderId.getOrderDateTimeFromOrderId()
                print(" oldOrderDateTime: " + str(clientOrderId.getOrderDateTimeFromOrderId()))

                
                if(clientOrderId.isOrderStale(oldestAllowedDateTime)):
                    print(" order status: stale")                    
                    self.resubmitPurchase(order)     #note: if order is expire, cut the "discount in half" keep repeating until the price is reasonable.  With 12-15 halvings, the discount would reduce to almost nothing, but would try to buy at better prices first
                else:
                    print(" order status: fresh")
        pass

    
    def checkMaxProgressToPurchase(self):
        #reduce to max if above max
        if(self.CurrentProgressToPurchaseQuantityInFiat >= self.PurchaseQuantityMaxInFiatPerPurchase):
            print("CurrentProgressToPurchaseQuantityInFiat exceeds max per purchase, reducing to max")
            self.CurrentProgressToPurchaseQuantityInFiat = self.PurchaseQuantityMaxInFiatPerPurchase
    
    def checkMaxProgressToProcess(self):
        #reduce to max if above max
        if(self.CurrentProgressToProcessActiveOrders >= 1.0):
            print("CurrentProgressToPurchaseQuantityInFiat exceeds max per purchase, reducing to max")
            self.CurrentProgressToProcessActiveOrders = 1.0
    
    #re-submits purchase order at a higher price (but not higher than the best bid)
    def resubmitPurchase(self, _orderObj):
        orderId = _orderObj["id"]
        clientOrderId = clientOrderIdObj(str(_orderObj["client_order_id"]))
        oldOrderDateTime = clientOrderId.getOrderDateTimeFromOrderId()
        
        #cancel order
        print("cancelling: " + str(orderId))
        cancelResult = bidValueCostPerCoin = __main__.geminiClient.client.cancel_order(str(orderId))  #API call
        
        #resubmit a new order
        clientOrderId.incrementAttemptNumber()
        clientOrderId.resetOrderDateTime()
        
        #calculate new discount
        if(clientOrderId.attemptNumber >= 12):  #reduce discount to exactly 0, because it's practically the same as 0 anyway, and would have a better chance of successful purchase
            discount = 0
        else:
            discount = (self.DesiredDiscount/clientOrderId.attemptNumber)
        
        #get price
        bidValueCostPerCoin = self.getTickerBid()
        pricePerCoin = bidValueCostPerCoin * (1.0000-discount) 
        pricePerCoin = round(pricePerCoin,2)
        print("bid price:" + str(pricePerCoin) + " discount: " + str(discount))
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
        
        result = __main__.geminiClient.client.new_order(client_order_id=clientOrderId.getOrderId(), symbol=self.PurchaseSymbol, amount=str(coinQuantity), price=str(pricePerCoin), side='buy', type='exchange limit', options=ORDER_OPTIONS)  #API call        
        print("purchase order result: " + str(result))

    def doNewPurchase(self):

        _quantityInFiat=round(self.CurrentProgressToPurchaseQuantityInFiat,2)
        
        #generate an order id
        clientOrderId=clientOrderIdObj()
        print(" orderId:"+clientOrderId.getOrderId())
        
        #get price
        bidValueCostPerCoin = self.getTickerBid()
        pricePerCoin = bidValueCostPerCoin * (1.0000-self.DesiredDiscount)  #Note that this logic only should be used for purchase and not sale! (in that case add "premium" instead of "discount")
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
        
        
        #example: ORDER_OPTIONS=['maker-or-cancel']        
        #place buy order                                                                                                                                                                                                                                                                                                                  
        result = __main__.geminiClient.client.new_order(client_order_id=clientOrderId.getOrderId(), symbol=self.PurchaseSymbol, amount=str(coinQuantity), price=str(pricePerCoin), side='buy', type='exchange limit', options=ORDER_OPTIONS)  #API call
        print(" purchase result: " + str(result))  
    
    
#client_order_id string format: "PYCA|"+datetime using the format ORDER_ID_DATE_FORMAT+"|"+attemptNumber+"|"+random GUID
class clientOrderIdObj:           
    def __init__(self, _str_client_order_id = None):
        if(_str_client_order_id is None):
            self.uuid = uuid.uuid4()
            self.order_datetime = datetime.datetime.now().strftime(ORDER_ID_DATE_FORMAT)
            self.attemptNumber = 1
            self.str_client_order_id = self.getOrderId()  #needs to be last in the list
        else:            
            if(ORDER_ID_PREFIX in str(_str_client_order_id)):
                print(_str_client_order_id)
                self.str_client_order_id = _str_client_order_id  #needs to be first in the list
                self.order_datetime = self.getOrderDateTimeFromOrderId()
                self.attemptNumber = self.getAttemptNumberFromOrderId()
                self.uuid = self.getUUIDFromOrderId()
                
            else:
                #invalid client_order_id
                pass
        
    def getOrderDateTimeFromOrderId(self):
        stringParts = self.str_client_order_id.split('|')
        return datetime.datetime.strptime(stringParts[1].replace(ORDER_ID_PREFIX,"",1),ORDER_ID_DATE_FORMAT)

    def getAttemptNumberFromOrderId(self):
        stringParts = self.str_client_order_id.split('|')
        return int(stringParts[2])

    def getUUIDFromOrderId(self):
        stringParts = self.str_client_order_id.split('|')
        return uuid.UUID(stringParts[3])

    def incrementAttemptNumber(self):
        self.attemptNumber += 1

    def resetOrderDateTime(self):
        self.order_datetime = datetime.datetime.now().strftime(ORDER_ID_DATE_FORMAT)

    def getOrderId(self):
        #return ORDER_ID_PREFIX +datetime.datetime.now().strftime(ORDER_ID_DATE_FORMAT)+"|"+
        return ORDER_ID_PREFIX +str(self.order_datetime)+"|"+str(self.attemptNumber)+"|"+str(self.uuid)
        
    def isOrderStale(self, oldestAllowedDateTime):
        if(self.order_datetime < oldestAllowedDateTime):
            return True
        else:
            return False
        
        
