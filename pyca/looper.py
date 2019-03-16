import time

def defaultFunction():
	print('loopit')


def loop(interval_seconds, execute_function):
	starttime=time.time()
	while True:
		print('interval triggered, accuracy:' + str((time.time() - starttime) % interval_seconds))
		execute_function()
		time.sleep(interval_seconds - ((time.time() - starttime) % interval_seconds)) 
