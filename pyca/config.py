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

	exConfig.add_section('GeminiBuyDCAPostOnly')
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchasesPerDay', 1.0)
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchaseQuantityPerDayInFiat', 10.0)
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchaseSymbol', 'btcusd')

	with open('example.cfg', 'w') as cfgFile:
		exConfig.write(cfgFile)

def getConfig(isSandbox):
	config = configparser.RawConfigParser()

	if(not isSandbox):
		filename = 'prod.cfg'
		config.read('prod.cfg')	
	else:
		filename = 'sandbox.cfg'
		config.read('sandbox.cfg')	

	if(os.path.isfile(filename)):
		config.read(filename)
	else:
		print('config file not found, creating example config. rename to '+filename+' and update values')
		createExampleConfig()
		sys.exit()

	return config


        	



