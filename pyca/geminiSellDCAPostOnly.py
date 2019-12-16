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
import geminiAPIHelper  #todo: should be in the other class
import geminiTradeDCAPostOnly


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

class GeminiSellDCAPostOnly(geminiTradeDCAPostOnly.GeminiTradeDCAPostOnly):
    def __init__(self, _Enabled, _OrdersPerDay, _OrderQuantityPerDayInFiat, _TradeSymbol, _HardMinimumCoinPrice, _NumberOfMinutesToConsiderOrderStale, _ChanceToProceedOnOrderPerTick, _MaxDaysCatchup,  _DesiredPremium, _StartingProgressForFirstOrder):
        self.TradeSide = TRADE_SIDE
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
        
    
    
    
         



    
