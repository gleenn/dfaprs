Bridge between APRS TNC and BRCMap server
=========================================

A process that runs in the background 

Before installation ensure that you have dfaprs deployment keys on the system.

Installation (Ubuntu)
---------------------

Serial configuration with the daemon managed by upstartd:

    sudo apt-get install -y git
    sudo apt-get install -y make
	sudo apt-get install -y python-setuptools
	sudo easy_install pip
	sudo pip install virtualenv
    git clone --depth=1 git@gitlab.com:discofish/dfaprs.git dfaprs
    cd dfaprs
    make 
    sudo make install
    sudo echo 'description "APRS to BRC Map bridge"

		start on runlevel [2345]
		stop on runlevel [!2345]

		expect fork

		respawn
		respawn limit 5 5

		script
		    export HOME=/root
		    chdir $HOME
		    exec /usr/local/bin/dfaprs --source="serial:///dev/ttyUSB*" -t file:///var/opt/dfaprs/beacons.json 2>&1 | logger -t dfaprs &
		    echo $$ > /var/run/dfaprs.pid
		end script

		post-start script
		end script

		pre-start script
		        echo Starting dfaprs
		end script

		pre-stop script
		        echo Stopping dfaprs
		end script
	' > /etc/init/dfaprs.conf
	sudo initctl reload-configuration
	sudo service dfaprs start 
	sudo tail -f /var/log/syslog

Installation (CentOS) 
----------------------

Network configuration with the daemon managed by systemd:

    sudo yum install -y git
    sudo yum install -y make
	sudo yum install -y python-setuptools
	sudo easy_install pip
	sudo pip install virtualenv
    git clone --depth=1 git@gitlab.com:discofish/dfaprs.git dfaprs
    cd dfaprs
    make 
    sudo make install
    sudo echo 'Description=APRS to BRC Map bridge

		[Service]
		ExecStart=/usr/bin/dfaprs --source=aprs://noam.aprs2.net --target=http://localhost:8091
		Restart=always
		StandardOutput=syslog
		SyslogIdentifier=dfaprs
		User=nobody
		Group=nobody
		WorkingDirectory=/root

		[Install]
		WantedBy=multi-user.target
	' > /usr/lib/systemd/system/dfaprs.service
	systemctl enable dfaprs
	systemctl start dfaprs
	tail -f /var/log/messages

To update:
	
	systemctl daemon-reload
	systemctl reset-failed dfaprs
	systemctl restart dfaprs


Calibrating TT4 TNC
--------------------

	- Turn on the radio 
	- Set frequency to 144.39 
	- Turn off squelching. Make sure you can hear modem buzzes clearly (it's extremely finicky indoors - e.g. moving the radio a couple of feet from one side of the table to another seems to make a big difference). 
	- Plug in TT4
	- Open terminal at 19200 bps, flow control off (sudo screen -fn /dev/ttyUSB0 19200,cs8, Ctrl-A k to exit)
	- Power cycle TT4, press ESC three times to go to command mode
	- Run MONITOR command to calibrate audio level. Set RXAMP so that the signal saturates around 80 (e.g. I set it to 10) and turn the volume knob so that static is somewhere in 50s. Output level is very, very sensitive to the volume knob position - turning it just a few degrees makes a huge difference. 80 max/50 avg levels seem to work ok, but we may want to fine tune the numbers.
	- Press any key to exit monitor, make sure that AMODE is set to TEXT, set ABAUD to 9600 (so that we can switch between TT4 & Kenwood without reconfiguring software), and type QUIT to exit command mode
	- Start dfaprs  

