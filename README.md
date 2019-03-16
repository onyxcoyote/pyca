#INSTALL DEPENDENCIES

cd ~/repos
mkdir geminibuild
cd geminibuild

git clone https://github.com/kennethreitz/requests.git
pip3 install ~/repos/geminibuild/requests

git clone https://github.com/mattselph/gemini-python-unoffc.git
pip3 install ~/repos/geminibuild/gemini-python-unoffc


#UNINSTALL DEPENDENCIES
#pip3 uninstall gemini-python-unoffc requests chardet urllib3 idna certifi
