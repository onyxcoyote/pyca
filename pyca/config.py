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
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchasesPerDay', 1.0)
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchaseQuantityPerDayInFiat', 10.0)
	exConfig.set('GeminiBuyDCAPostOnly', 'PurchaseSymbol', 'btcusd')
	exConfig.set('GeminiBuyDCAPostOnly','HardMaximumCoinPrice','8000')
	exConfig.set('GeminiBuyDCAPostOnly','NumberOfMinutesToConsiderOrderStale','120')
	exConfig.set('GeminiBuyDCAPostOnly','ChanceToProceedOnPurchasePerTick','0.05')
	exConfig.set('GeminiBuyDCAPostOnly','DesiredDiscount','0.10')
	exConfig.set('GeminiBuyDCAPostOnly','StartingProgressForFirstPurchase','0.60')
	
	

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



