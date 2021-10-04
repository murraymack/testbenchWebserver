# testbenchWebserver
*Webserver for doing automatic installs of BraiinsOS firmware and monitoring the miners when the install completes*

### Pre-Requisites
1. To get started with the program, you need to ```pip install -r requirements.txt```.

1. You also need to get a recent copy of the [BraiinsOS toolbox.zip](https://feeds.braiins-os.com/toolbox/latest/) (with the form of ```./files/bos-toolbox/bos-toolbox.bat```)

1.  Finally, you need a copy of the recent feeds, from https://feeds.braiins-os.com/, that needs to go in ```./files/feeds```

The program is also designed for automatic configuration and installation of a referral.
If you wish to change the base configuration or referral, the referral is located at ```./files/referral.ipk```, 
and the configuration is located at ```./files/config.toml```.

### Running
To run the program, run either ```python app.py``` on Windows, or ```python3 app.py``` on Linux.

*__The installation process will need to be edited on Linux, it relies on 2 .exe or .bat files,__*
```./files/asicseer_installer.exe``` *__and__* ```./files/bos-toolbox/bos-toolbox.bat```

The toolbox can be downloaded for Linux as well, it just needs the installation handler info changed in the *install* function inside ```./miner_data.py```
