import config
import gemini.client

def getGeminiAPI():
    configFile = config.getConfig()

    API_KEY = configFile.get('GeminiAPIKeys', 'API_KEY')
    API_SECRET = configFile.get('GeminiAPIKeys', 'API_SECRET')
    IS_SANDBOX = configFile.get('GeminiAPIKeys', 'is_sandbox')

    cfg = GeminiAPI(API_KEY,API_SECRET,IS_SANDBOX)
    return cfg

class GeminiAPI:
    def __init__(self, _API_KEY, _API_SECRET, _isSandBox):
        self.API_KEY = str(_API_KEY)
        self.API_SECRET = str(_API_SECRET)
        self.client = gemini.client.Client(api_key=self.API_KEY,api_secret=self.API_SECRET,sandbox=_isSandBox)

    def printMe(self):
        print("==ConfigAPI==")	
        print("(values omitted)")
        #print("API_KEY:"+self.API_KEY) #dont print that
        #print("API_SECRET:"+self.API_SECRET)  #dont print that

                    
