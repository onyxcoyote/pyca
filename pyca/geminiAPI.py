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

import config
import gemini.client

def getGeminiAPI():
    configFile = config.getConfig()

    API_KEY = configFile.get('GeminiAPIKeys', 'API_KEY')
    API_SECRET = configFile.get('GeminiAPIKeys', 'API_SECRET')
    IS_SANDBOX = eval(configFile.get('GeminiAPIKeys', 'is_sandbox'))
    

    cfg = GeminiAPI(API_KEY,API_SECRET,IS_SANDBOX)
    return cfg

class GeminiAPI:
    def __init__(self, _geminiAPIKey, _geminiAPISecret, _isSandBox):
        self.isSandbox = eval(str(_isSandBox))
        self.client = gemini.client.Client(api_key=_geminiAPIKey, api_secret=_geminiAPISecret, sandbox=self.isSandbox)

    def printMe(self):
        print("==ConfigAPI==")	
        print("isSandbox:"+str(self.isSandbox))
        print("BASE_URI:"+self.client.BASE_URI)

                    
