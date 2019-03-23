import datetime



class VARS():
    def __init__(self):
        self.DETAILED_LOGGING_MODE = True
        self.SECONDS_PER_TICK = 6.0   #60.0
        self.TICKS_PER_DAY = (24*60*60)/self.SECONDS_PER_TICK

    def printMe(self):
        print("TICKS_PER_DETAILED_LOGGING_MODEDAY: " + str(self.DETAILED_LOGGING_MODE))
        print("SECONDS_PER_TICK: " + str(self.SECONDS_PER_TICK))
        print("TICKS_PER_DAY: " + str(self.TICKS_PER_DAY))


GLOBAL_VARS = VARS()


