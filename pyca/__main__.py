#!/usr/bin/env python3

import looper
import config


cfgAPI=None

def main():
	print("==loading config==")

	global cfgGeminiAPI
	global cfgGeminiBuyDCAPostOnly

	cfgAPI = config.getConfigGeminiAPI(True)
	cfgSettings = config.getConfigGeminiBuyDCAPostOnly(True)

	cfgAPI.printme()
	cfgSettings.printme()

	print("==starting==")
	looper.loop(interval_seconds=6.0,execute_function=doRules)

def doRules():
	print('rules go here')
	if(cfgSettings.PurchasesPerDay>0):
		pass
		#increment amount
		#do purchase sometime, but check balance first	


main()


