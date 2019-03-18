import time
from __init__ import GLOBAL_VARS

def defaultFunction():
    print('loopit')


def loop(interval_seconds, execute_function):
    starttime=time.time()
    while True:
        if(GLOBAL_VARS.DETAILED_LOGGING_MODE):
            print('interval triggered, accuracy:' + str((time.time() - starttime) % interval_seconds))

        execute_function()
        time.sleep(interval_seconds - ((time.time() - starttime) % interval_seconds)) 
