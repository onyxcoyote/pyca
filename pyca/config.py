import configparser
import os
import sys
from geminiAPI import GeminiAPI
from geminiBuyDCAPostOnly import GeminiBuyDCAPostOnly	


		
def createExampleConfig():
	exConfig = configparser.RawConfigParser()
        	
	exConfig.add_section('GeminiAPIKeys')
	exConfig.set('GeminiAPIKeys', 'API_KEY', 'abcd1234')
	exConfig.set('GeminiAPIKeys', 'API_SECRET', 'QRZXabcd1234')
	exConfig.set('GeminiAPIKeys', 'is_sandbox', 'True')

	exConfig.add_section('GeminiBuyDCAPostOnly')
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchasesPerDay', 1.0)
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchaseQuantityPerDayInFiat', 10.0)
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchaseSymbol', 'btcusd')
	exConfig.set('GeminiBuyDCAPostOnly','HardMaximumCoinPrice','8000')
	exConfig.set('GeminiBuyDCAPostOnly','NumberOfMinutesToConsiderOrderStale','120')
	exConfig.set('GeminiBuyDCAPostOnly','ChanceToProceedOnPurchasePerTick','0.05')
	exConfig.set('GeminiBuyDCAPostOnly','DesiredDiscount','0.10')
	
	

	with open('example.cfg', 'w') as cfgFile:
		exConfig.write(cfgFile)

#def getConfig(isSandbox):
def getConfig():
	config = configparser.RawConfigParser()

	filename = 'pyca.cfg'

	if(os.path.isfile(filename)):
		config.read(filename)
	else:
		print('config file not found, creating example config. rename to '+filename+' and update values')
		createExampleConfig()
		sys.exit()

	return config


def isSandbox():
    return True  #todo


