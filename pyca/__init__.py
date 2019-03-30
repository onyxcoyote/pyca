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


