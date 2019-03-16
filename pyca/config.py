import configparser
import os
import sys

class ConfigGeminiAPI:
	def __init__(self, _API_KEY, _API_SECRET):
		self.API_KEY = _API_KEY
		self.API_SECRET = _API_SECRET
	
	def printme(self):
		print("==ConfigAPI==")	
		print("API_KEY:"+self.API_KEY)
		#print("API_SECRET:"+self.API_SECRET)
	
class ConfigGeminiBuyDCAPostOnly:
	def __init__(self, _PurchasesPerDay, _PurchaseQuantityPerDayInFiat, _PurchaseSymbol):
		self.PurchasesPerDay = _PurchasesPerDay
		self.PurchaseQuantityPerDayInFiat = _PurchaseQuantityPerDayInFiat
		self.PurchaseSymbol = _PurchaseSymbol
	
	def printme(self):
		print("==ConfigGeminiBuyDCAPostOnly==")
		print("PurchasesPerDay:"+self.PurchasesPerDay)
		print("PurchaseQuantityPerDayInFiat:"+self.PurchaseQuantityPerDayInFiat)
		print("PurchaseSymbol:"+self.PurchaseSymbol)


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

def getConfigGeminiAPI(isSandbox):
	config = getConfig(isSandbox)

	API_KEY = config.get('APIKeys', 'API_KEY')
	API_SECRET = config.get('APIKeys', 'API_SECRET')
	
	cfg = ConfigAPI(API_KEY,API_SECRET)
	return cfg
        	
def getConfigGeminiBuyPostOnly(isSandbox):
	config = getConfig(isSandbox)

	PurchasesPerDay = config.get('GeminiBuyDCAPostOnly', 'PurchasesPerDay')
	PurchaseQuantityPerDayInFiat = config.get('GeminiBuyDCAPostOnly', 'PurchaseQuantityPerDayInFiat')
	PurchaseSymbol = config.get('GeminiBuyDCAPostOnly', 'PurchaseSymbol')

	cfg = ConfigGeminiBuyDCAPostOnly(PurchasesPerDay, PurchaseQuantityPerDayInFiat, PurchaseSymbol)
	return cfg


