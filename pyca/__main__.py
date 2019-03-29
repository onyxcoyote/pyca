#!/usr/bin/env python3

import looper
import config
import geminiAPI
import geminiBuyDCAPostOnly
from __init__ import GLOBAL_VARS
#from __init__ import VARS


import datetime

geminiClient = None
geminiBuyRule = None



def main():
    print("start time:"+str(datetime.datetime.now()))
    
    print("===TODO: COPYING NOTICE===")
    
    print("===loading config===")

    GLOBAL_VARS.printMe()

    global geminiClient
    geminiClient = geminiAPI.getGeminiAPI()
    geminiClient.printMe()
    
    global geminiBuyRule
    geminiBuyRule = geminiBuyDCAPostOnly.getGeminiBuyDCAPostOnly()
    geminiBuyRule.printMe()

    print("===starting rules===")
    print("")
    
    looper.loop(interval_seconds=GLOBAL_VARS.SECONDS_PER_TICK,execute_function=doRules)
    
    print("===program end===")


def doRules():
    try:    
        print("==executing rules== " + str(datetime.datetime.now()))
        #geminiPurchasesPerDay = float(cfgGeminiBuyDCAPostOnly.PurchasesPerDay)
        #geminiPurchaseQuantityPerDayInFiat = float(cfgGeminiBuyDCAPostOnly.PurchaseQuantityPerDayInFiat)
        
        print("=GeminiBuyDCAPostOnly=")
        geminiBuyRule.doRule()


        print("==rules complete==" + str(datetime.datetime.now()))
        print
    except Exception as e:
        print(str(e))

main()



