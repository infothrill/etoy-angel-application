installLocation=${PWD}/angel-app
vPython=${installLocation}/bin/python

angelApp: virtual-python setupToolsBootStrap twisted ezPyCrypto xattr 
	cd ${installLocation} && svn co http://svn.gna.org/svn/angel-app/trunk angel-app
	wget "http://angelapp.missioneternity.org/index.py/Documentation/Install?action=AttachFile&do=get&target=angel_app.tgz" -O angel_app.tgz
	tar xvfz angel_app.tgz

zope-interface: virtual-python
	cd ${installLocation} && \
	wget http://www.zope.org/Products/ZopeInterface/3.0.1final/ZopeInterface-3.0.1.tgz && \
	tar xvfz ZopeInterface-3.0.1.tgz && \
	cd ZopeInterface-3.0.1 && ${vPython} setup.py install
	

xattr: setupToolsBootStrap
	cd ${installLocation} && svn co http://svn.red-bean.com/bob/xattr/trunk/ xattr && cd xattr && ${vPython} setup.py build && ${vPython} setup.py install

ezPyCrypto: pyCrypto
	cd ${installLocation} && \
	wget -O ezPyCrypto-0.1.1_lite.tgz "http://angelapp.missioneternity.org/index.py/Documentation/Install?action=AttachFile&do=get&target=ezPyCrypto-0.1.1_lite.tgz" && \
	tar xvzf ezPyCrypto-0.1.1_lite.tgz && \
	cd ezPyCrypto-0.1.1 && \
	${vPython} setup.py install
	

pyCrypto:
	cd ${installLocation} && \
	wget http://www.amk.ca/files/python/crypto/pycrypto-2.0.1.tar.gz && \
	tar xvzf pycrypto-2.0.1.tar.gz && \
	cd pycrypto-2.0.1 && \
	${vPython} setup.py install

	
twisted: virtual-python zope-interface
	cd ${installLocation} &&  \
	svn co svn://svn.twistedmatrix.com/svn/Twisted/trunk twisted &&  \
	cd twisted &&  \
	sed -e "s/'news']/'news', 'web2']/" < setup.py > bla && mv bla setup.py && \
	${vPython} setup.py install
	

setupToolsBootStrap: virtual-python ez_setup.py
	${vPython} ez_setup.py

ez_setup.py:
	wget http://peak.telecommunity.com/dist/ez_setup.py

virtual-python: ${installLocation} virtual-python.py
	python virtual-python.py --prefix=${installLocation}

virtual-python.py:
	wget http://peak.telecommunity.com/dist/virtual-python.py

${installLocation}:
	mkdir ${installLocation}

clean: 
	rm -rf angel-app && (rm virtual-python.py; ez_setup.py) || exit 0
