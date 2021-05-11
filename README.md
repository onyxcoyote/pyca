#What it does
------------
Dollar-cost-average cryptocurency buying bot for gemini, features:
1. does periodic buys using only maker orders (fees for API maker orders on gemini are 0.1%, as of May 2021)
2. to try to get the best price, it starts at a lower price (configurable) and gradually increases price (at a configurable time frame) by resubmitting and gradually higher price up to the current best bid

	a. refreshes in relation to the current bid (in case of price going up and trade not executing) 

	b. this resubmitting of trades does not lose track over system reboots
3. configurable frequencies and amounts or purchase
4. configurable maximum coin price above which it will not buy
5. adds a random delay to purchase times to help mitigate adversaries predicting exact purchase times
6. there is a configurable maximum value spent per day in fiat, set by default to 500 fiat units per day (e.g. 500 USD), to help mitigate against accidentally spending more than desired on cryptocurrency purchased.  This can be changed in the configuration file if desired.
7. can do automatic sells of cryptocurrency too

NOTE: This program is meant to be run on a computer or server that is generally up most of the time (because the purchase timer resets in the case of a machine reboot), and for security purposes that computer would be dedicated to running this program.


#INSTALLATION
------------

##1. Install python3 and pip3:

###example debian
```
sudo apt-get install python3 python3-pip
```

###example centos7
```
yum install centos-release-scl scl-utils-build
yum install rh-python36-python
scl enable rh-python36 bash
```

##2. Clone repository:
```
git clone https://github.com/151henry151/pyca.git
```

##3 Create a virtual environment (venv) and install python libraries:
```
cd pyca
python3 -m venv venv
source venv/bin/activate
pip3 install gemini-python-unoffc requests chardet urllib3 idna certifi
```
NOTE: see https://docs.python.org/3/library/venv.html for more information on creation and use of virtual environments. To exit the virtual environment run ```deactivate```

##4. Run program to generate a blank config file (pyca.cfg):
```
python3 pyca
```

##5. Copy example.cfg to pyca.cfg:
```
cp example.cfg pyca.cfg
```
##5a. Update parameters in pyca.cfg: 
	api_key/api_secret from gemini, needs trading permissions.  Do not require session heartbeat.
	leave is_sandbox as True for testing (gemini sandbox) or change to False to trade with actual money
	update other settings as desired



##6. running program manually:
```
source venv/bin/activate
python3 pyca
```
If everything runs correctly, then you can go ahead and create a system service to run the program automatically on system startup and restart it if interrupted:


##6b. run program automatically on startup using systemd by creating this file in /etc/systemd/system/pyca.service:
```
[Unit]
Description=pyca

[Service]
WorkingDirectory=/home/username/pyca/
ExecStart=/home/username/pyca/venv/bin/python3 /home/username/pyca
Restart=always
RestartSec=45
StandardOutput=file:/var/log/pyca.log
StandardError=file:/var/log/pyca_error.log
SyslogIdentifier=pyca

[Install]
WantedBy=multi-user.target

```
Note that this example service file assumes you are using a virtualenv, if not you can modify the first path in ExecStart to point at your python3 binary.

##7. changing parameters

If parameters are changed in the pyca.cfg file, the program would need to be stopped and re-started. If you are running the program automatically with systemd as described in 6b, ```systemctl restart pyca.service```


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


