#What it does
Dollar-cost-average bitcoin buying bot for gemini
-uses only maker orders (fees for API market orders on gemini are 0.1%)
-starts at a lower price (configurable) and gradually increases price (at a configurable time frame) up to the current best bid and refreshes to the current bid (in case of price going up and trade not executing)
	-this resubmitting of trades does not lose track over system reboots
-configurable frequencies and amounts or purchase
-configurable maximum coin price above which it will not buy


This is meant to be run on a computer or server that is generally up most of the time (because the purchase timer resets)



#INSTALL 

#INSTALL PYTHON3 and PIP3

#example debian
apt-get install python3
apt-get install python3-pip

#example centos7
yum install centos-release-scl scl-utils-build
yum install rh-python36-python
scl enable rh-python36 bash


#INSTALL PYTHON LIBRARIES
cd /tmp
mkdir pycabuild
cd pycabuild

#checkout a specific release of libraries to help mitigate against dependency attacks (v2.21.0)
cd /tmp/pycabuild
git clone https://github.com/kennethreitz/requests.git
cd requests
git fetch origin 5a1e738ea9c399c3f59977f2f98b083986d6037a 
git reset --hard FETCH_HEAD
pip3 install .

#checkout a specific release of libraries to help mitigate against dependency attacks (last checkin as of 2/9/2018)
cd /tmp/pycabuild
git clone https://github.com/mattselph/gemini-python-unoffc.git
cd gemini-python-unoffc
git fetch origin 684ae57b2c36cd96739e2b0d15db94ed6e27bba4
git reset --hard FETCH_HEAD
pip3 install .


#SET UP THIS PROGRAM
#download repository
#e.g.
cd /tmp/pycabuild
git clone TBD   #TODO

#copy all *.py files to the install location
mkdir /srv/pyca
cp /tmp/pycabuild/pyca/*.py /srv/pyca
cd /src/pyca

#run program to generate a blank config file (pyca.cfg)
update parameters in pyca.cfg:
	api_key/api_secret from gemini, needs trading permissions.  Do not require session heartbeat.
	leave is_sandbox as True for testing (gemini sandbox) or change to False to trade with actual money
	update other settings as desired



#run program manually
cd /srv/pyca
python3 .

#ideally set the program as a service so it runs automatically on startup





#UNINSTALL DEPENDENCIES (this may affect any other programs that rely on these)
#pip3 uninstall gemini-python-unoffc requests chardet urllib3 idna certifi
