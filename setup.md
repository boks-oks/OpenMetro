# Setting up the server

> [!NOTE]
> For simplicity, I will be calling the Windows 8.1 machine the "guest" and the machine hosting the proxy the "host".

1. Install mitmproxy using `pip install mitmproxy`.
> [!WARNING]
> You must install `mitmproxy` on another machine! The proxy needs to be active as the system starts up, otherwise the tiles won't update!

2. Run the server. Use the following command:
```
mitmdump -s OpenMetro.py --listen-port 8080 --set connection_strategy=lazy --set tls_version_client_min=TLS1
```

3. Change proxy in `inetcpl.cpl`.<br/>
On your guest, open Internet Settings (Win+R, `inetcpl.cpl`)<br/>
Under `Connections`, click `LAN Settings` then `Use a proxy server for your LAN.`.<br/>
Enter your host's IP and port (default 8080) in `Address` and `Port`.<br/>
4. Change proxy using `netsh`.<br/>
Open an admin `cmd` window.<br/>
Type `netsh winhttp set proxy IP:PORT` replacing IP and PORT with the IP and port used in `inetcpl.cpl`. 

5. Install mitmproxy's certificate.<br/>
On your guest, go to [mitm.it](http://mitm.it).<br/>
Download the certificate for Windows.<br/>
Install the certificate for the entire computer using MMC:<br/>
Open MMC (Win+R, mmc.exe)<br/>
File -> Add/Remove Snap-in -> Certificates -> Computer Account -> Leave all values at default -> OK.<br/>
Under Certificates, right-click Trusted Root Certification Authorities -> All Tasks -> Import -> Next.<br/>
Browse to the file you just downloaded (you may have to show all file types) and import it.<br/>

Once everything is done, reboot.
