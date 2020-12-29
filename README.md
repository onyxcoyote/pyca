#What it does
------------
Dollar-cost-average bitcoin buying bot for gemini, features:
1. does periodic buys using only maker orders (fees for API maker orders on gemini are 0.1%, as of August 2019)
2. to try to get the best price, it starts at a lower price (configurable) and gradually increases price (at a configurable time frame) by resubmitting and gradually higher price up to the current best bid

	a. refreshes in relation to the current bid (in case of price going up and trade not executing) 

	b. this resubmitting of trades does not lose track over system reboots
3. configurable frequencies and amounts or purchase
4. configurable maximum coin price above which it will not buy
5. adds a random delay to purchase times to help mitigate adversaries predicting exact purchase times
6. there is a hardcoded maximum value spent per day in fiat, currently 500 fiat units per day (e.g. 500 USD), to help mitigate against accidentally spending more than desired on cryptocurrency purchased.  This can be changed directly in the code if desired.


NOTE: This program is meant to be run on a computer or server that is generally up most of the time (because the purchase timer resets in the case of a machine reboot), and for security purposes that computer would be dedicated to running this program.


#INSTALLATION
------------

##1. INSTALL PYTHON3 and PIP3

###example debian
```
apt-get install python3
apt-get install python3-pip
```

###example centos7
```
yum install centos-release-scl scl-utils-build
yum install rh-python36-python
scl enable rh-python36 bash
```

##2a (either 2a or 2b). INSTALL PYTHON LIBRARIES (DIFFICULT WAY)
```
cd /tmp
mkdir pycabuild
cd pycabuild
```

###checkout a specific release of libraries to help mitigate against dependency attacks (v2.21.0)
```
cd /tmp/pycabuild
git clone https://github.com/kennethreitz/requests.git
cd requests
git fetch origin 5a1e738ea9c399c3f59977f2f98b083986d6037a 
git reset --hard FETCH_HEAD
pip3 install .
```

###checkout a specific release of libraries to help mitigate against dependency attacks (last checkin as of 2/9/2018)
```
cd /tmp/pycabuild
git clone https://github.com/mattselph/gemini-python-unoffc.git
cd gemini-python-unoffc
git fetch origin 684ae57b2c36cd96739e2b0d15db94ed6e27bba4
git reset --hard FETCH_HEAD
pip3 install .
```

##2b (either 2a or 2b). INSTALL PYTHON DEPENDECIES (EASY WAY)
```
pip3 install gemini-python-unoffc requests chardet urllib3 idna certifi
```


##3. SET UP THIS PROGRAM
###download repository
###e.g.
```
cd /tmp/pycabuild
git clone https://github.com/onyxcoyote/pyca.git
```

##4. copy all *.py files to the install location
```
mkdir /srv/pyca
cp /tmp/pycabuild/pyca/*.py /srv/pyca
cd /srv/pyca
```

##5. run program to generate a blank config file (pyca.cfg)
update parameters in pyca.cfg:
	api_key/api_secret from gemini, needs trading permissions.  Do not require session heartbeat.
	leave is_sandbox as True for testing (gemini sandbox) or change to False to trade with actual money
	update other settings as desired



##6a. run program manually
```
cd /srv/pyca
python3 .
```

NOTE: ideally set the program as a service so it runs automatically on startup


##6b. run program automatically on startup using systemd, for example
TODO: add pyca.service example 


##7. changing parameters

If parameters are changed in the pyca.cfg file, the program would need to be stopped and re-started.


##8. secure pyca.cfg

Since pyca.cfg contains api keys, it should be kept protected.  The recommended file permissions on pyca.cfg are 400, so only the user executing the program has access to read it.
```
chmod 400 pyca.cfg
```

#UNINSTALL
------------
##UNINSTALL PYTHON DEPENDENCIES (this may affect any other programs that rely on these)
#pip3 uninstall gemini-python-unoffc requests chardet urllib3 idna certifi

##UNINSTALL THIS PROGRAM
#just delete the downloaded files e.g. /src/pyca


