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

                    
