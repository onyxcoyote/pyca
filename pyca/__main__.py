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

import looper
import config
import geminiAPI
import geminiTradeDCAPostOnly
import geminiBuyDCAPostOnly
import geminiSellDCAPostOnly
from __init__ import GLOBAL_VARS


import datetime

geminiClient = None
geminiBuyRule = None
geminiSellRule = None


def main():
    print("start time:"+str(datetime.datetime.now()))
    
    print("pyca")
    print("Copyright (C) 2019  onyxcoyote.com")
    print("GPL3.0, see LICENSE.txt")
    
    print("===loading config===")

    GLOBAL_VARS.printMe()

    global geminiClient
    geminiClient = geminiAPI.getGeminiAPI()
    geminiClient.printMe()
    
    global geminiBuyRule
    geminiBuyRule = geminiBuyDCAPostOnly.getGeminiBuyDCAPostOnly()
    geminiBuyRule.printMe()
    
    global geminiSellRule
    geminiSellRule = geminiSellDCAPostOnly.getGeminiSellDCAPostOnly()
    geminiSellRule.printMe()

    print("===starting rules===")
    print("")
    
    looper.loop(interval_seconds=GLOBAL_VARS.SECONDS_PER_TICK,execute_function=doRules)
    
    print("===program end===")


def doRules():
    try:    
        print("==executing rules== " + str(datetime.datetime.now()))
        #geminiPurchasesPerDay = float(cfgGeminiBuyDCAPostOnly.PurchasesPerDay)
        #geminiPurchaseQuantityPerDayInFiat = float(cfgGeminiBuyDCAPostOnly.PurchaseQuantityPerDayInFiat)
        
        if(geminiBuyRule.isEnabled()):
            print("=GeminiBuyDCAPostOnly=")
            geminiBuyRule.doRule()
        
        if(geminiSellRule.isEnabled()):
            print("=GeminiSellDCAPostOnly=")
            geminiSellRule.doRule()


        print("==rules complete==" + str(datetime.datetime.now()))
        print
    except Exception as e:
        print("Error: " + str(e)  + " Traceback: " + str(traceback.print_tb(e.__traceback__)))

main()



