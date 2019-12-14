
from __init__ import GLOBAL_VARS
import __main__



    def getTickerBid(self):
        result = __main__.geminiClient.client.get_ticker(self.TradeSymbol)   #API call
        #print("ticker: " + str(result))  #e.g. dict value of:  {'bid': '3976.83', 'volume': {'BTC': '6.0073562', 'timestamp': 1552863000000, 'USD': '23832.206809991'}, 'ask': '3976.84', 'last': '3975.00'}
        print("ticker bid: " + result.get("bid"))
        return float(result.get("bid"))
    
    def getTickerAsk(self):
        result = __main__.geminiClient.client.get_ticker(self.TradeSymbol)   #API call
        #print("ticker: " + str(result))  #e.g. dict value of:  {'bid': '3976.83', 'volume': {'BTC': '6.0073562', 'timestamp': 1552863000000, 'USD': '23832.206809991'}, 'ask': '3976.84', 'last': '3975.00'}
        print("ticker ask: " + result.get("ask"))
        return float(result.get("bid"))
