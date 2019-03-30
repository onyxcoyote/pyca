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
