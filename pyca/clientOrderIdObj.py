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



import time
import random
import traceback
import uuid
import datetime
import string

from __init__ import GLOBAL_VARS
import __main__
import config



ORDER_ID_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


#client_order_id string format: 
#   "PYCA-BUY|"+datetime using the format ORDER_ID_DATE_FORMAT+"|"+attemptNumber+"|"+random GUID
#   "PYCA-SEL|"+datetime using the format ORDER_ID_DATE_FORMAT+"|"+attemptNumber+"|"+random GUID

class clientOrderIdObj:           
    def __init__(self, _order_id_prefix, _str_client_order_id = None):
        
        self.order_id_prefix = _order_id_prefix
        
        if(_str_client_order_id is None):
            self.uuid = uuid.uuid4()
            self.order_datetime = datetime.datetime.now().strftime(ORDER_ID_DATE_FORMAT)
            self.attemptNumber = 1
            self.str_client_order_id = self.getOrderId()  #needs to be last in the list
        else:            
            if(_order_id_prefix in str(_str_client_order_id)):
                print(_str_client_order_id)
                self.str_client_order_id = _str_client_order_id  #needs to be first in the list
                self.order_datetime = self.getOrderDateTimeFromOrderId()
                self.attemptNumber = self.getAttemptNumberFromOrderId()
                self.uuid = self.getUUIDFromOrderId()
                
            else:
                #invalid client_order_id
                pass
        
    def getOrderDateTimeFromOrderId(self):
        stringParts = self.str_client_order_id.split('|')
        return datetime.datetime.strptime(stringParts[1].replace(self.order_id_prefix,"",1),ORDER_ID_DATE_FORMAT)

    def getAttemptNumberFromOrderId(self):
        stringParts = self.str_client_order_id.split('|')
        return int(stringParts[2])

    def getUUIDFromOrderId(self):
        stringParts = self.str_client_order_id.split('|')
        return uuid.UUID(stringParts[3])

    def incrementAttemptNumber(self):
        self.attemptNumber += 1

    def resetOrderDateTime(self):
        self.order_datetime = datetime.datetime.now().strftime(ORDER_ID_DATE_FORMAT)

    def getOrderId(self):
        return self.order_id_prefix +str(self.order_datetime)+"|"+str(self.attemptNumber)+"|"+str(self.uuid)
        
    def isOrderStale(self, oldestAllowedDateTime):
        if(self.order_datetime < oldestAllowedDateTime):
            return True
        else:
            return False
        
        
