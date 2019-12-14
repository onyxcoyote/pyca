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
	exConfig.set('GeminiBuyDCAPostOnly', 'Enabled', 'True')
	exConfig.set('GeminiBuyDCAPostOnly', 'OrdersPerDay', 1.0)
	exConfig.set('GeminiBuyDCAPostOnly', 'OrderQuantityPerDayInFiat', 10.0)
	exConfig.set('GeminiBuyDCAPostOnly', 'TradeSymbol', 'btcusd')
	exConfig.set('GeminiBuyDCAPostOnly', 'NumberOfMinutesToConsiderOrderStale','120')
	exConfig.set('GeminiBuyDCAPostOnly', 'MaxDaysCatchup','10')
	exConfig.set('GeminiBuyDCAPostOnly', 'ChanceToProceedOnOrderPerTick','0.05')
	exConfig.set('GeminiBuyDCAPostOnly', 'StartingProgressForFirstOrder','0.60')
	exConfig.set('GeminiBuyDCAPostOnly', 'HardMaximumCoinPrice','18000')	
	exConfig.set('GeminiBuyDCAPostOnly', 'DesiredDiscount','0.10')
	
	
	#Maybe use Trade instead of Order.  an Order is a thing and a trade is an action?
	exConfig.add_section('GeminiSellDCAPostOnly')
	exConfig.set('GeminiSellDCAPostOnly', 'Enabled', 'False')
	exConfig.set('GeminiSellDCAPostOnly', 'OrdersPerDay', 1.0)
	exConfig.set('GeminiSellDCAPostOnly', 'OrderQuantityPerDayInFiat', 10.0)
	exConfig.set('GeminiSellDCAPostOnly', 'TradeSymbol', 'btcusd')
    exConfig.set('GeminiSellDCAPostOnly', 'NumberOfMinutesToConsiderOrderStale','120')
    exConfig.set('GeminiSellDCAPostOnly', 'MaxDaysCatchup','10')	
	exConfig.set('GeminiSellDCAPostOnly', 'ChanceToProceedOnOrderPerTick','0.05')
	exConfig.set('GeminiSellDCAPostOnly', 'StartingProgressForFirstOrder','0.60')
	exConfig.set('GeminiSellDCAPostOnly', 'HardMinimumCoinPrice','25000')
	exConfig.set('GeminiSellDCAPostOnly', 'DesiredPremium','0.10')
	
	

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




