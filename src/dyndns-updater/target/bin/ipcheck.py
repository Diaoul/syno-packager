#!/usr/bin/env python
import base64, getopt, urllib, httplib, os, re, sys, stat, string, time, telnetlib, socket, binascii, urllib2, ConfigParser

try:
  import syslog
except:  # for platforms without syslog that try to use --syslog option
  class fake_syslog:
    def openlog(self,foo):
      raise Exception("Syslog not supported on this platform")
    def syslog(self,foo):
      raise Exception("Syslog not supported on this platform")
  syslog = fake_syslog()

try:
  from pysnmp import session 
  from pysnmp import error 
except:  
  class fake_session:
    class session:
      def __init__(self, a, c):
        raise Exception("Pysnmp missing, note you need version 1.x series of Pysnmp")
  session = fake_session()


Version = "0.245"

#
# ipcheck.py  
#
# Copyright GNU GENERAL PUBLIC LICENSE Version 2
# http://www.gnu.org/copyleft/gpl.html
#
# Author  : Kal <kal@users.sourceforge.net>
#
# Acknowledgements
# ================
# 
# dyndns crew             -a great service, reliable and professional
# Bobby Griggs            -ls_dyndns.py client 
# Vincent Zweije          -HTTP Date header idea for wuHHMM codes 
# Todd Rose               -Various suggestions and Linksys support 
# Yaron Minsky            -syslog patch and RT311 support
# Karen Chancellor        -RT311 tests
# Johannes Maslowski      -Draytek Vigor support
# Ulf Axelsson            -option -d fixes
# Del Hodge               -Netopia R9100 support
# Jan Bjorvik             -Cisco DSL support
# Robert Towster          -SMC barricade
# Onno Kortmann           -acctfile security suggestion
# Greg Bentz              -Linksys firmware 1.37, BSD Default route
# Erwin Burgstaller       -Cisco ISDN support
# Allen Eastwood          -HawkingTech support
# JP Szikora              -ZyXEL Prestige support
# Remi Zara               -NetBSD info
# Thomas Deselaers        -Debian package manpage
# Steve Warner            -SNMP support
# John Radimecky          -Watchguard SOHO support
# Mark Anderson           -router global var bug, time, testrun, docs
# Justin Kuo              -Nexland ISB2LAN
# Mark Lederer            -MacOS X
# Mark Aufflick           -Compex Netpassage 15
# Ken Frank               -UgatePlus, BSD 4.3 info
# Michel Bouissou         -Cayman DSL support
# Jan Carlson             -Gnet ADSL router model BB0040 support
# Tony Scicchitano        -BeOS local ip detection
# Bas Heijermans          -OS/2 tips and code
# Jeff Senn (jas)         -DLink DI701 w/PPPOE, Win32 Default Route
# Jim Richardson          -RT314 tests
# Andrew Gillham          -NetBSD route detection
# K Scott                 -Netgear logout page 
# Neal Probert            -custom dns bug
# Dave Burris             -sco openserver support
# Jerome Sautret          -Eicon modem support
# Daryl Boyd              -Nortel Instant Internet modem support
# John Ruttenberg         -Nexland Pro800Turbo support, and auth fixes
# Tony Scicchitano        -New SMC Barricade with password
# Michael O'Quinn         -searching syslog option for IP
# Lucas Bruand            -Check datfile for "w" mode
# Jon Hart                -Pointing out 255 can be used in dotted quad
# Cedric Moreau           -Alcatel Speed Touch Pro
# Frank Adcock            -DLink DI804 patch
# Darren Tucker           -tracking down 404 handling error
# Tristan Hill            -snmpget option
# Victor Ng               -platform strings case insensitive
# David Jordan            -Netgear338 support
# Juha Ylitalo            -code cleanup patches
# Larry Kluger            -DLink DI713P support
# Douglas Henke           -Siemens SpeedStream 2620 with password
# Paul Andreassen         -add port forwarding for Alcatel Speed Touch Pro
# J.D. Bronson            -upper opts typo, netgear 3114 fixes, zywall 10
# Adam Jenkins            -Barricade 7004VWBR patch see --VWBR
# Stephan Allene          -DLink DSL504 support
# Stephan Allene          -Correct bug with DLink DSL504 support
# Carl John Nobile        -badauth bug fix
# Cobe Higginbottom       -DI704 no password patch
# Marc Tanner             -DI614+ notes
# For CISCO IOS: Hansjoerg G.Henker  BitH@GMX.DE - www.c-bit.org
# Brad Crittenden         -VT1000v patch
# Mark Keisler            -default route detection fix
# Jason Anderson          -Linksys RT31P2 patch
# Tuan Hoang              -SMC Barricade logout fix
# Robert Holland          -Adtran Netvanta support
# Gene Cumm               -Barricade 7004 fixes and ssl check 
# David Bresson           -Linsys WRT56G
# Evan Carey              -Netgear WTG624
# Jordi Pujol             -Alcatel SpeedStream v.4.3.2.6
# Jordi Pujol             verify actual ip address with a DNS lookup
# Jordi Pujol             possibility to specify values of wilcard and backup_mx
# Bas van Oostveen        config file support through ConfigParser
#
# global constants
#
Updatehost = "members.dyndns.org"
Updatepage = "/nic/update"
Useragent = "ipcheck/" + Version
Fakeagent = "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)"

Touchage = 25                       # days after which to force an update
                                    # Touchage = 0 means don't ever force

Linuxip = "/sbin/ifconfig"    
Win32ip = "ipconfig /all"      
Sunip = "/usr/sbin/ifconfig"	
BSDip = "/sbin/ifconfig"         
Macip = "/sbin/ifconfig"          
Beosip = "netstat"
Os2ip = "ifconfig"
scoip = "/etc/ifconfig"
Otherip = "/sbin/ifconfig"          

Linuxrt = "/sbin/route -n"
Win32rt = "route print"
Sunrt = "/bin/netstat -irn"
BSDrt = "/sbin/route -n get default"
Macrt = "/usr/sbin/netstat -r"
Beosrt = "netstat"
Os2rt = "route -n get default"
scort = "/usr/bin/netstat -nr"
Otherrt = "/sbin/route -n show"


# regular expression for address
Addressgrep = re.compile ('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

def Usage():
  print """
Make sure you can write to the current directory for data
files and that you always run from the same directory.
The first time you run the script, you will be asked to run
with the --makedat option in addition to any other options.
This will create the data files for the hostnames and options 
your specify on the command line.  You should only do this once.
Subsequent runs should be made without the --makedat option.

For help with different options: python ipcheck.py -h
For supported devices listing  : python ipcheck.py --devices
For long detailed help text    : python ipcheck.py --help

Example 1: the external IP is on eth0 of the current machine
python ipcheck.py -l -i eth0 username password hostnames

Example 2: you are using the Linksys routing device
python ipcheck.py -l -L linksyspassword username password hostnames

Example 3: you want to use web based ip detection
python ipcheck.py -l -r checkip.dyndns.org:8245 ...

where ... is your dyndns username password and hostnames.
Hostnames should be comma delimited if there are more than one.
"""

def Options():
  print """
Usage  : ipcheck.py [options] Username Password Hostnames
or       ipcheck.py [options] --acctfile acct_info_file 

Options: -a address     manually specify the address 
         -r URL         NAT router, use web IP detection 
         -A text        scan syslog for an IP after text (Unix only) 
         -F filename    guess the WAN IP from a firewall log 
         -b VALUE       set backup mx option to VALUE (default NOCHG, values: YES|NO|NOCHG),
                        if option is present without value, VALUE is YES
         -c             custom dns option (default dynamic) 
         --config       load settings from configuration file
         -d dir         directory for data files (default current)
         -D             check also the ip against DNS services
         -e script      execute script after a successful update 
         -f             force update regardless of current state 
         -g             NAT router, let dyndns guess your IP 
                        (do not use this in a cronjob, try -r) 
         -h             print this help text 
         --help         print all available help text 
         -i interface   interface for local address (default ppp0) 
         -j             disable https 
         -l             log debugging text to ipcheck.log file 
         --syslog       log debugging text to syslog (Unix only) 
         -m mxhost      mx host (default NOCHG, values: mailexchanger|NOCHG) 
         -o             set dyndns offline mode 
         -p             proxy bypass on port 8245 
         -q             quiet mode (unless there is an error) 
         -s             static dns option (default dynamic) 
         -t             test run, do not send the update 
         -v             verbose mode 
         -w VALUE       set wildcard mode to VALUE (default NOCHG, values: ON|OFF|NOCHG) 
                        if option is present without value, VALUE is ON
         --makedat      create the ipcheck.dat file by dns lookup
         --devices      print router options (Linksys, Netgear, etc)
         -n ip 		the router IP address on the internal lan

For help with different options: python ipcheck.py -h
For supported devices listing  : python ipcheck.py --devices
For long detailed help text    : python ipcheck.py --help
"""

def Devices():
  print """
The script will locate the address of your router automatically by
looking at the default route of the machine you are running on.
Then it will read the status page for the external IP address
and use that for updates.  You need to specify the admin password
with the appropriate option."""
# remember -A already used above
  print """
         --pfile        device password below is actually a filename 
         -B password    New Barricade with password on port 88
         --VWBR         Use with -B to indicate 7004VWBR Router
         -C password    Cisco (667i) DSL router password
         -E             Eicon Diva (no password needed)
         -G             UgatePlus (no password needed)"""
# remember -A -D and -F already used above
  print """
         -H password    HawkingTech router password
         -I password    Cisco (700 series) ISDN router password
         -J password    ZyXEL prestige 642ME router password
         -K password    Compex NetPassage 15
         -L password    Linksys (BEFSR41) NAT router password
         -M password    MacSense password
         -N password    Netgear RT311 NAT router password
         -O password    Netopia (R9100) NAT router password
         -P port[,password]
                         Nexland Pro800Turbo, WAN port, port==any use the
                         first connected port; port=[01] use the port'th port
                         if available, else any; port=-[01] use port'th port
                         if available, else fail.  Specify password if
                         required.  For example, -P any,123 says to use the
                         first port and password 123.  -P 1 says prefer port
                         #1 and no password is required.  -P -0,xyz forces
                         port 0 and uses password xyz.
         -Q pword,iface password and interface for Instant Internet 
         -R password    Netgear FR3114 password
         -S             SMC Barricade (no password needed)
         --WBR password Use with -S if 2404WBR with password
         -T password    Alcatel Speed Touch Pro password
                        (you can also try -r 10.0.0.138/cgi/router/)
         -V password    Eicon Diva (see -E for no password)
         -W password    Watchguard SOHO NAT firewall password
         -X             Nexland router (no password set)
         -Y password    Cayman DSL 3220H NAT router password
         -Z password    ZyXEL 642R and Zywall 10 router password
         -1 password    DLink DSL504 password
         -2 password    Siemens SpeedStream 2620 router password
         -3 password    Netgear RT338 ISDN router
         -4 password    Gnet model BB0040 ADSL router password
         -5             DLink DI704 with no password
         -6 password    DLink DI704 password
         -7 password    DLink DI701 password
         -8 password    DLink DI804/DI614+ password
         -9 password    DLink DI713P password
         --WTG624=password    Netgear WTG624 router
         --VT1000v      Motorola VT1000v VoIP voice terminal (no password needed)
         --Draytek=password    
                        Vigor2000 NAT router password
         --Netvanta=password
                        Adtran Netvanta series routers,
                        both telnet and 'enable' passwords
                        must be configured to be same value
         
You can change the default username for the above devices with:
 
         -U username    override the default NAT router username
                        leave this option out to use the default

For Cisco IOS devices and any others that understand SNMP, you
can also use --snmp to detect the external IP.

         --snmp snmp_agent,community,numeric_objectid
 
You will need the v1.x pysnmp module from http://pysnmp.sourceforge.net/
The snmp code does not work with v2.x or 3.x of pysnmp
You also need to know the agent, community and numeric objectid:
python ipcheck.py --snmp 172.62.254.254,public,.1.3.5.2.1.2.10.2.5.4 ...
where ... = username password hostnames

Alternate/Generic SNMP retrieval
         --snmpget snmp_agent,community,numeric_objectid
You will need the v1.x pysnmp module from http://pysnmp.sourceforge.net/
The snmp code does not work with v2.x or 3.x of pysnmp
You also need to know the agent(hostname or ip), community and
numeric objectid:
python ipcheck.py --snmpget router,public,.1.3.6.1.4.1.343.6.23.1.12.1.2.3 ...
where ... = username password hostnames
This option will do a snmp get to the specified objectid which needs to be
that of the ip to be used in the update

         --forward port[/protocol],...
Ports to be forward from your router to this machine.
Defaults to tcp protocol. Stay set until router turned off.
example: -T password --forward=80,time/udp,21/6
"""

def HelpText():
  print """
Start ipcheck.py with no arguments to get some quick examples.

The script creates data files in the current working directory.
Make sure you have write permission and that you run the script
from the same directory each time.  You can use the -d option
to specify an alternate directory for data files. 

The first time you run the script, you will be asked to run
with the --makedat option.  This will create the data files
and complete the update.  You should only do this once.
Subsequent runs should be made without the --makedat option.

If -f is set, all hosts will be updated regardless of the 
current error, wait or IP state.  You should never need this. 

You can place your username password and hostnames in a file 
(all on the first line) and use the --acctfile option if you do 
not wish your password to show up on a ps. 

The best way to run ipcheck is in the /etc/ppp/ip-up.local file   
or the BSD ppp.linkup file (you will need to sleep 30 before 
running the script since ppp.linkup runs before the link is up.) 
The script will also run from a cronjob.  Just make sure the 
hostnames are the same in each execution.  You should make sure
it is using the same directory each time for data files.  The -d 
option can be used to specify where data files go.

The file ipcheck.dat contains the IP address and hostnames 
used in the last update.  If the ipcheck.dat file is older 
than """ + `Touchage` + """ days, an update will be made to touch the hostnames. 

The file ipcheck.wait is created if dyndns requests a wait 
before retrying.  This file will be automatically removed when 
the wait is no longer in effect. 

The file ipcheck.err is created if the response is an error. 
It will not try to update again until this error is resolved. 
You must remove the file yourself once the problem is fixed. 

If your ISP has a badly behaved transparent proxy on port 80  
traffic, you can try the -p option to use port 8245. 

If a http message is sent to dyndns.org, the response will be 
saved in the ipcheck.html file. 

Custom domains can be specified with the -c option.  You must 
first complete the create database step on the Dyndns web page. 
Suppose you have the domain ipcheck.org defined as an A record 
and your nodes aliased to ipcheck.org with CNAME records.  Use: 
python ipcheck.py -c username password ipcheck.org 

Note that if you intended to maintain both a custom domain and  
a dyndns domain (ie. ipcheck.dyndns.org) you should be using 
the -d option to keep the data files in separate directories. 
The custom domains are not compatible with the mx, backmx and 
wildcard options.  Setup your database accordingly. 

To be sure that the address is correct, the script performs a DNS
lookup and checks the answer against the local database address.
IMPORTANT: Updating DNS records takes some time, don't run this
script repeatedly, wait more than 5 minutes for DNS updates.

The script can find your public IP address in one of several ways:

1) interface IP detection is the default method and appropriate
if the machine you are running on has an interface with the public
IP addressed assigned.  The script knows how to query various 
operating systems for the address of an interface specified 
with the -i option (default ppp0).  Note on Win32 systems 
specify the MAC address device after -i and on BeOS systems 
specify the interface number after -i (eg. -i 1). 

2) router IP detection is used if you have a routing device
such as a Netgear RT311.  Use the --devices option to get a
help on specific devices.  This method is used by the script
if you specify one of the device-related options.

3) web IP detection may be used if your device is not supported
python ipcheck.py -r checkip.dyndns.org:8245 ... 
where ... = username password hostnames 
This method is used if you specify the -r option.
IMPORTANT: Do not run web based IP detection more often 
than once every 15 minutes.  It is costing dyndns bandwidth. 

4) you can explicitly set the desired IP address with -a

5) when -g is used, the script will not send any IP address
at all (even ones detected by the previous options).  Only
the account information will be sent to the dyndns server.
The dyndns server will assign the hostnames to the source
IP address of the request.  The assigned address is saved in
the ipcheck.dat file.  IMPORTANT: Do not run this from a cronjob
unless you know the address saved in the ipcheck.dat file 
matches locally detected public IP to prevent unnecessary updates.

If your have an unsupported device and are willing to help with
some testing, email me. 

The ipcheck homepage can be found at:
http://ipcheck.sourceforge.net/

Client development information can be found at:
http://support.dyndns.org/dyndns/clients/devel/

Please include the ipcheck.log file if you email me with a problem. 
kal@users.sourceforge.net
"""

    
class Logger:
  #
  # open a new log file in the target dir if logging
  # a race condition if there are tons of scripts
  # starting at the same time and should really use locking
  # but that would be overkill for this app
  #
  def __init__(self, logname = "ipcheck.log", verbose = 0, logging = 0, use_syslog = 0):
    self.logname = logname
    self.verbose = verbose
    self.logging = logging
    self.syslog = use_syslog
    self.prefix = "ipcheck.py: "

    asctime = time.asctime(time.localtime(time.time()))

    if self.syslog:
      syslog.openlog("ipcheck")
    if self.logging:
      self.logfp = open(self.logname, "w")
      self.logfp.write(Useragent + "\n")
      self.logfp.write(self.prefix + asctime + "\n")
      self.logfp.write(self.prefix + "logging to " + self.logname + "\n")
      self.logfp.close()
    if self.verbose:
      print Useragent 
      print self.prefix + asctime 

  # normal logging message
  def logit(self, logline):
    if self.verbose:
      print self.prefix + logline
      if self.syslog:
        syslog.syslog(logline)
    if self.logging:
      self.logfp = open(self.logname, "a")
      self.logfp.write(self.prefix + logline + "\n")
      self.logfp.close()

  # logging message that gets printed even if not verbose
  def logexit(self, logline):
    print self.prefix + logline
    if self.logging:
      self.logfp = open(self.logname, "a")
      self.logfp.write(self.prefix + logline + "\n")
      self.logfp.close()
    if self.syslog:
      syslog.syslog(logline)


def DefaultRoute(logger, Tempfile):
  logger.logit("Searching default route on sys.platform = " + sys.platform)
  iphost = ""
  platform = string.lower(sys.platform)
  if string.find(platform, "win32") != -1:
    logger.logit("WIN32 default route detection for router.")
    os.system (Win32rt + " > " + Tempfile)
    fp = open(Tempfile, "r")
    try:
     while 1:
      fileline = fp.readline()
      if not fileline:
        break
      # jas:
      # the code that was here did not work at all for the output
      # of 'route print' on my win98 box.
      # Here is a very simple version that works well...
      tst = string.split(fileline)
      if len(tst) > 2 and tst[0] == "0.0.0.0": 
        iphost = tst[2]
        break
    finally:
       fp.close()
  elif string.find(platform, "linux") != -1:
    logger.logit("Linux default route detection for router.")
    fp = os.popen(Linuxrt, "r")
    lines = string.split(fp.read(), "\n")
    fp.close()
    for fileline in lines:
      if string.find(fileline, "UG") != -1:
        if string.find(fileline, "0.0.0.0") != -1:
          ipmatch = Addressgrep.search(fileline)
          ip1 = ipmatch.group()
          p1 = string.find(fileline, ip1) + len(ip1)
          ipmatch = Addressgrep.search(fileline, p1)
          iphost = ipmatch.group()
          break

  elif string.find(platform, "sunos") != -1:
    logger.logit("Sunos default route detection for router.")
    fp = os.popen(Sunrt, "r")
    content = fp.read()
    fp.close()
    p1 = string.find(content, "default")
    if p1 != -1:
      ipmatch = Addressgrep.search(content, p1+8)
      iphost = ipmatch.group()

  elif string.find(platform, "darwin") != -1:
    logger.logit("Darwin default route detection for router.")
    fp = os.popen(Macrt, "r")
    content = fp.read()
    fp.close()
    p1 = string.find(content, "default")
    if p1 != -1:
      ipmatch = Addressgrep.search(content, p1+8)
      iphost = ipmatch.group()

  elif string.find(platform, "netbsd") != -1:
    logger.logit("NetBSD default route detection for router.")
    fp = os.popen(BSDrt, "r")
    content = fp.read()
    fp.close()
    p1 = string.find(content, "gateway")
    if p1 != -1:
      ipmatch = Addressgrep.search(content, p1+8)
      iphost = ipmatch.group()

  elif string.find(platform, "freebsd") != -1:
    logger.logit("Freebsd default route detection for router.")
    fp = os.popen(BSDrt, "r")
    content = fp.read()
    fp.close()
    p1 = string.find(content, "gateway")
    if p1 != -1:
      ipmatch = Addressgrep.search(content, p1+8)
      iphost = ipmatch.group()

  elif string.find(platform, "os2") != -1:
    logger.logit("OS2 default route detection for router.")
    os.system (Os2rt + " > " + Tempfile)
    fp = open(Tempfile, "r")
    while 1:
      fileline = fp.readline()
      if not fileline:
        break
      p1 = string.find(fileline, "default")
      if p1 != -1:
        ipmatch = Addressgrep.search(fileline, p1+8)
        iphost = ipmatch.group()
        break
    fp.close()

  elif string.find(platform, "sco") != -1:
    logger.logit("SCO default route detection for router.")
    os.system (Scort + " > " + Tempfile)
    fp = open(Tempfile, "r")
    while 1:
      fileline = fp.readline()
      if not fileline:
        break
      p1 = string.find(fileline, "default")
      if p1 != -1:
        ipmatch = Addressgrep.search(fileline, p1+8)
        iphost = ipmatch.group()
        break
    fp.close()

  elif string.find(platform, "beos") != -1:
    logger.logexit("BeOS default route detection via network settings file.")
    fp = open("/boot/home/config/settings/network", "r")
    while 1:
      fileline = fp.readline()
      if not fileline:
        break
      p1 = string.find(fileline, "ROUTER")
      if p1 != -1:
        ipmatch = Addressgrep.search(fileline, p1+8)
        iphost = ipmatch.group()
        break
    fp.close()

  else:
    logger.logit("Unknown platform default route detection for router.")
    os.system (Otherrt + " > " + Tempfile)
    fp = open(Tempfile, "r")
    while 1:
      fileline = fp.readline()
      if not fileline:
        break
      p1 = string.find(fileline, "default")
      if p1 != -1:
        ipmatch = Addressgrep.search(fileline, p1+8)
        iphost = ipmatch.group()
        break
    fp.close()

  return iphost


def BasicAuth(logger, iphost, page, user, passwd, outfile):

  ipdata = ""
  try:
    logger.logit("Basic authentication page: " + page)
    h1 = httplib.HTTP(iphost)
    h1.putrequest("GET", page)
    fakeagent = "Mozilla/4.76 [en] (X11; U; Linux 2.4.1-0.1.9 i586)"
    h1.putheader("USER-AGENT", fakeagent)
    authstring = base64.encodestring(user + ":" + passwd)
    authstring = string.replace(authstring, "\012", "")
    h1.putheader("AUTHORIZATION", "Basic " + authstring)
    h1.endheaders()
    errcode, errmsg, headers = h1.getreply()
    fp = h1.getfile()
    ipdata = fp.read()
    fp.close()
  except:
    logline = "Failed connecting to router at " + iphost
    logger.logexit(logline)
    logger.logexit("Exception: " + `sys.exc_info()[0]`)
    sys.exit(-1)

  # create an output file of the response
  fp = open(outfile, "w")
  fp.write(ipdata)
  fp.close()
  logger.logit(outfile + " file created")

  return ipdata



#
# taken directly from the examples directory in pysnmp distribution
# http://pysnmp.sourceforge.net/
#
# results of run are stored in retval and returned
#
class snmptable (session.session):
    """Retrieve a table from remote SNMP process
    """
    def __init__ (self, agent, community):
        """Explicitly call superclass's constructor as it gets overloaded
           by this class constructor and pass a few arguments alone.
        """   
        session.session.__init__ (self, agent, community)

    def run (self, objids):
        """Query SNMP agent for one or more Object IDs. The objid
           argument should be a list of strings where each string
           represents an Object ID in dotted numbers notation
           (e.g. ['.1.3.6.1.4.1.307.3.2.1.1.1.4.1']).
        """   

        # clear the retval
        retval = []

        # Convert string type Object ID's into numeric representation
        numeric_objids = map (self.str2nums, objids)

        # BER encode SNMP Object ID's to query
        encoded_objids = map (self.encode_oid, numeric_objids)

        # Since we are going to _query_ SNMP agent for Object ID's
        # associated value, there will be no variable values passed to
        # SNMP agent.
        encoded_values = []

        # Remember the beginning of the table
        head_encoded_objid = encoded_objids[0]
        
        # Traverse the agent's MIB
        while 1:
            # Build a complete SNMP message of type 'GETNEXTREQUEST', pass it
            # a list BER encoded Object ID's to query and an empty list of values
            # associated with these Object ID's (empty list as there is no point
            # to pass any variables values along the SNMP GETNEXT request)
            question = self.encode_request ('GETNEXTREQUEST', encoded_objids, encoded_values)

            # Try to send SNMP message to SNMP agent and receive a response.
            answer = self.send_and_receive (question)

            # Catch SNMP exceptions
            try:
                # As we get a response from SNMP agent, try to disassemble SNMP reply
                # and extract two lists of BER encoded SNMP Object ID's and 
                # associated values).
                (encoded_objids, encoded_values) = self.decode_response (answer)

            # SNMP agent reports 'no such name' when table is over
            except error.SNMPError, why:
                # If NoSuchName
                if why.status == 2:
                    # Return as we are done
                    return retval
                else:
                    raise error.SNMPError(why.status, why.index)

            # Stop at the end of the table
            if not self.oid_prefix_check (head_encoded_objid, encoded_objids[0]):
                # Return as we are done
                return retval
            
            # Decode BER encoded Object ID.
            objids = map (self.decode_value, encoded_objids)

            # Decode BER encoded values associated with Object ID's.
            values = map (self.decode_value, encoded_values)

            # Convert two lists into a list of tuples for easier printing
            results = map (None, objids, values)

            # Just print them out
            # for (objid, value) in results:
            #    print objid + ' ---> ' + str(value)
            retval = retval + results

    def getrow (self, objid):
        """Query SNMP agent for one Object ID. The objid argument
           should be a string representing a Object ID in dotted
           numbers notation
           (e.g. '.1.3.6.1.4.1.307.3.2.1.1.1.4.1').
        """
        # Convert string type Object IDs into numeric representation
        numeric_objid = self.str2nums(objid)        

        # BER encode SNMP Object IDs to query
        encoded_objid = self.encode_oid(numeric_objid)

        # Build a complete SNMP message
        question = self.encode_request ('GETREQUEST', [encoded_objid], [])

        # Try to send SNMP message to SNMP agent and receive a response.
        answer = self.send_and_receive (question)

        # As we get a response from SNMP agent, try to disassemble SNMP reply
        # and extract two lists of BER encoded SNMP Object IDs and
        # associated values).
        (_encoded_objids, encoded_values) = self.decode_response (answer)

        # Decode BER encoded value.
        return self.decode_value(encoded_values[0])
###########################################################################
# Ipcheckfile is common baseclass for Datfile and Errorfile
class Ipcheckfile:
  # Constructor
  # You can give filename in here or leave it later.
  def __init__(self, fname=None):
    self.fname = fname

  # getFilename
  # Return: Filename (just matter of courtesy to make method for it)
  def getFilename(self):
    return self.fname

  # setFilename (just matter of courtesy to make method for it)
  def setFilename(self, fname):
    self.fname = fname

  # exists
  # Return: 1, file exists
  #         0, file doesn't exist
  # Note: this doesn't say that you can necessarily read it.
  def exists(self):
    exists = 0
    if "access" in os.__dict__.keys():
       exists = os.access (self.fname, os.F_OK)
    else:
      try:
        fp = open (self.fname, "r")
        fp.close()
        exists = 1
      except:
        pass
    return exists

###########################################################################
# Datfile handles reading and writing of datfile.
# Format:
# IPaddress
# hostname1
# hostname2
# hostname3
# ...
# Variables:
# - fname - name of datfile
# - ip - our public IP address
# - hostnames - list of hostnames related to the IP address on first line.
class Datfile(Ipcheckfile):
  #
  # Constructor
  def __init__(self, fname = None):
    Ipcheckfile.__init__(self, fname)
    self.ip = None

  #
  # Age of file based on difference between current time and the time,
  # when it was last modified.
  # Return: time difference in seconds.
  def getAge(self):
    currtime = time.time()
    mtime = os.stat(self.fname)[stat.ST_MTIME]
    fileage = (currtime - mtime) / (60*60*24)
    return fileage

  #
  # read
  # Read content of file and return tuple, where first variable is 
  # your public IP and second is list of hostnames assosiated to it.
  # Return: (ip,list of hostnames)
  def read(self):
    fp = open(self.fname, "r")
    lines = string.split(fp.read(), "\n")
    fp.close()
    ip = lines[0]
    hosts = []
    for line in lines[1:]:
      if line:
        hosts.append(line)
    assert hosts
    return (ip,hosts)

  # setIP
  # setIP for write() that will happen later.
  def setIP(self, ip):
    self.ip = ip

  # write
  # Write valid datfile based on ip and hostnames information.
  # If caller has not given them, use the values that have been
  # stored into instance variables.
  def write(self, ip = None, hostnames = None):
    if not ip:
      ip = self.ip

    assert ip and hostnames
    fp = open(self.fname, "w")
    fp.write(ip + "\n")
    for host in hostnames:
      fp.write(host + "\n")
    fp.close()


###########################################################################
# Errorfile handles reading, writing and analyzing of errfile.
class Errorfile(Ipcheckfile):
  #
  # Constructor
  # You can give filename in here or leave it later.
  def __init__(self, logger, fname = None):
    self.logger = logger
    Ipcheckfile.__init__(self, fname)

  # analyze
  # analyze content of existing errorfile.
  # Parameters:
  # - username that user would like to use.
  # - password that user would like to use.
  # - hostnames that user would like to update.
  # Return:
  # 1 - if fatal errors were encountered
  # 0 - if its OK to continue
  def analyze(self, username, password, hostnames):
    # generic_cases always print same message"
    generic_cases = { 
      "badagent" : ["Badagent contact author at kal@users.sourceforge.net."],
      "dnserr"   : ["Contact support@dyndns.org about dnserr error.",
                    "Attach the ipcheck.html file for details.",
                    "Erase the ipcheck.err file when the problem is fixed."],
      "numhost"  : ["Contact support@dyndns.org about numhost error.",
                    "Attach the ipcheck.html file for details.",
                    "Erase the ipcheck.err file when the problem is fixed."],
      "shutdown" : ["Service shutdown from dyndns.org",
                    "Check http://www.dyndns.org/status.shtml",
                    "Erase the ipcheck.err file when shutdown is over."]
    }
    # one_param cases add first argument to the end of first line.
    one_param = { 
      "badsys" :   ["system error",
                    "Erase the ipcheck.err file if this is correct now."],
      "!donator" : ["!donator", 
                    "Erase the ipcheck.err file when this problem is fixed."],
    }
    # hostname cases are shown only if first argument in error matches with
    # one of the hostnames that we would like to update.
    # Problematic hostname is shown at the end of first line.
    hostname_cases = {
      "abuse" :   ["abuse lockout",
                   "Use the form at http://support.dyndns.org/dyndns/abuse.shtml",
                   "Erase the ipcheck.err file when dyndns notifies you (by email)." ],
      "!active" : ["!active",
                   "You need to activate your Custom domain first.",
                   "Dyndns may require it to be properly delegated.",
                   "Erase the ipcheck.err file when the problem is fixed."],
      "nohost"  : ["nohost",
                   "You may be trying -s for a dynamic host or vice versa.",
                   "Erase the ipcheck.err if file this host is now created."],
      "notfqdn" : ["notfqdn",
                   "Erase the ipcheck.err file if this is really correct."],
      "!yours"  : ["!yours",
                   "Erase the ipcheck.err file when the problem is fixed."],
    }

    self.logger.logit("Handling errors in ipcheck.err file.")
    errors = []
    fatal = 0
    if self.exists():
      fp = open(self.fname, "r")
      errors = string.split(fp.read(), "\n")
      fp.close()
    for err in errors:
      fatal = 1
      errlist = string.split(err, " ")
      if err[:7] == "badauth":
        self.logger.logit("badauth found.")
        if errlist[1] == username and errlist[2] == password:
          self.logger.logexit("Previous authorization error encountered for")
          self.logger.logexit("Username:" + username)
          self.logger.logexit("Password:" + password)
          self.logger.logexit("Erase the ipcheck.err file if this is correct now.")
        else:
          self.logger.logit("trying new username or password.")
          self.logger.logit("ipcheck.err file removed and continuing.")
          os.unlink(self.fname)
          fatal = 0
      elif errlist[0] in generic_cases.keys():
        self.logger.logit(errlist[0] + " found.")
        for line in generic_cases[errlist[0]]:
          self.logger.logexit(line)
      elif errlist[0] in one_param.keys():
        self.logger.logit(errlist[0] + " found.")
        self.logger.logexit("Previous " + one_param[errlist[0]][0] + " encountered for " + errlist[1])
        for line in one_param[errlist[0]][1:]:
          self.logger.logexit(line)
      elif errlist[0] in hostname_cases.keys():
        self.logger.logit(errlist[0] + " found.")
        if errlist[1] in hostnames:
          self.logger.logexit("Previous " + hostname_cases[errlist[0]][0] + " encountered for host: " + errlist[1])
          for line in hostname_cases[errlist[0]][1:]:
            self.logger.logexit(line)
        else:
          fatal = 0
      elif err:
        self.logger.logexit("Unrecognized error in ipcheck.err file.")
        self.logger.logexit("Erase the ipcheck.err if there is no problem.")
      else:
        fatal = 0
      if fatal:
        break

    return fatal

  def write(self, description, fatal=None):
    if fatal:
      mode = "w"
    else:
      mode = "a"
    old = self.exists()
    fp = open(self.fname, mode)
    fp.write(description + "\n" )
    fp.close()
    if not old:
      self.logger.logit("ipcheck.err FILE CREATED.")

# acctfile has account information about your dyndns account.
# Format: username password hostname1,hostname2,hostname3
# Parameters:
# - acctfile - filename for account information
# - logger - instance of Logger for logging
# Return: ["username", "password", "hostname1,hostname2,hostname3"]
# Exception:
# - sys.exit(-1) in all problems.
def read_acctfile(fname, logger):
  try:
    fp = open (fname, "r")
    data = fp.read()
    fp.close()
  except:
    logger.logexit("Bad acctfile: " + fname)
    logger.logexit("Exception: " + `sys.exc_info()[0]`)
    sys.exit(-1)

  fields = string.split(data)
  if len(fields) != 3:
    logline = "File does not contain 3 arguments: " + fname
    logger.logexit(logline)
    sys.exit(-1)
  return fields

def read_pfile(fname, logger):
  if string.find(fname, "--pfile") != -1:
    logger.logexit("Bad usage.  Try: --pfile -X filename")
    logger.logexit("where X is the option letter for your device.")
    logger.logexit("Do not put the filename right after the --pfile option.")
    sys.exit(-1)

  try:
    fp = open (fname, "r")
    data = fp.read()
    fp.close()
  except:
    logger.logexit("Bad pfile: " + fname)
    logger.logexit("Exception: " + `sys.exc_info()[0]`)
    sys.exit(-1)

  # strip training CRLF
  if data[-1] == '\n' or data[-1] == '\r':
    data = data[:-1]
  if data[-1] == '\n' or data[-1] == '\r':
    data = data[:-1]

  return data

# check_ip verifies that ip address, which we are planning
# to send to dyndns.org is really valid.
# Parameters:
# - localip - ip that we are planning to send
# Return:
# - None, if its valid
# - string, which explains why its not valid.
def check_ip(localip):
  logline = None
  if not localip:
    # check if the router elif's found no address
    logline = "No address found on router." 
  elif localip == "0.0.0.0":
    # check if detected ip is not valid
    logline = "The router has external IP 0.0.0.0 assigned. "
  elif string.count(localip, ".") != 3:
    # check the IP to make sure it is sensible
    logline = "Invalid local address " + localip
  else:
    octets = string.split(localip, ".")
    ip = [0,0,0,0]
    try:
      for i in range(4):
        ip[i] = int(octets[i])
    except:
      ip = [0,0,0,0]

    # 0-255 in first three allowed, 1-255 in last also
    if ip[0] < 0 or ip[0] > 255 \
    or ip[1] < 0 or ip[1] > 255 \
    or ip[2] < 0 or ip[2] > 255 \
    or ip[3] < 0 or ip[3] > 255:
      logline = "Invalid local address " + localip

  return logline

# check_public_ip verifies that given ip address does not belong to 
# one of those private ip address spaces, which are reserved for
# intranet use.
# Parameters:
# - localip - ip that needs checking
# Return:
# - None, if its private address
# - string, if its valid address
def check_public_ip(localip):
  if localip[:4] != "127." \
  and localip[:8] != "192.168." \
  and localip[:3] != "10." \
  and localip[:4] != "172." \
  and localip[:2] != "0." \
  and string.find(localip, "255") == -1:
    return localip
  return None

class IpCheckConfigParser(ConfigParser.SafeConfigParser):
  def get(self, section, option, default=None):
    if default!=None and not self.has_option(section, option):
      return default
    return ConfigParser.SafeConfigParser.get(self, section, option)

  def getboolean(self, section, option, default=None):
    if default!=None and not self.has_option(section, option):
      return bool(default)
    return ConfigParser.SafeConfigParser.getboolean(self, section, option)

  def getfloat(self, section, option, default=None):
    if default!=None and not self.has_option(section, option):
      return float(default)
    return ConfigParser.SafeConfigParser.getfloat(self, section, option)

  def getint(self, section, option, default=None):
    if default!=None and not self.has_option(section, option):
      return int(default)
    return ConfigParser.SafeConfigParser.getint(self, section, option)

  def getlist(self, section, option, default=None):
    if default!=None and not self.has_option(section, option):
      if not isinstance(default, (list, tuple)):
        raise Exception("Default option '%s' for '%s' is not a list" % (default, option))
      return default
    return ConfigParser.SafeConfigParser.get(self, section, option).split(",")

def _main(argv):
  #
  # parse the command line options
  #
  if len(argv) == 1:
    Usage()
    sys.exit(0)
  
  try:
    loweropts = "a:bcd:e:fghi:jlm:n:opqr:stvw"
    upperopts = "A:B:C:DEF:GH:I:J:K:L:M:N:O:P:Q:R:ST:U:V:W:XY:Z:1:2:3:4:56:7:8:9:"
    wordopts = ["syslog", "pfile", "acctfile=", "help", "config=", "devices", "snmp=", "makedat", "snmpget=", "forward=", "VWBR", "WBR=", "VT1000v", "Draytek=", "Netvanta=","WTG624=", "Belkin_f5d7230"]
    opts, args = getopt.getopt(argv[1:], loweropts+upperopts, wordopts)
  except getopt.error, reason:
    print reason
    sys.exit(-1)

  #
  # PYTHON GURU NEEDED
  #
  # Is there any way in python to set argv to hide the command line?
  # ala the perl $0 = "orcus [accepting connections]";
  #
  # http://theoryx5.uwinnipeg.ca/CPAN/perl/pod/perlfaq8/Is_there_a_way_to_hide_perl_s_command_line_from_programs_such_as_ps_.html
  #

  #
  # load configuration file if given on command line
  #
  config_files = []
  for opt in opts:
    (lopt, ropt) = opt
    if lopt == "--config":
      if not os.path.isfile(ropt):
        print >>sys.stderr, "bad config option, %s file does not exist" % ropt
        sys.exit()
      config_files.append(ropt)
  cfg = IpCheckConfigParser()
  cfg.read(config_files)

  #
  # Global options
  #
  if cfg.has_option("ipcheck", "Updatehost"):
    global Updatehost
    Updatehost = cfg.get("ipcheck", "Updatehost")
  if cfg.has_option("ipcheck", "Updatepage"):
    global Updatepage
    Updatehost = cfg.get("ipcheck", "Updatepage")
  if cfg.has_option("ipcheck", "Fakeagent"):
    global Fakeagent
    Updatehost = cfg.get("ipcheck", "Fakeagent")
  if cfg.has_option("ipcheck", "Touchage"):
    global Touchage
    Updatehost = cfg.get("ipcheck", "Touchage")
  
  # 
  # ROUTER SUPPORT GLOBALS 
  # 
  # leave Linksys_host = "" to autodetect via the default route 
  # enter an ip here to skip the autodetect, this goes for all
  # the xxxx_host variables below
  # 
  routerIP = cfg.get('ipcheck', "routerIP", "")

  # 
  # Linksys router support details from bgriggs@pobox.com
  # 
  Linksys_user = cfg.get("ipcheck", "Linksys_user", " ")
  Belkin_f5d7230_page = cfg.get("ipcheck", "Belkin_f5d7230_page", "/")
  Linksys_page = cfg.get("ipcheck", "Linksys_page", "/Status.htm")
  
  Macsense_user = cfg.get("ipcheck", "Macsense_user", " ")
  Macsense_page = cfg.get("ipcheck", "Macsense_page", "/Status.htm")

  #
  # Motorola VT1000v
  MotorolaVT1000v_page = cfg.get("ipcheck", "MotorolaVT1000v_page", "/startupdata.html")
  #username and password are not needed 


  # 
  # Netgear router support 
  # 
  Netgear_user = cfg.get("ipcheck", "Netgear_user", "admin")
  Netgear_page = cfg.get("ipcheck", "Netgear_page", "/mtenSysStatus.html")
  Netgear314_page1 = cfg.get("ipcheck", "Netgear314_page1", "/rpMten.html")
  Netgear314_page2 = cfg.get("ipcheck", "Netgear314_page2", "/mtenSysStatus.html")
  NetgearFR_page = cfg.get("ipcheck", "NetgearFR_page", "/auth.html")
  Netgear_logout = cfg.get("ipcheck", "Netgear_logout", "/Logout.html")

  Netgear3114_user = cfg.get("ipcheck", "Netgear3114_user", "admin")
  Netgear3114_page1 = cfg.get("ipcheck", "Netgear3114_page1", "/")
  Netgear3114_page2 = cfg.get("ipcheck", "Netgear3114_page2", "/st_dhcp.htm")
  Netgear3114_page3 = cfg.get("ipcheck", "Netgear3114_page3", "/logout.htm")
  
  # Gene Cumm--Netgear FVS318	//GRC
  NetgearFVS318_page = cfg.get("ipcheck", "NetgearFVS318_page", "/sysstatus.html")

  # Netgear WTG624
  NetgearWTG624_page1 = cfg.get("ipcheck", "NetgearWTG624_page1", "/")
  NetgearWTG624_page2 = cfg.get("ipcheck", "NetgearWTG624_page2", "/RST_status.htm")
  NetgearWTG624_page3 = cfg.get("ipcheck", "NetgearWTG624_page3", "/LGO_logout.htm")

  #
  # DLink DI-804/DI-614+ router support
  #
  DI804_user = cfg.get("ipcheck", "DI804_user", "admin")
  DI804_page = cfg.get("ipcheck", "DI804_page", "/doc/m3.htm")
  DI614_page = cfg.get("ipcheck", "DI614_page", "/st_devic.html")

  #
  # DLink DI-713P router support
  #
  DI713P_user = cfg.get("ipcheck", "DI713P_user", "root")
  DI713P_page = cfg.get("ipcheck", "DI713P_page", "/cgi-bin/logi")

  #
  # DLink DI-704 router with no password support
  #
  DInop_user = cfg.get("ipcheck", "DInop_user", "admin")
  DInop_page = cfg.get("ipcheck", "DInop_page", "status.htm")

  #
  # DLink DI-704 router support
  #
  DI704_user = cfg.get("ipcheck", "DI704_user", "root")
  DI704_page = cfg.get("ipcheck", "DI704_page", "/cgi-bin/logi")

  #
  # DLink DSL-504 router support
  #
  DSL504_user = cfg.get("ipcheck", "DSL504_user", "admin")
  DSL504_page = cfg.get("ipcheck", "DSL504_page", "/sum/RoutingTable_ntpr.html")

  #
  # Draytek Vigor2000 router support 
  # 
  Draytek_user = cfg.get("ipcheck", "Draytek_user", "admin")
  Draytek_page = cfg.get("ipcheck", "Draytek_page", "/doc/digisdn.sht")
  
  # 
  # Netopia R9100 router support 
  # 
  Netopia_user = cfg.get("ipcheck", "Netopia_user", "")
  Netopia_page = cfg.get("ipcheck", "Netopia_page", "/WanEvtLog")
  
  # 
  # Cisco routers (667 and 770) 
  # uses telnet with no user name
  # 

  #
  # Adtran Netvanta routers
  # uses telnet with no user name
  # 

  #
  # SMC Barricade
  # 
  SMC_page = cfg.get("ipcheck", "SMC_page", "/status.HTM")
  #username and password are not needed 
  
  # 
  # HawkingTech router support 
  # 
  Hawking_user = cfg.get("ipcheck", "Hawking_user", "admin")
  Hawking_page = cfg.get("ipcheck", "Hawking_page", "/Monitor.htm")
  
  # 
  # ZyXEL router support, uses telnet
  # 
  
  # 
  # DI701 router support, uses telnet
  # 
  
  #
  # Watchguard SOHO firewall/router support
  #
  Watchguard_user = cfg.get("ipcheck", "Watchguard_user", "admin")
  Watchguard_page = cfg.get("ipcheck", "Watchguard_page", "/sysstat.htm")
  Watchguard_page2 = cfg.get("ipcheck", "Watchguard_page2", "/external.htm")
  
  # 
  # Nexland (but see Pro800Turbo, below)
  # 
  Nexland_page = cfg.get("ipcheck", "Nexland_page", "/status.htm")
  #username and password are not needed 

  # 
  # Nexland Pro800Turbo
  # 
  Pro800Turbo_page = cfg.get("ipcheck", "Pro800Turbo_page", "/status.html")
  Pro800Turbo_port = cfg.get("ipcheck", "Pro800Turbo_port", "any")
  Pro800Turbo_port_number = cfg.getint("ipcheck", "Pro800Turbo_port_number", 0)
  #username and password are not needed 

  # 
  # UgatePlus 
  # 
  Ugate_page = cfg.get("ipcheck", "Ugate_page", "/st_dhcp.htm")
  #username and password are not needed 

  #
  # Eicon Diva 2430 SE ADSL Modem
  #
  Eicon_page = cfg.get("ipcheck", "Eicon_page", "/Status.htm")
  #username and password are not needed

  # 
  # Eicon Diva with password 
  # 
  Veicon_user = cfg.get("ipcheck", "Veicon_user", "")
  Veicon_page = cfg.get("ipcheck", "Veicon_page", "/login.htm")
  
  # Instant Internet router

  # 
  # Compex NetPassage 15
  # uses telnet with no username
  # 

  #
  # Cayman DSL 3220-H
  # uses telnet
  #
  Cayman_user = cfg.get("ipcheck", "Cayman_user", "admin")
  
  #
  # Gnet model BB0040 ADSL router
  # uses telnet
  #
  Gnet_user = cfg.get("ipcheck", "Gnet_user", "")
  
  #
  # Netgear RT338 ISDN router
  # uses telnet
  #
  Netgear338_user = cfg.get("ipcheck", "Netgear338_user", "")
  
  # 
  # Newer SMC Barricade with password on port 88
  # 
  Barricade_user = cfg.get("ipcheck", "Barricade_user", "admin")
  Barricade_page = cfg.get("ipcheck", "Barricade_page", "/status.HTM")
  
  # 
  # Siemens SpeedStream 2620 with password on port 88
  # 
  Siemens2620_page = cfg.get("ipcheck", "Siemens2620_page", "/MAIN.HTM")
  
  #
  # Alcatel Speed Touch Pro uses telnet
  #
  # username is not needed
  Alcatel_user = cfg.get("ipcheck", "Alcatel_user", " ")

  #
  # find config file
  #

  #
  # default options
  #
  opt_address = cfg.get("ipcheck", "opt_address", "")
  opt_force = cfg.getint("ipcheck", "opt_force", 0)
  opt_checkDNS = cfg.getint("ipcheck", "opt_checkDNS", 0)
  opt_logging = cfg.getint("ipcheck", "opt_logging", 0)
  opt_syslog  = cfg.getint("ipcheck", "opt_syslog", 0)
  opt_verbose = cfg.getint("ipcheck", "opt_verbose", 0)
  opt_hostnames = cfg.get("ipcheck", "opt_hostnames", "")
  opt_interface = cfg.get("ipcheck", "opt_interface", "ppp0")
  opt_username = cfg.get("ipcheck", "opt_username", "")
  opt_password = cfg.get("ipcheck", "opt_password", "")
  opt_static = cfg.getint("ipcheck", "opt_static", 0)
  opt_wildcard = cfg.get("ipcheck", "opt_wildcard", "NOCHG")
  opt_backupmx = cfg.get("ipcheck", "opt_backupmx", "NOCHG")
  opt_mxhost = cfg.get("ipcheck", "opt_mxhost", "NOCHG")
  opt_proxy = cfg.getint("ipcheck", "opt_proxy", 0)
  opt_router = cfg.get("ipcheck", "opt_router", "")
  opt_guess = cfg.getint("ipcheck", "opt_guess", 0)
  opt_quiet = cfg.getint("ipcheck", "opt_quiet", 0)
  opt_offline = cfg.getint("ipcheck", "opt_offline", 0)
  opt_execute = cfg.get("ipcheck", "opt_execute", "")
  opt_directory = cfg.get("ipcheck", "opt_directory", "")
  opt_acctfile = cfg.get("ipcheck", "opt_acctfile", "")
  opt_pfile = cfg.getint("ipcheck", "opt_pfile", 0)
  opt_natuser = cfg.get("ipcheck", "opt_natuser", "")
  opt_forward = cfg.getlist("ipcheck", "opt_forward", [])
  opt_Linksys_password = cfg.get("ipcheck", "opt_Linksys_password", "")
  opt_Linksys_router = cfg.getint("ipcheck", "opt_Linksys_router", 0)
  opt_Netgear_password = cfg.get("ipcheck", "opt_Netgear_password", "")
  opt_Netgear3114_password = cfg.get("ipcheck", "opt_Netgear3114_password", "")
  opt_NetgearWTG624_password = cfg.get("ipcheck", "opt_NetgearWTG624_password", "")
  opt_Draytek_password = cfg.get("ipcheck", "opt_Draytek_password", "")
  opt_Netopia_password = cfg.get("ipcheck", "opt_Netopia_password", "")
  opt_Cisco_password = cfg.get("ipcheck", "opt_Cisco_password = ", "")
  opt_SMC_router = cfg.getint("ipcheck", "opt_SMC_router", 0)
  opt_Nexland_router = cfg.getint("ipcheck", "opt_Nexland_router", 0)
  opt_Pro800Turbo_router = cfg.getint("ipcheck", "opt_Pro800Turbo_router", 0)
  opt_ISDNCisco_password = cfg.get("ipcheck", "opt_ISDNCisco_password", "")
  opt_Hawking_password = cfg.get("ipcheck", "opt_Hawking_password", "")
  opt_Zyxel_password = cfg.get("ipcheck", "opt_Zyxel_password", "")
  opt_Zyxel_ME_password = cfg.get("ipcheck", "opt_Zyxel_ME_password", "")
  opt_Watchguard_password = cfg.get("ipcheck", "opt_Watchguard_password", "")
  opt_DInop_router = cfg.getint("ipcheck", "opt_DInop_router", 0)
  opt_DI704_password = cfg.get("ipcheck", "opt_DI704_password", "")
  opt_DI701_password = cfg.get("ipcheck", "opt_DI701_password", "")
  opt_DI713P_password = cfg.get("ipcheck", "opt_DI713P_password", "")
  opt_DI804_password = cfg.get("ipcheck", "opt_DI804_password", "")
  opt_DSL504_password = cfg.get("ipcheck", "opt_DSL504_password", "")
  opt_snmp_agent = cfg.get("ipcheck", "opt_snmp_agent", "")
  opt_snmp_community = cfg.get("ipcheck", "opt_snmp_community", "")
  opt_snmp_objectid = cfg.get("ipcheck", "opt_snmp_objectid", "")
  opt_snmp_agent_prefix = cfg.get("ipcheck", "opt_snmp_agent_prefix", "")
  opt_custom = cfg.getint("ipcheck", "opt_custom", 0)
  opt_testrun = cfg.getint("ipcheck", "opt_testrun", 0)
  opt_makedat = cfg.getint("ipcheck", "opt_makedat", 0)
  opt_Compex_password = cfg.get("ipcheck", "opt_Compex_password", "")
  opt_Cayman_password = cfg.get("ipcheck", "opt_Cayman_password", "")
  opt_Gnet_password = cfg.get("ipcheck", "opt_Gnet_password", "")
  opt_Ugate_router = cfg.getint("ipcheck", "opt_Ugate_router", 0)
  opt_II_password = cfg.get("ipcheck", "opt_II_password", "")
  opt_Belkin_f5d7230_router = cfg.getint("ipcheck", "opt_Belkin_f5d7230_router", 0)
  opt_II_interface = cfg.get("ipcheck", "opt_II_interface", "")
  opt_Eicon_router = cfg.getint("ipcheck", "opt_Eicon_router", 0)
  opt_Veicon_password = cfg.get("ipcheck", "opt_Veicon_password", "")
  opt_Barricade_password = cfg.get("ipcheck", "opt_Barricade_password", "")
  opt_7004VWBR = cfg.getint("ipcheck", "opt_7004VWBR", 0)
  opt_WBR = cfg.get("ipcheck", "opt_WBR", "")
  opt_Siemens2620_password = cfg.get("ipcheck", "opt_Siemens2620_password", "")
  opt_after_syslog = cfg.get("ipcheck", "opt_after_syslog", "")
  opt_firewall_log = cfg.get("ipcheck", "opt_firewall_log", "")
  opt_Macsense_password = cfg.get("ipcheck", "opt_Macsense_password", "")
  opt_MotorolaVT1000v_router = cfg.getint("ipcheck", "opt_MotorolaVT1000v_router", 0)
  opt_AlcatelSTP_password = cfg.get("ipcheck", "opt_AlcatelSTP_password", "")
  opt_no_https = cfg.getint("ipcheck", "opt_no_https", 0)
  opt_Netgear338_password = cfg.get("ipcheck", "opt_Netgear338_password", "")
  opt_Netvanta_password = cfg.get("ipcheck", "opt_Netvanta_password", "")

  #
  # check verbose, logging and detailed help options first
  # check directory to place logging file
  #
  for opt in opts:
    (lopt, ropt) = opt
    if lopt == "-l":
      opt_logging = 1
    elif lopt == "--syslog":
      opt_syslog = 1
    elif lopt == "-v":
      opt_verbose = 1
    elif lopt == "--devices":
      Devices()
      sys.exit(0)
    elif lopt == "--help":
      Usage()
      Options()
      Devices()
      HelpText()
      sys.exit(0)
    elif lopt == "-h":
      Options()
      sys.exit(0)
    elif lopt == "-d":
      if os.path.isdir(ropt):
        opt_directory = ropt
      else:
        print "bad directory option"
        sys.exit()

      # fix the dir name to end in slash
      if opt_directory[-1:] != "/":
        opt_directory = opt_directory + "/"

  #
  # create the logger object
  #
  if opt_directory:
    logger = Logger(opt_directory + "ipcheck.log", opt_verbose, opt_logging, opt_syslog)
    logline = "opt_directory set to " + opt_directory
    logger.logit(logline)
  else:
    logger = Logger("ipcheck.log", opt_verbose, opt_logging, opt_syslog)

  #
  # check acctfile option
  #
  for opt in opts:
    (lopt, ropt) = opt
    if lopt == "--acctfile":
      opt_acctfile = ropt
      logline = "opt_acctfile set to " + opt_acctfile
      logger.logit(logline)

  #
  # check pfile option
  #
  for opt in opts:
    (lopt, ropt) = opt
    if lopt == "--pfile":
      opt_pfile = 1
      logline = "opt_pfile set" 
      logger.logit(logline)

  if not (config_files and opt_username and opt_password and opt_hostnames) and (len(args) != 3 and not opt_acctfile):
    Usage()
    sys.exit(0)

  #
  # okay now parse rest of the options and log as needed
  #
  for opt in opts:
    (lopt, ropt) = opt
    if lopt == "-a":
      opt_address = ropt
      logline = "opt_address set to " + opt_address
      logger.logit(logline)
    elif lopt == "-D":
      opt_checkDNS = 1
      logline = "requested to check the ip against DNS"
      logger.logit(logline)
    elif lopt == "-i":
      opt_interface = ropt
      logline = "opt_interface set to " + opt_interface
      logger.logit(logline)
    elif lopt == "-f":
      opt_force = 1
      logline = "opt_force set " 
      logger.logit(logline)
    elif lopt == "-j":
      opt_no_https = 1
      logline = "opt_no_https set " 
      logger.logit(logline)
    elif lopt == "-w":
      if ropt != "":
        opt_wildcard = "ropt"
      else:
        opt_wildcard = "ON"
      logline = "opt_wildcard set to " + opt_wildcard
      logger.logit(logline)
    elif lopt == "-s":
      opt_static = 1
      logline = "opt_static set " 
      logger.logit(logline)
    elif lopt == "-c":
      opt_custom = 1
      logline = "opt_custom set " 
      logger.logit(logline)
    elif lopt == "-b":
      if ropt != "":
        opt_backupmx = "ropt"
      else:
        opt_backupmx = "YES"
      logline = "opt_backupmx set to " + opt_backupmx
      logger.logit(logline)
    elif lopt == "-p":
      opt_proxy = 1
      logline = "opt_proxy set " 
      logger.logit(logline)
    elif lopt == "-m":
      opt_mxhost = ropt
      logline = "opt_mxhost set to " + opt_mxhost
      logger.logit(logline)
    elif lopt == "-r":
      opt_router = ropt
      logline = "opt_router set to " + opt_router
      logger.logit(logline)
    elif lopt == "-g":
      opt_guess = 1
      logline = "opt_guess set " 
      logger.logit(logline)
    elif lopt == "-t":
      opt_testrun = 1
      logline = "opt_testrun set " 
      logger.logit(logline)
    elif lopt == "--makedat":
      opt_makedat = 1
      logline = "opt_makedat set " 
      logger.logit(logline)
    elif lopt == "-q":
      opt_quiet = 1
      logline = "opt_quiet set " 
      logger.logit(logline)
    elif lopt == "-o":
      opt_offline = 1
      logline = "opt_offline set " 
      logger.logit(logline)
    elif lopt == "-e":
      opt_execute = ropt
      logline = "opt_execute set to " + opt_execute
      logger.logit(logline)
    elif lopt == "-U":
      opt_natuser = ropt
      logline = "opt_natuser set to " + opt_natuser
      logger.logit(logline)

      Linksys_user = opt_natuser
      Macsense_user = opt_natuser
      Netgear_user = opt_natuser
      Netgear3114_user = opt_natuser
      Draytek_user = opt_natuser
      Netopia_user = opt_natuser
      Hawking_user = opt_natuser
      Watchguard_user = opt_natuser
      Veicon_user = opt_natuser
    elif lopt == "--Belkin_f5d7230":
      opt_Belkin_f5d7230_router = 1
      logline = "opt_Belkin_f5d7230_router set " 
      logger.logit(logline)
      Cayman_user = opt_natuser
      Gnet_user = opt_natuser
      Barricade_user = opt_natuser
      DI804_user = opt_natuser
      Alcatel_user = opt_natuser

    elif lopt == "--VT1000v":
      opt_MotorolaVT1000v_router = 1
      logline = "opt_MotorolaVT1000v_router set " 
      logger.logit(logline)
    elif lopt == "-M":
      if opt_pfile == 1:
        opt_Macsense_password = read_pfile(ropt, logger)
        logger.logit("opt_Macsense_password from file")
      else:
        opt_Macsense_password = ropt
        logger.logit("opt_Macsense_password from command line")
      logger.logit("*" * len(opt_Macsense_password))
    elif lopt == "-L":
      opt_Linksys_router = 1
      if opt_pfile == 1:
        opt_Linksys_password = read_pfile(ropt, logger)
        logger.logit("opt_Linksys_password from file")
      else:
        opt_Linksys_password = ropt
        logger.logit("opt_Linksys_password from command line")
      logger.logit("*" * len(opt_Linksys_password))
    elif lopt == "-N":
      if opt_pfile == 1:
        opt_Netgear_password = read_pfile(ropt, logger)
        logger.logit("opt_Netgear_password from file")
      else:
        opt_Netgear_password = ropt
        logger.logit("opt_Netgear_password from command line")
      logger.logit("*" * len(opt_Netgear_password))
    elif lopt == "-R":
      if opt_pfile == 1:
        opt_Netgear3114_password = read_pfile(ropt, logger)
        logger.logit("opt_Netgear3114_password from file")
      else:
        opt_Netgear3114_password = ropt
        logger.logit("opt_Netgear3114_password from command line")
      logger.logit("*" * len(opt_Netgear3114_password))
    elif lopt == "--Draytek":
      if opt_pfile == 1:
        opt_Draytek_password = read_pfile(ropt, logger)
        logger.logit("opt_Draytek_password from file")
      else:
        opt_Draytek_password = ropt
        logger.logit("opt_Draytek_password from command line")
      logger.logit("*" * len(opt_Draytek_password))
    elif lopt == "-O":
      if opt_pfile == 1:
        opt_Netopia_password = read_pfile(ropt, logger)
        logger.logit("opt_Netopia_password from file")
      else:
        opt_Netopia_password = ropt
        logger.logit("opt_Netopia_password from command line")
      logger.logit("*" * len(opt_Netopia_password))
    elif lopt == "-C":
      if opt_pfile == 1:
        opt_Cisco_password = read_pfile(ropt, logger)
        logger.logit("opt_Cisco_password from file")
      else:
        opt_Cisco_password = ropt
        logger.logit("opt_Cisco_password from command line")
      logger.logit("*" * len(opt_Cisco_password))
    elif lopt == "-S":
      opt_SMC_router = 1
      logline = "opt_SMC_router set " 
      logger.logit(logline)
    elif lopt == "-G":
      opt_Ugate_router = 1
      logline = "opt_Ugate_router set " 
      logger.logit(logline)
    elif lopt == "-E":
      opt_Eicon_router = 1
      logline = "opt_Eicon_router set "
      logger.logit(logline)
    elif lopt == "-V":
      if opt_pfile == 1:
        opt_Veicon_password = read_pfile(ropt, logger)
        logger.logit("opt_Veicon_password from file")
      else:
        opt_Veicon_password = ropt
        logger.logit("opt_Veicon_password from command line")
      logger.logit("*" * len(opt_Veicon_password))
    elif lopt == "-B":
      if opt_pfile == 1:
        opt_Barricade_password = read_pfile(ropt, logger)
        logger.logit("opt_Barricade_password from file")
      else:
        opt_Barricade_password = ropt
        logger.logit("opt_Barricade_password from command line")
      logger.logit("*" * len(opt_Barricade_password))
    elif lopt == "--VWBR":
      opt_7004VWBR = 1
    elif lopt == "--WBR":
      opt_WBR = ropt
    elif lopt == "-Q":
      Qopts = string.split(ropt, ",")
      if len(Qopts) != 2:
        logline = "Bad -Q option: " + ropt
        logger.logexit(logline)
        sys.exit(-1)
      logger.logit(logline)
      if opt_pfile == 1:
        opt_II_password = read_pfile(Qopts[0], logger)
        logger.logit("opt_II_password from file")
      else:
        opt_II_password = Qopts[0]
        logger.logit("opt_II_password from command line")
      logger.logit("*" * len(opt_II_password))

      opt_II_interface = Qopts[1]
      logline = "opt_II_interface = " + opt_II_interface
    elif lopt == "-X":
      opt_Nexland_router = 1
      logline = "opt_Nexland_router set " 
      logger.logit(logline)
    elif lopt == "-P":
      opt_Pro800Turbo_router = 1
      ropt_save = ropt
      cindex = string.find(ropt,",")
      if cindex == -1:
        ropt_port = ropt
        Pro800Turbo_password = None
      else:
        ropt_port = ropt[:cindex]
        Pro800Turbo_password = ropt[cindex+1:]

      if ropt_port == 'any':
        Pro800Turbo_port = 'any'
      else:
        if ropt_port[0] == '-':
          Pro800Turbo_port = 'force'
          ropt_port = ropt_port[1:]
        else:
          Pro800Turbo_port = 'prefer'        
        try:
          ropt_int = int(ropt_port)
          if ropt_int < -1 or ropt_int > 1:
            raise ValueError("invalid port value %s" % (ropt_save))
          Pro800Turbo_port_number = ropt_int
        except:
          logline = "Bad -P option %s" % (ropt_save)
          logger.logexit(logline)
          sys.exit(-1)
      logline = "opt_Pro800Turbo port %s %d" % (Pro800Turbo_port,
                                                Pro800Turbo_port_number)
      logger.logit(logline)
    elif lopt == "--forward":
      opt_forward_ports = string.split(ropt, ",")
      if len(opt_forward_ports)==0:
        logger.logexit("Not ports specified to forward")
        sys.exit(-1)
      for opt_forward_port in opt_forward_ports:
        opt_forward_portprotocol=string.split(opt_forward_port,"/")
        if len(opt_forward_portprotocol)==1:
          opt_forward_portprotocol=opt_forward_portprotocol+["tcp"]
        if len(opt_forward_portprotocol)!=2:
          logline = "Bad -forward option %s" % opt_forward_port
          logger.logexit(logline)
          sys.exit(-1)
        opt_forward=opt_forward+[ opt_forward_portprotocol ]
      logline = "opt_forward %s" % str(opt_forward)
      logger.logit(logline)
    elif lopt == "-I":
      if opt_pfile == 1:
        opt_ISDNCisco_password = read_pfile(ropt, logger)
        logger.logit("opt_ISDNCisco_password from file")
      else:
        opt_ISDNCisco_password = ropt
        logger.logit("opt_ISDNCisco_password from command line")
      logger.logit("*" * len(opt_ISDNCisco_password))
    elif lopt == "-H":
      if opt_pfile == 1:
        opt_Hawking_password = read_pfile(ropt, logger)
        logger.logit("opt_Hawking_password from file")
      else:
        opt_Hawking_password = ropt
        logger.logit("opt_Hawking_password from command line")
      logger.logit("*" * len(opt_Hawking_password))
    elif lopt == "-J":
      if opt_pfile == 1:
        opt_Zyxel_ME_password = read_pfile(ropt, logger)
        logger.logit("opt_Zyxel_ME_password from file")
      else:
        opt_Zyxel_ME_password = ropt
        logger.logit("opt_Zyxel_ME_password from command line")
      logger.logit("*" * len(opt_Zyxel_ME_password))
    elif lopt == "-Z":
      if opt_pfile == 1:
        opt_Zyxel_password = read_pfile(ropt, logger)
        logger.logit("opt_Zyxel_password from file")
      else:
        opt_Zyxel_password = ropt
        logger.logit("opt_Zyxel_password from command line")
      logger.logit("*" * len(opt_Zyxel_password))
    elif lopt == "-2":
      if opt_pfile == 1:
        opt_Siemens2620_password = read_pfile(ropt, logger)
        logger.logit("opt_Siemens2620_password from file")
      else:
        opt_Siemens2620_password = ropt
        logger.logit("opt_Siemens2620_password from command line")
      logger.logit("*" * len(opt_Siemens2620_password))
    elif lopt == "-3":
      if opt_pfile == 1:
        opt_Netgear338_password = read_pfile(ropt, logger)
        logger.logit("opt_Netgear338_password from file")
      else:
        opt_Netgear338_password = ropt
        logger.logit("opt_Netgear338_password from command line")
      logger.logit("*" * len(opt_Netgear338_password))
    elif lopt == "-4":
      if opt_pfile == 1:
        opt_Gnet_password = read_pfile(ropt, logger)
        logger.logit("opt_Gnet_password from file")
      else:
        opt_Gnet_password = ropt
        logger.logit("opt_Gnet_password from command line")
      logger.logit("*" * len(opt_Gnet_password))
    elif lopt == "-5":
      opt_DInop_router = 1
    elif lopt == "-6":
      if opt_pfile == 1:
        opt_DI704_password = read_pfile(ropt, logger)
        logger.logit("opt_DI704_password from file")
      else:
        opt_DI704_password = ropt
        logger.logit("opt_DI704_password from command line")
      logger.logit("*" * len(opt_DI704_password))
    elif lopt == "-7":
      if opt_pfile == 1:
        opt_DI701_password = read_pfile(ropt, logger)
        logger.logit("opt_DI701_password from file")
      else:
        opt_DI701_password = ropt
        logger.logit("opt_DI701_password from command line")
      logger.logit("*" * len(opt_DI701_password))
    elif lopt == "-8":
      if opt_pfile == 1:
        opt_DI804_password = read_pfile(ropt, logger)
        logger.logit("opt_DI804_password from file")
      else:
        opt_DI804_password = ropt
        logger.logit("opt_DI804_password from command line")
      logger.logit("*" * len(opt_DI804_password))
    elif lopt == "-9":
      if opt_pfile == 1:
        opt_DI713P_password = read_pfile(ropt, logger)
        logger.logit("opt_DI713P_password from file")
      else:
        opt_DI713P_password = ropt
        logger.logit("opt_DI713P_password from command line")
      logger.logit("*" * len(opt_DI713P_password))
    elif lopt == "-1":
      if opt_pfile == 1:
        opt_DSL504_password = read_pfile(ropt, logger)
        logger.logit("opt_DSL504_password from file")
      else:
        opt_DSL504_password = ropt
        logger.logit("opt_DSL504_password from command line")
      logger.logit("*" * len(opt_DSL504_password))
    elif lopt == "-W":
      if opt_pfile == 1:
        opt_Watchguard_password = read_pfile(ropt, logger)
        logger.logit("opt_Watchguard_password from file")
      else:
        opt_Watchguard_password = ropt
        logger.logit("opt_Watchguard_password from command line")
      logger.logit("*" * len(opt_Watchguard_password))
    elif lopt == "-K":
      if opt_pfile == 1:
        opt_Compex_password = read_pfile(ropt, logger)
        logger.logit("opt_Compex_password from file")
      else:
        opt_Compex_password = ropt
        logger.logit("opt_Compex_password from command line")
      logger.logit("*" * len(opt_Compex_password))
    elif lopt == "-A":
      opt_after_syslog = ropt
      logline = "opt_after_syslog = " + ropt
      logger.logit(logline)
    elif lopt == "-F":
      opt_firewall_log = ropt
      logline = "opt_firewall_log = " + ropt
      logger.logit(logline)
    elif lopt == "-Y":
      if opt_pfile == 1:
        opt_Cayman_password = read_pfile(ropt, logger)
        logger.logit("opt_Cayman_password from file")
      else:
        opt_Cayman_password = ropt
        logger.logit("opt_Cayman_password from command line")
      logger.logit("*" * len(opt_Cayman_password))
    elif lopt == "-T":
      if opt_pfile == 1:
        opt_AlcatelSTP_password = read_pfile(ropt, logger)
        logger.logit("opt_AlcatelSTP_password from file")
      else:
        opt_AlcatelSTP_password = ropt
        logger.logit("opt_AlcatelSTP_password from command line")
      logger.logit("*" * len(opt_AlcatelSTP_password))
    elif lopt == "-n":
      routerIP = ropt
      logline = "opt_router_ip = " + ropt
      logger.logit(logline)

    elif lopt == "--snmp":

      snmpopts = string.split(ropt, ",")
      if len(snmpopts) != 3:
        logline = "Bad --snmp option: " + ropt
        logger.logexit(logline)
        sys.exit(-1)

      #
      # check snmp agent is an IP address
      #
      opt_snmp_agent = snmpopts[0]
      if string.count(opt_snmp, ".") != 3:
        logline = opt_snmp_agent + " bad snmp agent, IP address required"
        logger.logexit(logline)
        sys.exit(-1)
      opt_snmp_agent_prefix = string.join(string.split(opt_snmp_agent, ".", 3)[:2], ".")
  
      #
      # community can be anything
      #
      opt_snmp_community = snmpopts[1]

      #
      # check the objectid is numeric
      #
      opt_snmp_objectid = snmpopts[2]
      #objid_s = string.split(opt_snmp_objectid, '.')
      #objid_s = filter(lambda x: len(x), objid_s)
      #try:
      #  objid_n = map(lambda x: string.atol(x), objid_s)
      #except:
      #  logline = opt_snmp_objectid + " bad snmp objectid, numeric id required"
      #  logger.logexit(logline)
      #  sys.exit(-1)

      logger.logit("opt_snmp_agent = " + opt_snmp_agent)
      logger.logit("opt_snmp_agent_prefix = " + opt_snmp_agent_prefix)
      logger.logit("opt_snmp_community = " + opt_snmp_community)
      logger.logit("opt_snmp_objectid = " + opt_snmp_objectid)

    elif lopt == "--snmpget":

      try:
        (opt_snmp_agent, opt_snmp_community, opt_snmp_objectid) = string.split(ropt, ',')
      except:
        logger.logexit("Bad --snmpget option: " + ropt)
        sys.exit(-1)

      # Check for a half reasonable numeric object id
      if re.search("^\.([0-9]+\.)+[0-9]+$",opt_snmp_objectid) == None:
        logger.logexit("Bad Object ID: " + opt_snmp_objectid)
        sys.exit(-1)
    
      logger.logit("opt_snmp_agent = " + opt_snmp_agent)
      logger.logit("opt_snmp_community = " + opt_snmp_community)
      logger.logit("opt_snmp_objectid = " + opt_snmp_objectid)

    elif lopt == "--Netvanta":
      opt_Netvanta_password = ropt
      logger.logit("opt_Netvanta_password from command line")
      logger.logit("*" * len(opt_Netvanta_password))

    elif lopt == "--WTG624":
      if opt_pfile == 1:
        opt_NetgearWTG624_password = read_pfile(ropt, logger)
        logger.logit("opt_NetgearWTG624_password from file")
      else:
        opt_NetgearWTG624_password = ropt
        logger.logit("opt_NetgearWTG624_password from command line")
      logger.logit("*" * len(opt_NetgearWTG624_password))

  #
  # handle the username, password, hostnames part
  #
  if opt_acctfile:
    args = read_acctfile(opt_acctfile, logger)

  if not opt_username:
    opt_username = args[0] 
  logline = "opt_username = " + opt_username
  logger.logit(logline)

  if not opt_password:
    opt_password = args[1] 
  logger.logit("opt_password = " + "*" * len(opt_password))

  if not opt_hostnames:
    opt_hostnames = args[2] 
  logline = "opt_hostnames = " + opt_hostnames
  logger.logit(logline)
  hostnames = string.split(opt_hostnames, ",")
    
  #
  # taint check, make sure each hostname is a dotted fqdn
  #
  for host in hostnames:
    if not "." in host:
      logline = "Bad hostname: " + host
      logger.logexit(logline)
      sys.exit(-1)

  #
  # check if hostname is a custom domain
  #
  domains = [ \
"at-band-camp.net",
"ath.cx",
"barrel-of-knowledge.info",
"barrell-of-knowledge.info",
"better-than.tv",
"blogdns.com",
"blogdns.net",
"blogdns.org",
"blogsite.org",
"boldlygoingnowhere.org",
"broke-it.net",
"buyshouses.net",
"cechire.com",
"dnsalias.com",
"dnsalias.net",
"dnsalias.org",
"dnsdojo.com",
"dnsdojo.net",
"dnsdojo.org",
"does-it.net",
"doesntexist.com",
"doesntexist.org",
"dontexist.com",
"dontexist.net",
"dontexist.org",
"doomdns.com",
"doomdns.org",
"dvrdns.org",
"dyn-o-saur.com",
"dynalias.com",
"dynalias.net",
"dynalias.org",
"dynathome.net",
"dyndns.ws",
"endofinternet.net",
"endofinternet.org",
"endoftheinternet.org",
"est-a-la-maison.com",
"est-a-la-masion.com",
"est-le-patron.com",
"est-mon-blogueur.com",
"for-better.biz",
"for-more.biz",
"for-our.info",
"for-some.biz",
"for-the.biz",
"forgot.her.name",
"forgot.his.name",
"from-ak.com",
"from-al.com",
"from-ar.com",
"from-az.net",
"from-ca.com",
"from-co.net",
"from-ct.com",
"from-dc.com",
"from-de.com",
"from-fl.com",
"from-ga.com",
"from-hi.com",
"from-ia.com",
"from-id.com",
"from-il.com",
"from-in.com",
"from-ks.com",
"from-ky.com",
"from-la.net",
"from-ma.com",
"from-md.com",
"from-me.org",
"from-mi.com",
"from-mn.com",
"from-mo.com",
"from-ms.com",
"from-mt.com",
"from-nc.com",
"from-nd.com",
"from-ne.com",
"from-nh.com",
"from-nj.com",
"from-nm.com",
"from-nv.com",
"from-ny.net",
"from-oh.com",
"from-ok.com",
"from-or.com",
"from-pa.com",
"from-pr.com",
"from-ri.com",
"from-sc.com",
"from-sd.com",
"from-tn.com",
"from-tx.com",
"from-ut.com",
"from-va.com",
"from-vt.com",
"from-wa.com",
"from-wi.com",
"from-wv.com",
"from-wy.com",
"ftpaccess.cc",
"fuettertdasnetz.de",
"game-host.org",
"game-server.cc",
"getmyip.com",
"gets-it.net",
"go.dyndns.org",
"gotdns.com",
"gotdns.org",
"groks-the.info",
"groks-this.info",
"ham-radio-op.net",
"here-for-more.info",
"hobby-site.com",
"hobby-site.org",
"home.dyndns.org",
"homedns.org",
"homeftp.net",
"homeftp.org",
"homeip.net",
"homelinux.com",
"homelinux.net",
"homelinux.org",
"homeunix.com",
"homeunix.net",
"homeunix.org",
"iamallama.com",
"in-the-band.net",
"is-a-anarchist.com",
"is-a-blogger.com",
"is-a-bookkeeper.com",
"is-a-bruinsfan.org",
"is-a-bulls-fan.com",
"is-a-candidate.org",
"is-a-caterer.com",
"is-a-celticsfan.org",
"is-a-chef.com",
"is-a-chef.net",
"is-a-chef.org",
"is-a-conservative.com",
"is-a-cpa.com",
"is-a-cubicle-slave.com",
"is-a-democrat.com",
"is-a-designer.com",
"is-a-doctor.com",
"is-a-financialadvisor.com",
"is-a-geek.com",
"is-a-geek.net",
"is-a-geek.org",
"is-a-green.com",
"is-a-guru.com",
"is-a-hard-worker.com",
"is-a-hunter.com",
"is-a-knight.org",
"is-a-landscaper.com",
"is-a-lawyer.com",
"is-a-liberal.com",
"is-a-libertarian.com",
"is-a-linux-user.org",
"is-a-llama.com",
"is-a-musician.com",
"is-a-nascarfan.com",
"is-a-nurse.com",
"is-a-painter.com",
"is-a-patsfan.org",
"is-a-personaltrainer.com",
"is-a-photographer.com",
"is-a-player.com",
"is-a-republican.com",
"is-a-rockstar.com",
"is-a-socialist.com",
"is-a-soxfan.org",
"is-a-student.com",
"is-a-teacher.com",
"is-a-techie.com",
"is-a-therapist.com",
"is-an-accountant.com",
"is-an-actor.com",
"is-an-actress.com",
"is-an-anarchist.com",
"is-an-artist.com",
"is-an-engineer.com",
"is-an-entertainer.com",
"is-by.us",
"is-certified.com",
"is-found.org",
"is-gone.com",
"is-into-anime.com",
"is-into-cars.com",
"is-into-cartoons.com",
"is-into-games.com",
"is-leet.com",
"is-lost.org",
"is-not-certified.com",
"is-saved.org",
"is-slick.com",
"is-uberleet.com",
"is-very-bad.org",
"is-very-evil.org",
"is-very-good.org",
"is-very-nice.org",
"is-very-sweet.org",
"is-with-theband.com",
"isa-geek.com",
"isa-geek.net",
"isa-geek.org",
"isa-hockeynut.com",
"issmarterthanyou.com",
"isteingeek.de",
"istmein.de",
"kicks-ass.net",
"kicks-ass.org",
"knowsitall.info",
"land-4-sale.us",
"lebtimnetz.de",
"leitungsen.de",
"likes-pie.com",
"likescandy.com",
"merseine.nu",
"mine.nu",
"misconfused.org",
"mypets.ws",
"myphotos.cc",
"neat-url.com",
"office-on-the.net",
"on-the-web.tv",
"podzone.net",
"podzone.org",
"readmyblog.org",
"saves-the-whales.com",
"scrapper-site.net",
"scrapping.cc",
"selfip.biz",
"selfip.com",
"selfip.info",
"selfip.net",
"selfip.org",
"sells-for-less.com",
"sells-for-u.com",
"sells-it.net",
"sellsyourhome.org",
"servebbs.com",
"servebbs.net",
"servebbs.org",
"serveftp.net",
"serveftp.org",
"servegame.org",
"shacknet.nu",
"simple-url.com",
"space-to-rent.com",
"stuff-4-sale.org",
"stuff-4-sale.us",
"teaches-yoga.com",
"thruhere.net",
"traeumtgerade.de",
"webhop.biz",
"webhop.info",
"webhop.net",
"webhop.org",
"worse-than.tv",
"writesthisblog.com",
  ]

  # add recursivedns.com to the domains
  domains = domains + ["recursivedns.com"]

  if not opt_custom:
    for host in hostnames:
      h = string.lower(host)
      known = 0
      for dom in domains:
        if dom == h[-len(dom):]:
          known = 1 
          break
      if not known:
        logline = "WARNING Unknown domain: " + host
        logger.logexit(logline)
        logger.logexit("If the domain is listed at http://www.dyndns.org/services/dyndns/domains.html")
        logger.logexit("then email kal@users.sourceforge.net to add the domain.")
        logger.logexit("Otherwise, you should be using -c for custom domains.")

  #
  # taint check the mx host
  #
  if opt_mxhost:
    if string.find(opt_mxhost, "NOCHG") != -1:
      opt_mxhost = "NOCHG"
    elif not "." in opt_mxhost:
      logline = "Bad mxhost: " + opt_mxhost
      logger.logexit(logline)
      sys.exit(-1)

  #
  # log the pwd
  #
  if os.environ.has_key("PWD"):
    logger.logit("PWD = " + os.environ["PWD"])

  #
  # create the full path names
  #
  datfile = Datfile("ipcheck.dat")
  if opt_directory:
    datfile.setFilename(opt_directory + datfile.getFilename())
    logger.logit("Datfile = " + datfile.getFilename())
  errfile = Errorfile(logger, "ipcheck.err")
  if opt_directory:
    errfile.setFilename(opt_directory + errfile.getFilename())
    logger.logit("Errfile = " + errfile.getFilename())
  Waitfile = "ipcheck.wait"
  if opt_directory:
    Waitfile = opt_directory + Waitfile
    logger.logit("Waitfile = " + Waitfile)
  Htmlfile = "ipcheck.html"
  if opt_directory:
    Htmlfile = opt_directory + Htmlfile
    logger.logit("Htmlfile = " + Htmlfile)
  Tempfile = "ipcheck.tmp"
  if opt_directory:
    Tempfile = opt_directory + Tempfile
    logger.logit("Tempfile = " + Tempfile)
  

  #
  # determine the local machine's ip
  #
  localip = ""
  iphost = ""
  if opt_address:
    logger.logit("Manually setting localip with -a")
    localip = opt_address
  elif opt_after_syslog:
    logger.logit("Scanning /var/log/messages for last occurance of " + opt_after_syslog)
    fp = open("/var/log/messages", "r")
    ipdata = fp.read()
    fp.close()
    p1 = string.rfind(ipdata, opt_after_syslog)
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata[p1:])
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)
    fp.close()

  elif opt_firewall_log:
    logger.logit("Scanning " + opt_firewall_log)
    lines = []
    fp = open(opt_firewall_log, "r")
    while 1:
      l = fp.readline()
      if not l:
        break
      lines.append(l)
    fp.close()
    lcnt = len(lines)

    localip = ""
    for x in xrange(lcnt-1, 0, -1):
      l = lines[x]
      if l[:3] == "NAT":
        ipmatch = Addressgrep.findall(l)
        if len(l) == 2:
          localip = check_public_ip(l[1])
        else:
          localip = check_public_ip(l[0])
      if localip:
        break

    logger.logit("IP matched " + localip)

  elif opt_snmp_agent_prefix:
    logger.logit("Trying snmp localip detection")

    # Create an instance of snmptable class
    instance = snmptable (opt_snmp_agent, opt_snmp_community)

    # Run snmptable against passed Object ID's 
    retval = []
    try:
      retval = instance.run([opt_snmp_objectid])
    except:
      logline = "Snmp session failed." 
      logger.logexit(logline)
      logger.logexit("Exception: " + `sys.exc_info()[0]`)
      sys.exit(-1)

    agentlen = len(opt_snmp_agent_prefix)
    objectlen = len(opt_snmp_objectid) + 1
    for (objid, value) in retval:
      logger.logit(objid + ' ---> ' + str(value))
      objval = objid[objectlen:]
      if objval[:agentlen] != opt_snmp_agent_prefix:
        localip = objval
        logger.logit("IP matched: " + localip)
        # match the last one so all options are printed in the log
        #break

  elif opt_snmp_agent:
    
    mysnmptable = snmptable(opt_snmp_agent, opt_snmp_community)

    try:
      value = mysnmptable.getrow(opt_snmp_objectid)
    except:
      logger.logexit("Snmp session failed.")
      logger.logexit("Exception: " + `sys.exc_info()[0]`)
      sys.exit(-1)

    logger.logit(opt_snmp_objectid + ' ---> ' + str(value))
    localip = value
    logger.logit("IP from snmpget is: " + localip)
    

  elif opt_Cayman_password:
    #
    # Cayman DSL 3220H router ip detection
    #
    #   This code was written for and tested on Device Firmware
    #   GatorSurf version 5.6.2 (build R0)
    #   with PPP / NAT
    
    #
    # determine the router host address
    #
    if routerIP:
      logger.logit("Cayman_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.254")
      iphost = "192.168.1.254"

    # connect to the router's admin console interface
    try:
      logger.logit("Trying Cayman DSL 3220H")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("ogin:")
      logger.logit("Login prompt found")
      tn.write(Cayman_user + "\r\n")
      logger.logit("Cayman_user sent")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_Cayman_password + "\r\n")
      logger.logit("opt_Cayman_password sent")
      tn.read_until(">")
      tn.write("show ip interface\r\n")
      logger.logit("show ip interface command sent")
      ipdata = tn.read_until(">", 2000)
      tn.write("exit\r\n")
      logger.logit("exit command sent")
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "cayman.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("cayman.out file created")

    # look for the WAN device in ipdata
    p1 = string.rfind(ipdata, "PPP")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1+1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)
      
  elif opt_Netgear338_password:
    #
    # Netgear RT338 ISDN router
    #
    # determine the router host address
    #
    if routerIP:
      logger.logit("Netgear338_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Netgear RT338")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_Netgear338_password + "\r\n")
      logger.logit("opt_Netgear338_password sent")
      tn.read_until("Number:")
      tn.write("24\r\n")
      logger.logit("menu number 24 sent")
      tn.read_until("Number:")
      tn.write("8\r\n")
      logger.logit("menu number 8 sent")
      ip1 = tn.read_until("router>", 2000)
      tn.write("ip ifconfig\r\n")
      logger.logit("ip ifconfig sent")
      ipdata = tn.read_until("router>", 2000)
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "netgear338.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("netgear338.out file created")

    # look for the last wanif0 device in the log
    p1 = string.rfind(ipdata, "wanif0")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)
    else:
      p1 = string.rfind(ipdata, "enif1")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)
  


  elif opt_Gnet_password:
    #
    # Gnet ADSL Router
    #
    #   This code was written for and tested on
    #   Gnet model BB0040 ADSL Router version 2.A3.2.03 (Build 011207.A)
    #   running ADSL/PPPOE/NAT in the device
    #
    # determine the router host address
    #
    if routerIP:
      logger.logit("Gnet_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.254")
      iphost = "192.168.1.254"

    # connect to the router's admin console interface
    try:
      logger.logit("Trying Gnet model BB0040 ADSL router")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_Gnet_password + "\r\n")
      logger.logit("opt_Gnet_password sent")
      tn.read_until(">")
      tn.write("ip subnet\r\n")
      logger.logit("ip subnet command sent")
      ipdata = tn.read_until(">", 2000)
      tn.write("@close\r\n")
      logger.logit("@close command sent")
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "gnet.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("gnet.out file created")

    # look for the WAN device in ipdata
    p1 = string.rfind(ipdata, "subnet ppp_device")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1+1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)
      

  elif opt_Compex_password:
    #
    # Compex NetPassage 15 router ip detection
    #
    #   This code was written for and tested on Device Firmware
    #   version "2.67 Build 1005, Mar 5 2001"
    
    #
    # determine the router host address
    #
    if routerIP:
      logger.logit("Compex_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.168.1")
      iphost = "192.168.168.1"

    # connect to the router's admin console interface
    try:
      logger.logit("Trying Compex NetPassage 15")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_Compex_password + "\r\n")
      logger.logit("opt_Compex_password sent")
      tn.read_until("ommand>")
      tn.write("show ip\r\n")
      logger.logit("show ip command sent")
      ipdata = tn.read_until("ommand>", 2000)
      tn.write("exit\r\n")
      logger.logit("exit command sent")
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "compex.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("compex.out file created")

    # look for the WAN device in ipdata
    p1 = string.rfind(ipdata, "WAN")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)
      
  elif opt_Zyxel_ME_password:
    # 
    # ZyXEL Prestige 642ME router ip detection
    # 

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Zyxel_ME_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying ZyXEL Prestige 642ME")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_Zyxel_ME_password + "\r\n")
      logger.logit("opt_Zyxel_ME_password sent")
      tn.read_until(">")
      tn.write("ip ifconfig\r\n")
      logger.logit("ip ifconfig sent")
      ipdata = tn.read_until(">", 2000)
      logger.logit("ipdata read")
      tn.write("exit\r\n")
      logger.logit("exit sent")
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "zyxelme.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("zyxelme.out file created")

    # look for the last wanif0 device in the log
    p1 = string.rfind(ipdata, "wanif0")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)
    else:
      p1 = string.rfind(ipdata, "enif1")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)
  
  elif opt_Zyxel_password:
    # 
    # ZyXEL 642R router ip detection
    # 

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Zyxel_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    ipdata = ""
    ip1 = ""
    ip2 = ""
    # connect to the router's admin webpage
    try:
      logger.logit("Trying ZyXEL Prestige 642R and 310")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_Zyxel_password + "\r\n")
      logger.logit("opt_Zyxel_password sent")
      #tn.read_until("Menu Selection Number:")
      tn.write("24\r\n")
      logger.logit("menu number 24 sent")
      #tn.read_until("Menu Selection Number:")
      tn.write("8\r\n")
      logger.logit("menu number 8 sent")
      tn.write("ip ifconfig\r\n")
      logger.logit("ip ifconfig sent")
      ip1 = tn.read_until(">", 2000)
      ip2 = tn.read_until(">", 2000)
      logger.logit("ip1 and ip2 read")
      tn.write("exit\r\n")
      logger.logit("exit sent")
      tn.write("99\r\n")
      logger.logit("menu number 99 sent")
    except:
      logger.logit("may not have gotten second prompt")
      tn.write("exit\r\n")
      logger.logit("exit sent")
      tn.write("99\r\n")
      logger.logit("menu number 99 sent")

    ipdata = ip1 + ip2

    # create an output file of the response
    filename = "zyxel.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("zyxel.out file created")

    # look for the last wanif0 device in the log
    p1 = string.rfind(ipdata, "wanif0")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)
    else:
      p1 = string.rfind(ipdata, "enif1")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)
  
  elif opt_NetgearWTG624_password:
    if routerIP:
      logger.logit("NetgearWTG624_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"

    logger.logit("Trying NetgearWTG624")

    logger.logit("Authenticating with home page")
    filename = "netgearWTG624p1.out"
    if opt_directory:
      filename = opt_directory + filename
    logindata = BasicAuth(logger, iphost, NetgearWTG624_page1, Netgear_user, opt_NetgearWTG624_password, filename)

    logger.logit("Getting status page")
    filename = "netgearWTG624p2.out"
    if opt_directory:
      filename = opt_directory + filename
    ipdata = BasicAuth(logger, iphost, NetgearWTG624_page2, Netgear_user, opt_NetgearWTG624_password, filename)

    p1 = string.find(ipdata, "IP")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

    logger.logit("Logging out")
    filename = "netgearWTG624p3.out"
    if opt_directory:
      filename = opt_directory + filename
    logoutdata = BasicAuth(logger, iphost, NetgearWTG624_page3, Netgear_user, opt_NetgearWTG624_password, filename)

  elif opt_Netgear3114_password:
    if routerIP:
      logger.logit("Netgear3114_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.100.1")
      iphost = "192.168.100.1"

    logger.logit("Trying Netgear3114")

    logger.logit("Authenticating with home page")
    filename = "netgear3114p1.out"
    if opt_directory:
      filename = opt_directory + filename
    logindata = BasicAuth(logger, iphost, Netgear3114_page1, Netgear3114_user, opt_Netgear3114_password, filename)

    logger.logit("Getting status page")
    filename = "netgear3114p2.out"
    if opt_directory:
      filename = opt_directory + filename
    ipdata = BasicAuth(logger, iphost, Netgear3114_page2, Netgear3114_user, opt_Netgear3114_password, filename)

    p1 = string.find(ipdata, "IP")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

    logger.logit("Logging out")
    filename = "netgear3114p3.out"
    if opt_directory:
      filename = opt_directory + filename
    logoutdata = BasicAuth(logger, iphost, Netgear3114_page3, Netgear3114_user, opt_Netgear3114_password, filename)

  elif opt_Hawking_password:
    # 
    # Hawking router ip detection
    # 
    ipdir = Hawking_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Hawking_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.10.10")
      iphost = "192.168.10.10"

    logger.logit("Trying HawkingTech")
    filename = "hawking.out"
    if opt_directory:
      filename = opt_directory + filename
    ipdata = BasicAuth(logger, iphost, ipdir, Hawking_user, opt_Hawking_password, filename)

    # look for local ip in the log
    p1 = string.find(ipdata, "WAN")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_Ugate_router:
    # 
    # UgatePlus router ip detection
    # 
    ipdir = Ugate_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Ugate_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying UgatePlus")
      ipurl = "http://" + iphost + Ugate_page
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "ugate.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("ugate.out file created")

    # look for the last Default gateway 
    p1 = string.rfind(ipdata, "I.P. Address")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_Veicon_password:
    # 
    # Eicon Diva 2430 SE ADSL Modem with password
    # 
    ipdir = Veicon_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Veicon_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Eicon with password")
      params = urllib.urlencode({'password': opt_Veicon_password})
      ipurl = "http://" + iphost + Veicon_page
      urlfp = urllib.urlopen(ipurl, params)
      ipdata = urlfp.read()
      urlfp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "veicon.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("veicon.out file created")

    # look for the last Default gateway 
    p1 = string.rfind(ipdata, "WAN IP address")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_Barricade_password:
    # 
    # Newer SMC Barricade with passwords on port 88
    # 
    ipdir = Barricade_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Barricade_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.2.1")
      iphost = "192.168.2.1"

    logger.logit("Trying new Barricade with password")

    if opt_7004VWBR:
      ipport = "80"
      loginaction = "/cgi-bin/login.exe"
      logoutaction = "/cgi-bin/logout.exe"
      statuspage = "/status_main.stm"
      ipprefix = "var wan_ip="
    else:
      ipport = "88"
      loginaction = "/login.htm"
      logoutaction = "/logout.htm"
      statuspage = "/status.HTM"
      ipprefix = "WAN IP"

    try:
      ipurl = "http://" + iphost + ":" + ipport + "/login.htm"
      logger.logit("urlopen " + ipurl)
      urlfp = urllib.urlopen(ipurl)
      logger.logit("urlfp.read")
      ipdata = urlfp.read()
      logger.logit("urlfp.close")
      urlfp.close()
      logger.logit("filename = login.out")
      filename = "login.out"
      if opt_directory:
        filename = opt_directory + filename
      logger.logit("file open")
      fp = open(filename, "w")
      logger.logit("write data")
      fp.write(ipdata)
      logger.logit("file close")
      fp.close()
      logger.logit("login.out file created")
    except:
      logline = "Failed to get login form"
      logger.logexit(logline)
      sys.exit(-1)

    try:
      logger.logit("Try to post to form")
      params = urllib.urlencode({'pws': opt_Barricade_password})
      ipurl = "http://" + iphost + ":" + ipport + loginaction
      logger.logit("urlopen " + ipurl)
      urlfp = urllib.urlopen(ipurl, params)
      logger.logit("urlfp.read")
      ipdata = urlfp.read()
      logger.logit("urlfp.close")
      urlfp.close()
      if string.find(ipdata, "not found") != -1 or string.find(ipdata, "<html><head><meta http-equiv=refresh content='0; url=index.htm'></head></html>") == -1:
          logger.logit("Trying to with page=login&")
          urlfp = urllib.urlopen(ipurl, "page=login&" + params)
          logger.logit("urlfp.read")
          ipdata = urlfp.read()
          logger.logit("urlfp.close")
          urlfp.close()

      filename = "post.out"
      if opt_directory:
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("post.out file created")
    except:
      logline = "Failed to post password to login form"
      logger.logexit(logline)
      sys.exit(-1)

    try:
      logger.logit("Now try to access " + statuspage + " on port " + ipport)
      ipurl = "http://" + iphost + ":" + ipport + statuspage
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()

      filename = "barricade.out"
      if opt_directory:
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("barricade.out file created")
    except:
      logline = "Failed accessing status page "
      logger.logexit(logline)
      sys.exit(-1)

    # look for the last Default gateway 
    p1 = string.rfind(ipdata, ipprefix)
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

    # logout so other users can login to the Barricade
    try:
      logger.logit("Try to post to logout form")
      ipurl = "http://" + iphost + ":" + ipport + logoutaction
      logger.logit("urlopen " + ipurl)
      urlfp = urllib.urlopen(ipurl)
      logger.logit("urlfp.read")
      ipdata = urlfp.read()
      logger.logit("urlfp.close")
      urlfp.close()

      filename = "logout.out"
      if opt_directory:
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("logout.out file created")
    except:
      logline = "Failed to post to logout form"
      logger.logexit(logline)
      sys.exit(-1)
 
  elif opt_Siemens2620_password:
    # 
    # Siemens SpeedStream 2620 with passwords on port 88
    # (This is just like the SMC Barricade entry just above, save that
    # some of the URLs are slightly different. Is the Siemens unit just
    # a rebadged SMC or vice-versa?)
    # 
    ipdir = Siemens2620_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Siemens2620_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.254.254")
      iphost = "192.168.254.254"

    logger.logit("Trying Siemens SpeedStream 2620 with password")

    try:
      ipurl = "http://" + iphost + ":88/"
      logger.logit("urlopen " + ipurl)
      urlfp = urllib.urlopen(ipurl)
      logger.logit("urlfp.read")
      ipdata = urlfp.read()
      logger.logit("urlfp.close")
      urlfp.close()
      logger.logit("filename = login.out")
      filename = "login.out"
      if opt_directory:
        filename = opt_directory + filename
      logger.logit("file open")
      fp = open(filename, "w")
      logger.logit("write data")
      fp.write(ipdata)
      logger.logit("file close")
      fp.close()
      logger.logit("login.out file created")
    except:
      logline = "Failed to get login form"
      logger.logexit(logline)
      sys.exit(-1)

    try:
      logger.logit("Try to post to form")
      params = urllib.urlencode({'pws': opt_Siemens2620_password})
      ipurl = "http://" + iphost + ":88/LOGIN.HTM"
      logger.logit("urlopen " + ipurl)
      urlfp = urllib.urlopen(ipurl, params)
      logger.logit("urlfp.read")
      ipdata = urlfp.read()
      logger.logit("urlfp.close")
      urlfp.close()
      if string.find(ipdata, "not found") != -1:
          logger.logit("Trying to with page=login&")
          params = urllib.urlencode({'pws': opt_Siemens2620_password})
          ipurl = "http://" + iphost + ":88/LOGIN.HTM"
          logger.logit("urlopen " + ipurl)
          urlfp = urllib.urlopen(ipurl, "page=login&" + params)
          logger.logit("urlfp.read")
          ipdata = urlfp.read()
          logger.logit("urlfp.close")
          urlfp.close()

      filename = "post.out"
      if opt_directory:
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("post.out file created")
    except:
      logline = "Failed to post password to login form"
      logger.logexit(logline)
      sys.exit(-1)

    try:
      logger.logit("Now try to access status.HTM on port 88")
      ipurl = "http://" + iphost + ":88/MAIN.HTM"
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()

      filename = "siemens.out"
      if opt_directory:
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("siemens.out file created")
    except:
      logline = "Failed accessing status page "
      logger.logexit(logline)
      sys.exit(-1)

    # look for the last Default gateway 
    p1 = string.rfind(ipdata, "WAN IP")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

        
  elif opt_Eicon_router:
    # 
    # Eicon Diva 2430 SE ADSL Modem ip detection
    # 
    ipdir = Eicon_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Eicon_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Eicon")
      ipurl = "http://" + iphost + Eicon_page
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "eicon.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("eicon.out file created")

    # look for the last Default gateway 
    p1 = string.rfind(ipdata, "WAN IP address")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

        
  elif opt_II_password:
    # 
    # Instant Internet router ip detection
    # 

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("II_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Instant Internet ")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_II_password + "\r\n")
      logger.logit("opt_II_password sent")
      tn.write("ppp " + opt_II_interface + "\r\n")
      logger.logit("ppp " + opt_II_interface + " sent")
      ip1 = tn.read_until("state:", 2000)
      logger.logit("ip read")
      tn.write("exit\r\n")
      logger.logit("exit sent")
      ipdata = ip1
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)


    # create an output file of the response
    filename = "II.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("II.out file created")

    # look for the last ipadr device in the log
    p1 = string.rfind(ipdata, "ipadr local:")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)


  elif opt_Nexland_router:
    # 
    # Nexland router ip detection
    # 
    ipdir = Nexland_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Nexland_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Nexland")
      ipurl = "http://" + iphost + Nexland_page
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "nexland.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("nexland.out file created")

    # look for the last Default gateway 
    p1 = string.rfind(ipdata, "Default gateway")
    if p1 == -1:
      p1 = string.find(ipdata, "IP Address<")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_Pro800Turbo_router:
    # 
    # Nexland Pro800Turbo router ip detection
    # 
    ipdir = Pro800Turbo_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Pro800Turbo_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Pro800Turbo")
      h1 = httplib.HTTP(iphost)
      h1.putrequest('GET',Pro800Turbo_page)
      if Pro800Turbo_password:
        authstring = base64.encodestring("admin:" + Pro800Turbo_password)
        h1.putheader('Authorization', 'Basic ' + authstring)
      # print ipdir
      h1.endheaders()
      errcode, errmsg, headers = h1.getreply()
      # print errcode
      # print errmsg
      fp = h1.getfile()
      ipdata = fp.read()
      fp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "pro800turbo.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("pro800turbo.out file created")

    p1 = 0
    local_ips = []
    connected = []
    while 1:
      p2 = string.find(ipdata[p1:], ">Connection Status<")
      if p2 == -1:
        break
      p1 = p1 + p2 + 1
      cmatch = re.search(">([^>]+)</td>",ipdata[p1:])
      if cmatch == None:
        break
      connected.append(cmatch.group(1))
      p2 = string.find(ipdata[p1:], "IP Address<")
      if p2 == -1:
        break
      p1 = p1 + p2
      if p1 == -1:
        break
      ipmatch = Addressgrep.search(ipdata, p1)
      p1 = p1 + len("IP Address<")
      if ipmatch == None:
        local_ips.append(None)
      else:
        local_ips.append(ipmatch.group())

    if Pro800Turbo_port == 'force':
      if local_ips[Pro800Turbo_port_number] != '0.0.0.0':
        # if forced, don't even check connection.  We might as well use
        # the IP we get, even it it isn't currently working.
        localip = local_ips[Pro800Turbo_port_number]
    else:
      if     local_ips[Pro800Turbo_port_number] != '0.0.0.0' \
         and connected[Pro800Turbo_port_number] == 'Connected':
        localip = local_ips[Pro800Turbo_port_number]
      else:
        for i in range(len(local_ips)):
          if local_ips[i] != '0.0.0.0':
            localip = local_ips[i]
            if connected[i] == 'Connected':
              break
            # Else keep looking for one that is "Connected".  If we don't find
            # one, might as well use the an ip address, even if not
            # "Connected".  I've had situations where that was still usable.
    if localip:
      logger.logit("IP matched: " + localip)

  elif opt_SMC_router:
    # 
    # SMC barricade router ip detection
    # 
    ipdir = SMC_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("SMC_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.254")
      iphost = "192.168.0.254"

    # connect to the router's admin webpage
    try:
      if opt_WBR != "":
        logger.logit("Trying SMC WBR with password")
        if opt_7004VWBR:
          # 2005-02-15 djlauk@users.sourceforge.net:
          # quick hack for SMC7004VWBRV.2
          logger.logit("Trying DJ's hack for model SMC7004VWBRV.2")
          SMC_page = "/login.htm?pws=" + opt_WBR
        else:
          SMC_page = "/login.cgi?pws=" + opt_WBR
        ipurl = "http://" + iphost + SMC_page
        urlfp = urllib.urlopen(ipurl)
        ipdata = urlfp.read()
        urlfp.close()
        SMC_page = "/status_main.htm" 
        ipurl = "http://" + iphost + SMC_page
        urlfp = urllib.urlopen(ipurl)
        ipdata = urlfp.read()
        urlfp.close()
      else:
        logger.logit("Trying SMC")
        ipurl = "http://" + iphost + SMC_page
        urlfp = urllib.urlopen(ipurl)
        ipdata = urlfp.read()
        urlfp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "smc.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("smc.out file created")

    # grab first thing that looks like an IP address
    ipmatch = Addressgrep.search(ipdata)
    if ipmatch != None:
      localip = ipmatch.group()
      logger.logit("IP matched: " + localip)

  elif opt_Netvanta_password != "":
    #
    # Adtran Netvanta router ip detection
    #
    #
    # determine the router host address
    #
    iphost = ""
    if routerIP:
      logger.logit("Netvanta_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost == "":
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"
    else:
      logline = "Trying router at " + iphost
      logger.logit(logline)

    # connect to the router's telnet interface
    # first try to talk to a Netvanta Series router
    try:
      logger.logit("Trying Netvanta router (AOS!)")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_Netvanta_password + "\r\n")
      logger.logit("Netvanta password sent")
      tn.write("enable\r\n")
      tn.read_until("assword:")
      logger.logit("enable Password prompt found")
      tn.write(opt_Netvanta_password + "\r\n")
      logger.logit("Netvanta password sent")
      tn.write("show interface ethernet 0/1\r\n")
      logger.logit("show interface command sent")
      ipdata = tn.read_until(", netmask", 1000)
      ipdata = string.replace(ipdata, ", netmask", "")
      logger.logit("ipdata read")
      tn.write("logo\r\n")
      logger.logit("logoff sent")
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "netvanta.out"
    if opt_directory != "":
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("netvanta.out file created")

    # look for the last (rfind) negotiated IP in the log
    p1 = string.rfind(ipdata, "Internet address is ")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_Cisco_password != "":
    #
    # Cisco router ip detection
    #
    #
    # determine the router host address
    #
    iphost = ""
    if routerIP:
      logger.logit("Cisco_host set explicitly.")
      iphost = Cisco_host
    else:
      iphost = DefaultRoute(logger, Tempfile)
    iphost = DefaultRoute(logger, Tempfile)

    if iphost == "":
      logger.logit("No router ip detected.  Assuming 192.168.10.5")
      iphost = "192.168.10.5"
    else:
      logline = "Trying router at " + iphost
      logger.logit(logline)

    # connect to the router's admin webpage
    # first try to talk to a Cisco 800-series
    try:
      logger.logit("Trying Cisco DSL 800 series (IOS!)")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_Cisco_password + "\r\n")
      logger.logit("Cisco password sent")
      tn.write("show ip interface | incl /32\r\n")
      logger.logit("show ip interface command sent")
      ipdata = tn.read_until("/32", 1000)
      logger.logit("unwanted stuff read")
      ipdata = tn.read_until("/32", 1000)
      ipdata = string.replace(ipdata, "/32", "")
      logger.logit("ipdata read")
      tn.write("logo\r\n")
      logger.logit("logoff sent")
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "cisco.out"
    if opt_directory != "":
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("cisco.out file created")

    # look for the last (rfind) negotiated IP in the log
    p1 = string.rfind(ipdata, "Internet address is ")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)


  elif opt_ISDNCisco_password:
    # 
    # ISDNCisco router ip detection
    # 

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("ISDNCisco_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.10.5")
      iphost = "192.168.10.5"

    # connect to the router's admin webpage
    # first try to talk to a Cisco 667i
    try:
      logger.logit("Trying Cisco ISDN 700 series")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword:")
      logger.logit("Password prompt found")
      tn.write(opt_ISDNCisco_password + "\r\n")
      logger.logit("opt_ISDNCisco_password sent")
      tn.write("show ip co\r\n")
      logger.logit("show ip co sent")
      ipdata = tn.read_until("Profile     PAT", 1000)
      logger.logit("ipdata read")
      tn.write("bye\r\n")
      logger.logit("bye sent")
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "cisco.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("cisco.out file created")

    # look for the last negotiated IP in the log
    # you may have to change this to a user defined profile
    p1 = string.rfind(ipdata, "RemoteNet") 
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_Netopia_password:
    # 
    # Netopia router ip detection
    # 
    ipdir = Netopia_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Netopia_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"

    logger.logit("Trying Netopia")
    filename = "netopia.out"
    if opt_directory:
      filename = opt_directory + filename
    ipdata = BasicAuth(logger, iphost, Netopia_page, Netopia_user, opt_Netopia_password, filename)

    # look for local ip in the log
    p1 = string.find(ipdata, "local")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_Draytek_password:
    # 
    # Draytek router ip detection
    # 
    ipdir = Draytek_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Draytek_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    logger.logit("Trying Draytek")
    filename = "draytek.out"
    if opt_directory:
      filename = opt_directory + filename
    ipdata = BasicAuth(logger, iphost, Draytek_page, Draytek_user, opt_Draytek_password, filename)

    # grab first thing that looks like an IP address
    ipmatch = Addressgrep.search(ipdata)
    if ipmatch != None:
      localip = ipmatch.group()
      logger.logit("IP matched: " + localip)

  elif opt_MotorolaVT1000v_router:
    # 
    # Motorola VT1000v router ip detection
    # 
    ipdir = MotorolaVT1000v_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("MotorolaVT1000v_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Motorola VT1000v")
      ipurl = "http://" + iphost + MotorolaVT1000v_page
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "motorolaVT1000v.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
  elif opt_Belkin_f5d7230_router:

    if routerIP:
      logger.logit("Belkin_f5d7230 router ip set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    ipdir = Belkin_f5d7230_page
    try:
      logger.logit("Trying Belkin f5d7230")
      ipurl = "http://" + iphost + ipdir
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "belkin_f5d7230.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("%s file created" % filename)

    p1 = string.find(ipdata, "wan_conn.html")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)


    fp.close()
    logger.logit("%s file created" % filename)

    # look for the last Default gateway 
    ipre = re.compile ('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    routerip = ipre.findall(ipdata)
    if len(routerip) > 0:
      localip = routerip[0]
      logger.logit("IP matched: " + localip)
    
  elif opt_Macsense_password:
    # 
    # MacSense router ip detection
    # 
    ipdir = Macsense_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Macsense_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying MacSense XRouter Pro router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying MacSense")
      h1 = httplib.HTTP(iphost)

      authstring = base64.encodestring(Macsense_user + ":" + opt_Macsense_password)
      authstring = string.replace(authstring, "\012", "")
      ipdir = Macsense_page + ' \r\n' \
        + 'Authorization: Basic ' \
        + authstring + '\r\n'
      h1.putrequest('GET', ipdir)
      h1.endheaders()

      errcode, errmsg, headers = h1.getreply()
      fp = h1.getfile()
      ipdata = fp.read()
      fp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the linksys response
    filename = "macsense.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("macsense.out file created")

    p1 = string.find(ipdata, "Public IP")
    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_Netgear_password:
    # 
    # Netgear router ip detection
    # 
    ipdir = Netgear_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("Netgear_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"

    logger.logit("Trying Netgear")
    filename = "netgear.out"
    if opt_directory:
      filename = opt_directory + filename
    ipdata = BasicAuth(logger, iphost, Netgear_page, Netgear_user, opt_Netgear_password, filename)

    # look for the last WAN Port in the log
    p1 = string.rfind(ipdata, "WAN")
    if p1 == -1:
      ipdata = BasicAuth(logger, iphost, Netgear314_page1, Netgear_user, opt_Netgear_password, filename)
      p1 = string.rfind(ipdata, "WAN")
    if p1 == -1:
      ipdata = BasicAuth(logger, iphost, Netgear314_page2, Netgear_user, opt_Netgear_password, filename)
      p1 = string.rfind(ipdata, "WAN")
    # Gene Cumm--Netgear FVS318	//GRC
    if p1 == -1:
      ipdata = BasicAuth(logger, iphost, NetgearFVS318_page, Netgear_user, opt_Netgear_password, filename)
      p1 = string.rfind(ipdata, "WAN Port")

    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

        logger.logit("Logging out on Netgear")
        # hit the logout page
        filename = "logout.out"
        if opt_directory:
          filename = opt_directory + filename
        ipdata = BasicAuth(logger, iphost, Netgear_logout, Netgear_user, opt_Netgear_password, filename)

  elif opt_DInop_router == 1:
    # 
    # DI704 router ip detection
    # 
    ipdir = DI704_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("DI704_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"

    logger.logit("Trying DI704 no password")

    try:
      logger.logit("Retrieving menu.htm...")
      ipurl = "http://" + iphost + "/menu.htm?RC=@"
      urlfp = urllib.urlopen(ipurl)
      menudata = urlfp.read()
      urlfp.close()

      filename = "di704_menu.out"
      if opt_directory != "":
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(menudata)
      fp.close()
      logger.logit("di704menu.out file created")
    except:
      logline = "Failed while fetching menu.htm page "
      logger.logexit(logline)
      sys.exit(-1)
 
    logline = "Parsing menu... "
    logger.logit("Parsing menu")
    menud = {}
    p1 = 0;
    p2 = 0;
    while 1:
      p1 = string.find(menudata, "VALUE=", p2)
      p2 = string.find(menudata, "NAME=", p1)
      if p1 == -1 or p2 == -1:
          break
      p3 = string.find(menudata, '"', p1)
      p4 = string.find(menudata, '"', p3 + 1)
      p5 = string.find(menudata, '>', p2)
      if p3 == -1 or p4 == -1 or p5 == -1:
          break
      
      rhs = menudata[p3+1:p4] 
      lhs = menudata[p2+6:p5]

      logline = lhs + " = " + rhs
      logger.logit(logline)
      menud[lhs] = rhs

    logger.logit("Adding password")
    menud["URL"] = opt_DI704_password

    try:
      logger.logit("Now try to access status.htm now")
      ipurl = "http://" + iphost + "/status.htm"
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()

      filename = "di704.out"
      if opt_directory:
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("di704.out file created")
    except:
      logline = "Failed accessing status page "
      logger.logexit(logline)
      sys.exit(-1)

    # look for the first WAN Port in the log
    p1 = string.find(ipdata, "WAN")

    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_DI704_password:
    # 
    # DI704 router ip detection
    # 
    ipdir = DI704_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("DI704_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"

    logger.logit("Trying DI704")

    try:
      logger.logit("Retrieving menu.htm...")
      ipurl = "http://" + iphost + "/menu.htm?RC=@"
      urlfp = urllib.urlopen(ipurl)
      menudata = urlfp.read()
      urlfp.close()

      filename = "di704_menu.out"
      if opt_directory != "":
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(menudata)
      fp.close()
      logger.logit("di704menu.out file created")
    except:
      logline = "Failed while fetching menu.htm page "
      logger.logexit(logline)
      sys.exit(-1)
 
    logline = "Parsing menu... "
    logger.logit("Parsing menu")
    menud = {}
    p1 = 0;
    p2 = 0;
    while 1:
      p1 = string.find(menudata, "VALUE=", p2)
      p2 = string.find(menudata, "NAME=", p1)
      if p1 == -1 or p2 == -1:
          break
      p3 = string.find(menudata, '"', p1)
      p4 = string.find(menudata, '"', p3 + 1)
      p5 = string.find(menudata, '>', p2)
      if p3 == -1 or p4 == -1 or p5 == -1:
          break
      
      rhs = menudata[p3+1:p4] 
      lhs = menudata[p2+6:p5]

      logline = lhs + " = " + rhs
      logger.logit(logline)
      menud[lhs] = rhs

    logger.logit("Adding password")
    menud["URL"] = opt_DI704_password

    try:
      logger.logit("Try to post to form")
      params = urllib.urlencode( menud )
      ipurl = "http://" + iphost + "/cgi-bin/logi"
      logger.logit("urlopen " + ipurl)
      urlfp = urllib.urlopen(ipurl, params)
      logger.logit("urlfp.read")
      ipdata = urlfp.read()
      logger.logit("urlfp.close")
      urlfp.close()
      filename = "post.out"
      if opt_directory:
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("post.out file created")
    except:
      logline = "Failed to post password to login form"
      logger.logexit(logline)
      sys.exit(-1)

    try:
      logger.logit("Now try to access status.htm now")
      ipurl = "http://" + iphost + "/status.htm"
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()

      filename = "di704.out"
      if opt_directory:
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("di704.out file created")
    except:
      logline = "Failed accessing status page "
      logger.logexit(logline)
      sys.exit(-1)

    # look for the first WAN Port in the log
    p1 = string.find(ipdata, "IP Address")

    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)

  elif opt_DI713P_password != "":
    #
    # DI713P router ip detection
    #
    # Tested with DI713P firmware 2.57 build 3a1
    # Based on DI704 code. The router appears to expect certain 
    # values for the hidden variables {PSWD, KEY, htm} on the login page.
    # So we first get the values from the login page (menu.htm) then
    # feed them back via the POST 
    
    ipdir = DI713P_page

    #
    # determine the router host address
    #
    if routerIP:
      logger.logit("DI713P_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost == "":
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"
    else:
      logline = "Trying router at " + iphost
      logger.logit(logline)

    logger.logit("Trying DI713P")

    # fetch the menu page and retrieve the hidden values
    try:
      logger.logit("Retrieving menu.htm...")
      ipurl = "http://" + iphost + "/menu.htm"
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()

      filename = "di713P_menu.out"
      if opt_directory != "":
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("di713P_menu.out file created")
    except:
      logline = "Failed while fetching menu.htm page "
      logger.logexit(logline)
      sys.exit(-1)
 
    # match for values of KEY, PSWD, htm
    di713P_logged_in = False  # default
    try:
      search_result = re.search('(")([^"]*)(") NAME=KEY', ipdata)
      if search_result == None: # If KEY not present then we are
        # already logged in. Don't do further string searching
        di713P_logged_in = True
      else:
        di713P_key = search_result.group(2)
        # logger.logit("KEY = " + di713P_key)
        search_result = re.search('(")([^"]*)(") NAME=PSWD', ipdata)
        di713P_pswd = search_result.group(2)
        # logger.logit("PSWD = " + di713P_pswd)
        search_result = re.search('(")([^"]*)(") NAME=htm', ipdata)
        di713P_htm = search_result.group(2)
        # logger.logit("htm = " + di713P_htm)
    except:
      logline = "Failed while matching for KEY, PSWD, htm page "
      logger.logexit(logline)
      sys.exit(-1)

    if di713P_logged_in:
      logger.logit("Already logged in to the DLink gateway")
    else:
      try:
        logger.logit("POSTing to login form")
        # params = urllib.urlencode({'RC': '@D', 'ACCT': "root", 'PSWD': di713P_pswd, 'URL': opt_DI713P_password, 'KEY': di713P_key, 'htm': di713P_htm })
     
        # The device seems to want the POST parameters in a specific
        # order. Unfortunately the order in the urlencode statement is
        # NOT carried through to the data packet (despite documentation to
        # the contrary. Sigh.) So we build up the data string a piece
        # at a time...
        params = urllib.urlencode({'RC':'@D'})
        params = params + "&" + urllib.urlencode({'ACCT':"root"})
        params = params + "&" + urllib.urlencode({'PSWD':di713P_pswd})
        params = params + "&" + urllib.urlencode({'URL':opt_DI713P_password})
        params = params + "&" + urllib.urlencode({'KEY':di713P_key})
        params = params + "&" + urllib.urlencode({'htm': di713P_htm})

        ipurl = "http://" + iphost + "/cgi-bin/logi"
        # logger.logit("urlopen " + ipurl + " ["+params+"]")
        urlfp = urllib.urlopen(ipurl, params)
        logger.logit("urlfp.read")
        ipdata = urlfp.read()
        logger.logit("urlfp.close")
        urlfp.close()
        filename = "di713P_post.out"
        if opt_directory != "":
          filename = opt_directory + filename
        fp = open(filename, "w")
        fp.write(ipdata)
        fp.close()
        logger.logit("di713P_post.out file created")
      except:
        logline = "Failed to post password to login form"
        logger.logexit(logline)
        sys.exit(-1)

    try:
      logger.logit("Fetching status.htm...")
      ipurl = "http://" + iphost + "/status.htm"
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()

      filename = "di713P_status.out"
      if opt_directory != "":
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("di713P_status.out file created")
    except:
      logline = "Failed to get status page "
      logger.logexit(logline)
      sys.exit(-1)

    # look for the first WAN Port in the log
    p1 = string.find(ipdata, "IP Address")

    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("Success! Found IP address " + localip)

  elif opt_DI804_password:
    # 
    # DI804/DI-614+ router ip detection
    # 
    ipdir = DI804_page

    #
    # determine the router host address
    # 
    if routerIP:
      logger.logit("DI804_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    logger.logit("Trying DI804/DI-614+")
    filename = "di804.out"
    if opt_directory:
      filename = opt_directory + filename
    ipdata = BasicAuth(logger, iphost, DI804_page, DI804_user, opt_DI804_password, filename)

    # look for the first WAN Port in the log
    p1 = string.find(ipdata, "Current IP")

    if p1 != -1:
      ipmatch = Addressgrep.search(ipdata, p1)
      if ipmatch != None:
        localip = ipmatch.group()
        logger.logit("IP matched: " + localip)
    else:
      logger.logit("Trying DI614+")
      filename = "di614.out"
      if opt_directory:
        filename = opt_directory + filename
      ipdata = BasicAuth(logger, iphost, DI614_page, DI804_user, opt_DI804_password, filename)
      p1 = string.find(ipdata, "PPPoE")
      if p1 == -1:
        p1 = string.find(ipdata, "WAN")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

  elif opt_DSL504_password:
    #
    # DSL504 router ip detection
    #
    ipdir = DSL504_page

    #
    # determine the router host address
    #
    if routerIP:
      logger.logit("DSL504_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.0.1")
      iphost = "192.168.0.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying DLink DSL504")
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword: ")
      #logger.logit("Password prompt found")
      tn.write(opt_DSL504_password + "\r")
      logger.logit("opt_DSL504_password sent")
      tn.read_until(">")
      tn.write("home\r\n")
      logger.logit("home command sent sent")
      tn.read_until(">")
      tn.write("nat interfaces\r\n")
      logger.logit("nat interfaces command sent")
      tn.read_until("ppp_device     Enabled               ", 2000)
      ip2 = tn.read_until(" ",2000)
      logger.logit("ip read")
      tn.write("@close\r\n")
      logger.logit("@close command sent")
      ipdata = ip2[:-1]
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "dsl504.out"
    if opt_directory:
      filename = opt_directory + filename
    open(filename, "w").write(ipdata)
    logger.logit("dsl504.out file created")

    localip = ipdata
    logger.logit("IP matched: " + localip)

      
  elif opt_Linksys_router != 0:
    # 
    # Linksys router ip detection
    # 
    ipdir = Linksys_page

    #
    # determine the linksys router host address
    # 
    iphost = ""
    if routerIP:
      logger.logit("Linksys_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost == "":
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"
    else:
      logline = "Trying linksys router at " + iphost
      logger.logit(logline)

    # connect to the router's admin webpage
    ipdata = ""
    try:
      logger.logit("Trying Linksys old auth")
      h1 = httplib.HTTP(iphost)

      #
      # Hack from Bobby Griggs for authorization.
      #
      # For some reason the router won't authenticate when
      # using standard headers for authorization.  Like this:
      #
      #h1.putrequest('GET', ipdir)
      #authstring = base64.encodestring(Linksys_user + ":" + opt_Linksys_password)
      #h1.putheader("Authorization", "Basic " + authstring)
      #
      # It may be looking for lines that end with just \n not \r\n.
      #
      # Note:  Modified by Greg Bentz.
      #        Linksys firmware 1.37, doesn't like the trailing \n on the authstring.
      #        Also requires "\r\n".
      #        My theory concerning the standard headers is that the Linksys header
      #        parsing requires all the header info to appear in one packet.
      #        Use of an extra putheader() call puts the authorization information into
      #        a second packet which is not read by the Linksys device.
      #
      authstring = base64.encodestring(Linksys_user + ":" + opt_Linksys_password)
      authstring = string.replace(authstring, "\012", "")
      ipdir = Linksys_page + ' HTTP/1.1 \r\n' \
        + 'Authorization: Basic ' \
        + authstring + '\r\n'
      h1.putrequest('GET', ipdir)

      h1.endheaders()

      errcode, errmsg, headers = h1.getreply()
      fp = h1.getfile()
      ipdata = fp.read()
      fp.close()

      logger.logit("Parsing Linksys old auth")
      p1 = string.find(ipdata, "WAN")
      if p1 != -1:
        p2 = string.find(ipdata, "IP", p1)
        if p2 != -1:
          ipmatch = Addressgrep.search(ipdata, p2)
          if ipmatch != None:
            localip = ipmatch.group()
            logger.logit("IP matched: " + localip)
    except:
      logger.logit("Exception Linksys old auth")

    if localip == "":
      try:
        logger.logit("Trying Linksys second auth")
        h1 = httplib.HTTP(iphost)
        authstring = base64.encodestring(Linksys_user + ":" + opt_Linksys_password)
        authstring = string.replace(authstring, "\012", "")
        ipdir = "/Status_Router.htm" + ' HTTP/1.1 \r\n' \
          + 'Authorization: Basic ' \
          + authstring + '\r\n'
        h1.putrequest('GET', ipdir)
        h1.endheaders()
        errcode, errmsg, headers = h1.getreply()
        fp = h1.getfile()
        ipdata = fp.read()
        fp.close()

        logger.logit("Parsing Linksys second auth")
        p1 = string.find(ipdata, "Internet IP")
        if p1 != -1:
          ipmatch = Addressgrep.search(ipdata, p1)
          if ipmatch != None:
            localip = ipmatch.group()
            logger.logit("IP matched: " + localip)

      except:
        logger.logit("Exception Linksys second auth")

    # Support for Linksys WRT54G Wireless Router
    # Modified by David Bresson 
    if localip == "":
      try:
        logger.logit("Trying Linksys WRT54G")
        h1 = httplib.HTTP(iphost)
        authstring = base64.encodestring(Linksys_user + ":" + opt_Linksys_password)
        authstring = string.replace(authstring, "\012", "")
        ipdir = "/Status_Router.asp" + ' HTTP/1.1 \r\n' \
          + 'Authorization: Basic ' \
          + authstring + '\r\n'
        h1.putrequest('GET', ipdir)
        h1.endheaders()
        errcode, errmsg, headers = h1.getreply()
        fp = h1.getfile()
        ipdata = fp.read()
        fp.close()

        logger.logit("Parsing Linksys WRT54G")
        p1 = string.find(ipdata, "wan_ip = ")
        if p1 != -1:
          ipmatch = Addressgrep.search(ipdata, p1)
          if ipmatch != None:
            localip = ipmatch.group()
            logger.logit("IP matched: " + localip)

      except:
        logger.logit("Exception Linksys WRT54G")

    # Support for Linksys RT31P2 Vonage VoIP Gateway Router
    # Default IP is 192.168.15.1.  Could support that later.
    if localip == "":
      try:
        logger.logit("Trying Linksys RT31P2")
        h1 = httplib.HTTP(iphost)
        authstring = base64.encodestring(Linksys_user + ":" + opt_Linksys_password)
        authstring = string.replace(authstring, "\012", "")
        ipdir = "/RouterStatus.htm" + ' HTTP/1.1 \r\n' \
          + 'Authorization: Basic ' \
          + authstring + '\r\n'
        h1.putrequest('GET', ipdir)
        h1.endheaders()
        errcode, errmsg, headers = h1.getreply()
        fp = h1.getfile()
        ipdata = fp.read()
        fp.close()

        logger.logit("Parsing Linksys RT31P2")
        p1 = string.find(ipdata, "Internet IP")
        if p1 != -1:
          ipmatch = Addressgrep.search(ipdata, p1)
          if ipmatch != None:
            localip = ipmatch.group()
            logger.logit("IP matched: " + localip)
 
      except:
        logger.logit("Exception Linksys RT31P2")

    # Support for Linksys WRT54GS
    # Thanks to Roland Bassett for testing
    if localip == "":
      try:
        logger.logit("Trying Linksys WRT54GS")

        proto = 'http://'
        thepage = '/StaRouter.htm'
        theurl = proto + iphost + thepage

        username = 'admin'
        password = opt_Linksys_password

        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, theurl, username, password)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

        try:
          response = urllib2.urlopen(theurl)
        except IOError, e:
          if hasattr(e, 'reason'):
            logger.logit( e.reason )
          elif hasattr(e, 'code'):
            logger.logit( e.code )

        # try to get the html text
        try:
          ipdata = response.read()
        except:
          ipdata = ""

        logger.logit("Parsing Linksys WRT54GS")
        p1 = string.find(ipdata, "wan_ip = ")
        if p1 != -1:
          ipmatch = Addressgrep.search(ipdata, p1)
          if ipmatch != None:
            localip = ipmatch.group()
            logger.logit("IP matched: " + localip)
 
      except:
        logger.logit("Exception Linksys WRT54GS")

    # create an output file of the linksys response
    if ipdata != "":
      filename = "linksys.out"
      if opt_directory != "":
        filename = opt_directory + filename
      fp = open(filename, "w")
      fp.write(ipdata)
      fp.close()
      logger.logit("linksys.out file created")
    else:
      logger.logit("No ipdata for linksys.out file.")


  elif opt_Watchguard_password:
    # 
    # Watchguard firewall/router ip detection
    # 
    ipdir = Watchguard_page

    #
    # determine the watchguard soho router host address
    # 
    if routerIP:
      logger.logit("Watchguard_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying Watchguard SOHO firewall at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.111.1")
      iphost = "192.168.111.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Watchguard")
      h1 = httplib.HTTP(iphost)

      authstring = base64.encodestring(Watchguard_user + ":" + opt_Watchguard_password)
      authstring = string.replace(authstring, "\012", "")
      ipdir = Watchguard_page + ' \r\n' \
        + 'Authorization: Basic ' \
        + authstring + '\r\n'
      h1.putrequest('GET', ipdir)
      h1.putheader("AUTHORIZATION", "Basic " + authstring)

      h1.endheaders()

      errcode, errmsg, headers = h1.getreply()
      fp = h1.getfile()
      ipdata = fp.read()
      fp.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    ipmatch = Addressgrep.search(ipdata)
    if ipmatch != None:
      localip = ipmatch.group()
      logger.logit("IP matched: " + localip)
    else:
      logger.logit("Trying Watchguard new firmware")
      h1 = httplib.HTTP(iphost)

      authstring = base64.encodestring(Watchguard_user + ":" + opt_Watchguard_password)
      authstring = string.replace(authstring, "\012", "")
      ipdir = Watchguard_page2 + ' \r\n' \
        + 'Authorization: Basic ' \
        + authstring + '\r\n'
      h1.putrequest('GET', ipdir)
      h1.putheader("AUTHORIZATION", "Basic " + authstring)
      h1.endheaders()

      errcode, errmsg, headers = h1.getreply()
      fp = h1.getfile()
      ipdata = fp.read()
      fp.close()

    # create an output file of the watchguard response
    filename = "watchguard.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("watchguard.out file created")

    ipmatch = Addressgrep.search(ipdata)
    if ipmatch != None:
      localip = ipmatch.group()
      logger.logit("IP matched: " + localip)

  elif opt_DI701_password:

    #
    # determine the router host address
    #
    if routerIP:
      logger.logit("DI701_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 192.168.1.1")
      iphost = "192.168.1.1"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying DLink DI701")
      tn = telnetlib.Telnet(iphost,333)
      logger.logit("Creating telnetlib obj done")
      tn.read_until("assword : ")
      logger.logit("Password prompt found")
      tn.write(opt_DI701_password + "\r")
      logger.logit("opt_DI701_password sent")
      tn.read_until("command>")
      tn.write("show\r")
      logger.logit("show command sent")
      tn.read_until("address of global port : [", 2000)
      ip2 = tn.read_until("]", 2000)
      logger.logit("ip read")
      #tn.write("exit\r\n")
      #logger.logit("exit sent")
      ipdata = ip2[:-1]
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "di701.out"
    if opt_directory:
      filename = opt_directory + filename
    open(filename, "w").write(ipdata)
    logger.logit("di701.out file created")

    localip = ipdata
    logger.logit("IP matched: " + localip)

  elif opt_AlcatelSTP_password:

    #
    # determine the router host address
    #
    if routerIP:
      logger.logit("AlcatelSTP_host set explicitly.")
      iphost = routerIP
    else:
      iphost = DefaultRoute(logger, Tempfile)

    if iphost:
      logline = "Trying router at " + iphost
      logger.logit(logline)
    else:
      logger.logit("No router ip detected.  Assuming 10.0.0.138")
      iphost = "10.0.0.138"

    # connect to the router's admin webpage
    try:
      logger.logit("Trying Alcatel STP")
      # disables negotiation to prevent the connection being dropped
      telnetlib.IAC="\021"  
      tn = telnetlib.Telnet(iphost)
      logger.logit("Creating telnetlib obj done")
      tn.read_until(" : ")
      logger.logit("User prompt found")
      tn.write(Alcatel_user + "\r")
      tn.write(opt_AlcatelSTP_password + "\r")
      logger.logit("opt_AlcatelSTP_password sent")
      tn.read_until("=>")
      tn.write("ip aplist\r")
      logger.logit("ip aplist sent")
      ret=tn.read_until("SERIAL",5)
      if string.find(ret,"SERIAL")==-1:
        # is an Alcatel version 4.3.2.6 ?
        tn.write("\r")
        tn.read_until("=>")
        tn.write("ip iplist\r")
        logger.logit("ip iplist sent")
        ret=tn.read_until("Serial          ",5)
        if string.find(ret,"Serial          ")==-1:
           raise "not connected"
      else:
        tn.read_until("addr:")
      ip2 = tn.read_until(" ")
      logger.logit("ip read")
      ipdata = ip2[:-1]
      if len(opt_forward) != 0:
        for opt_forwardportprotocol in opt_forward:
          tn.read_until("=>")
          logline="nat create protocol=%s inside_addr=%s inside_port=%s outside_addr=%s outside_port=%s "
          logline=logline % ( opt_forwardportprotocol[1], tn.sock.getsockname()[0], 
            opt_forwardportprotocol[0], ipdata, opt_forwardportprotocol[0] )
          tn.write(logline+"\r")
          logger.logit(logline)
          tn.read_until(logline)
        tn.read_until("=>")
      # no exit needed
      tn.close()
    except:
      logline = "No address found on router at " + iphost
      logger.logexit(logline)
      sys.exit(-1)

    # create an output file of the response
    filename = "alcatel_stp.out"
    if opt_directory:
      filename = opt_directory + filename
    open(filename, "w").write(ipdata)
    logger.logit("alcatel_stp.out file created")

    localip = ipdata
    logger.logit("IP matched: " + localip)

  elif opt_router:
    logger.logit("web based ip detection for localip")
    ipurl = ""

    # check for deprecated url
    if string.find(opt_router, "cgi-bin/check_ip.cgi") != -1:
      logger.logexit("You should be using -r checkip.dyndns.org ")
      logger.logexit("Continuing with new URL.")
      opt_router = "checkip.dyndns.org:8245"
    
    # strip off the http part, if any
    if opt_router[:7] == "HTTP://" or opt_router[:7] == "http://":
      ipurl = opt_router[7:]
    else:
      ipurl = opt_router

    # stick it back on for urllib usage
    ipurl = "http://" + ipurl

    # grab the data
    try:
      logger.logit("Trying URL " + ipurl)
      urlfp = urllib.urlopen(ipurl)
      ipdata = urlfp.read()
      urlfp.close()
    except:
      logline = "Unable to open url " + ipurl
      logger.logexit(logline)
      logger.logexit("Exception: " + `sys.exc_info()[0]`)
      sys.exit(-1)


    # create an output file of the ip detection response
    filename = "webip.out"
    if opt_directory:
      filename = opt_directory + filename
    fp = open(filename, "w")
    fp.write(ipdata)
    fp.close()
    logger.logit("webip.out file created")

    # grab first thing that looks like an IP address
    ipmatch = Addressgrep.search(ipdata)
    if ipmatch != None:
      localip = ipmatch.group()
      logger.logit("webip detected = " + localip)

  else:
    logger.logit("Interface ip detection on sys.platform = " + sys.platform)
    if sys.platform == "win32":
      logger.logit("win32 interface ip detection for localip")
      getip = Win32ip 
      os.system (getip + " > " + Tempfile)
      fp = open(Tempfile, "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after the interface
      p1 = string.find(ipdata, opt_interface)
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    elif string.find(sys.platform, "sunos") != -1:
      logger.logit("Sunos interface ip detection for localip (untested)")
      fp = os.popen(Sunip + " " + opt_interface, "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after the interface
      p1 = string.find(ipdata, opt_interface)
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    elif string.find(sys.platform, "linux") != -1:
      logger.logit("linux interface ip detection for localip")
      fp = os.popen(Linuxip + " " + opt_interface, "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after the interface
      p1 = string.find(ipdata, opt_interface)
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    elif string.find(sys.platform, "Darwin") != -1:
      logger.logit("Darwin interface ip detection for localip")
      fp = os.popen(Macip + " " + opt_interface , "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after the LAST inet (to avoid dead routes)
      p1 = string.rfind(ipdata, "inet ")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    elif string.find(sys.platform, "os2") != -1:
      logger.logit("OS2 interface ip detection for localip")
      getip = Os2ip + " " + opt_interface
      os.system (getip + " > " + Tempfile)
      fp = open(Tempfile, "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after the LAST inet (to avoid dead routes)
      p1 = string.rfind(ipdata, "inet ")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    elif string.find(sys.platform, "beos") != -1:
      logger.logit("BeOS interface ip detection for localip")
      getip = Beosip 
      os.system (getip + " > " + Tempfile)
      fp = open(Tempfile, "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after interface text
      p1 = string.rfind(ipdata, opt_interface + ":")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    elif string.find(sys.platform, "bsd") != -1:
      logger.logit("*BSD* interface ip detection for localip")
      fp = os.popen(BSDip + " " + opt_interface + " | grep -v 192.168 ", "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after the LAST inet (to avoid dead routes)
      p1 = string.rfind(ipdata, "inet ")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    elif string.find(sys.platform, "sco_") != -1:
      logger.logit("SCO interface ip detection for localip")
      getip = Scoip + " " + opt_interface 
      os.system (getip + " > " + Tempfile)
      fp = open(Tempfile, "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after the LAST inet (to avoid dead routes)
      p1 = string.rfind(ipdata, "inet ")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    else:
      logger.logit("Default interface ip detection for localip (untested)")
      getip = Otherip + " " + opt_interface 
      os.system (getip + " > " + Tempfile)
      fp = open(Tempfile, "r")
      ipdata = fp.read()
      fp.close()
      # grab the first dotted quad after the LAST inet (to avoid dead routes)
      p1 = string.rfind(ipdata, "inet ")
      if p1 != -1:
        ipmatch = Addressgrep.search(ipdata, p1)
        if ipmatch != None:
          localip = ipmatch.group()
          logger.logit("IP matched: " + localip)

    # check if we have a localip from all the above elifs
    if not localip:
      logline = "No address found on interface " + opt_interface + " use -i"
      logger.logexit(logline)
      sys.exit(-1)


  # end of all determining localip cases
  logline = check_ip(localip)
  if logline:
    logger.logexit(logline)
    sys.exit(-1)
    
  #
  # create the dat file from dns lookup if specified
  #
  if opt_makedat:
    logger.logit("DNS lookups to create data file.")

    if datfile.exists():
      logger.logexit("There is already an ipcheck.dat file existing.")
      logger.logexit("Remove this file first before running --makedat")
      sys.exit(0)
    else:
      logger.logit("Good, no ipcheck.dat file found.")

    ip1 = ""
    ip2 = ""
    h = ""
    try:
      for h in hostnames:
        if string.find(h, "recursivedns.com") != 0:
          logger.logit("detected recursivedns.com host")
          logger.logit("setting opt_force and skipping of dns lookup")
          opt_force = 1
          ip1 = "99.99.99.99"
          break

        if not ip1:
          logger.logexit("ip1 looking up " + h)
          (a, b, c) = socket.gethostbyname_ex(h)
          line = `a` + `b` + `c`
          logger.logexit("result: " + line)
          ip1 = c[0]
          logger.logit("ip1 = " + ip1)
          ip2 = ip1
        else:
          logger.logexit("ip2 looking up " + h)
          (a, b, c) = socket.gethostbyname_ex(h)
          line = `a` + `b` + `c`
          logger.logexit("result: " + line)
          ip2 = c[0]
          logger.logit("ip2 = " + ip2)

        # check if not same
        if ip1 != ip2:
          logger.logexit("WARNING: hostnames have different ips.")
          logger.logexit("I'm going to set the force option so all hosts")
          logger.logexit("will be synchronized to the same IP address.")
          opt_force = 1

    except:
      logger.logexit("Problems looking up hostname " + h)
      logger.logexit("Make sure the hostname is correct, is setup at Dyndns,")
      logger.logexit("and that local DNS lookups are working fine.")
      logger.logexit("Exception: " + `sys.exc_info()[0]`)
      sys.exit(-1)


    logger.logit("Writing the new dat file.")
    datfile.write(ip1, hostnames)

  #
  # read the data from file of last update, if any
  #
  if datfile.exists():
    (fileip, filehosts) = datfile.read()
    fileage = datfile.getAge()
  else:
    # do not create the file automatically cause people could get
    # into loops and use up a lot of bandwidth doing dns lookup
    logger.logexit("No ipcheck.dat file found.")
    logger.logexit("Use same command+options ONCE with --makedat to create from DNS lookup.")
    sys.exit(0)

  dnslookupip = ""
  if opt_checkDNS:
    ip2 = ""
    h = ""
    try:
      for h in hostnames:
        if not dnslookupip:
          logger.logexit("dnslookupip looking up " + h)
          (a, b, c) = socket.gethostbyname_ex(h)
          line = `a` + `b` + `c`
          logger.logexit("result: " + line)
          dnslookupip = c[0]
          logger.logit("dnslookupip = " + dnslookupip)
          ip2 = dnslookupip
        else:
          logger.logexit("ip2 looking up " + h)
          (a, b, c) = socket.gethostbyname_ex(h)
          line = `a` + `b` + `c`
          logger.logexit("result: " + line)
          ip2 = c[0]
          logger.logit("ip2 = " + ip2)
  
        # check if not same
        if dnslookupip != ip2:
          logger.logexit("WARNING: hostnames have different ips.")
          logger.logexit("I'm going to set the force option so all hosts")
          logger.logexit("will be synchronized to the same IP address.")
          opt_force = 1
  
    except:
      logger.logexit("Problems looking up hostname " + h)
      logger.logexit("Make sure the hostname is correct, is setup at Dyndns,")
      logger.logexit("and that local DNS lookups are working fine.")
      logger.logexit("Exception: " + `sys.exc_info()[0]`)
      sys.exit(-1)

  #
  # check filehosts list versus hostnames list
  #
  mismatch = 0
  for h in filehosts:
    if h not in hostnames:
      mismatch = 1
  for h in hostnames:
    if h not in filehosts:
      mismatch = 1
  if not mismatch:
    logger.logit("Good, filehosts and hostnames are the same.")
  else:
    # do not create the file automatically cause people could get
    # into loops and use up a lot of bandwidth doing dns lookup
    logger.logexit("The hostnames listed do not match the ipcheck.dat file.")
    logger.logexit("Remove the dat file and use same command ONCE with --makedat.")
    logger.logexit("Note that if you are maintaining both a custom domain and")
    logger.logexit("a dyndns domain, you should be using the -d option and")
    logger.logexit("keeing the data files in separate directories.")
    sys.exit(0)



  #
  # read the data from error file, if any
  #
  if not errfile.exists():
    logger.logit("Good, no ipcheck.err file.")
  elif not opt_force:
    logger.logit("Handling errors in ipcheck.err file.")
    fatal = errfile.analyze(opt_username,opt_password,hostnames)
    if fatal:
      sys.exit(-1)
  #
  # read the data from wait file, if any
  #
  waitcode = ""
  waitdate = ""
  try:
    fp = open (Waitfile, "r")
    waitcode = fp.readline()
    if waitcode[-1] == "\n": 
      waitcode = waitcode[:-1]
    waitdate = fp.readline()
    if waitdate[-1] == "\n": 
      waitdate = waitdate[:-1]
    fp.close()
  except:
    logger.logit("Good, no ipcheck.wait file.")

  if waitcode and not opt_force:

    logger.logit("Found wait entry.")
    logger.logit(waitcode)
    logger.logit(waitdate)

    #
    # first line is the code
    # second line is time.time() when the code was received
    # now determine whether we should continue or abort
    # remove the file if the wait is no longer needed
    #
    try:
      waitnum = float(waitdate)
    except:
      waitnum = 0.0

    if waitnum == 0.0:
      logger.logit("Invalid wait date in ipcheck.wait file.")
      logger.logit("ipcheck.wait file removed and continuing.")
      os.unlink (Waitfile)

    elif waitcode[0] == 'u':
      # wait until GMT
      logger.logit("Decoding wait until entry in ipcheck.wait file.")

      # First we check the age of the file.
      currtime = time.time()
      mtime = os.stat(Waitfile)[stat.ST_MTIME]
      if (currtime - mtime) / (60*60) > 24:
        # the file is older than 24 hours and should be ignored
        logger.logit("Stale ipcheck.wait file removed and continuing.")
        os.unlink (Waitfile)
      elif (currtime - waitnum) / (60*60) > 24:
        # the code is older than 24 hours and should be ignored
        logger.logit("Stale code in file removed and continuing.")
        os.unlink (Waitfile)
      else:
        try:
          waitsec = int(waitcode[2:])
        except:
          waitsec = 0

        currtime = time.time()
        if currtime > waitnum + waitsec:
          logger.logit("until wait entry expired.")
          logger.logit("ipcheck.wait file removed and continuing.")
          os.unlink (Waitfile)
        else:
          logger.logit("until wait entry in effect: quietly aborting.")
          sys.exit(-1)
  
    else:
      # wait h, m or s
      logger.logit("Decoding hms entry in ipcheck.wait file.")
      try:
        waitsec = int(waitcode[1:3])
        if waitcode[3] == 'h' or waitcode[3] == 'H':
          waitsec = waitsec * 60 * 60
        elif waitcode[3] == 'm' or waitcode[3] == 'M':
          waitsec = waitsec * 60 
      except:
        waitsec = 0

      currtime = time.time()
      if currtime > waitnum + waitsec:
        logger.logit("hms wait entry expired.")
        logger.logit("ipcheck.wait file removed and continuing.")
        os.unlink (Waitfile)
      else:
        logger.logit("hms wait entry in effect: quietly aborting.")
        sys.exit(-1)

  #
  # determine whether and which hosts need updating
  #
  updatehosts = []

  # if opt_force is set then update all hosts
  # or offline mode selected
  if opt_force or opt_offline:
    logger.logit("Updates forced by -f option.")
    for host in hostnames:
      updatehosts.append(host)

  # else if file age is older than update all hosts
  # Touchage == 0 means don't update
  elif fileage > Touchage and Touchage > 0:
    logger.logit("Updates required by stale ipcheck.dat file.")
    for host in hostnames:
      updatehosts.append(host)

  # else check the address from dns lookup
  elif opt_checkDNS and localip != dnslookupip:
    logger.logit("Updates required by ip lookup address mismatch.")
    logger.logit("localip = " + localip + " dnslookupip = " + dnslookupip)
    for host in hostnames:
      updatehosts.append(host)

  # else check the address used in last update
  elif localip != fileip:
    logger.logit("Updates required by ipcheck.dat address mismatch.")
    for host in hostnames:
      updatehosts.append(host)

  # This case is probably deprecated but will leave it in
  # case I missed something.  When reading the dat file,
  # I'm going to now only proceed if hostnames == filehosts.
  # Otherwise, a message will be printed out and an option
  # to create a dat file from dns lookups will be recommended.

  else:
    logger.logit("Checking hosts in file vs command line.")
    updateflag = 0
    for host in hostnames:
      if host not in filehosts:
        updateflag = 1

    # If anyone of the hosts on the command line needs updating,
    # put them all in the updatehosts list so they will get the
    # same last updated timestamp at dyndns.  This way they all 
    # won't need to be touched again for Touchage days, instead 
    # of having multiple touches for different last updated dates.
    if updateflag:
      for host in hostnames:
        updatehosts.append(host)

  if updatehosts == []:
    # Quietly log this message then exit too.
    logger.logit("The database matches local address.  No hosts update.")
    sys.exit(0)

  #
  # build the query strings
  #
  updateprefix = Updatepage
  if opt_static:
    updateprefix = updateprefix + "?system=statdns&hostname="
  elif opt_custom:
    updateprefix = updateprefix + "?system=custom&hostname="
  else:
    updateprefix = updateprefix + "?system=dyndns&hostname="

  hostlist = ""
  for host in updatehosts:
    hostlist = hostlist + host + ","
    logger.logit(host + " needs updating")
  if len(hostlist) > 0:
    hostlist = hostlist[:-1]

  if opt_offline:
    if opt_static:
      logger.logexit("offline and static mode not allowed together.")
      sys.exit(-1)

  updatesuffix = ""
  if opt_offline:
    #updatesuffix = updatesuffix + "&myip=1.0.0.0" 
    updatesuffix = updatesuffix + "&offline=YES"
  else:
    # only do these other things if not setting offline mode
    if opt_guess:
      logger.logit("Letting dyndns guess the IP.")
      localip = ""
    else:
      updatesuffix = updatesuffix + "&myip=" + localip 

    # custom domains do not have wildcard or mx records
    if not opt_custom:

      if opt_wildcard != "":
        updatesuffix = updatesuffix + "&wildcard=" + opt_wildcard
      else:
        updatesuffix = updatesuffix + "&wildcard=OFF"

      if opt_backupmx != "":
        updatesuffix = updatesuffix + "&backmx=" + opt_backupmx
      else:
        updatesuffix = updatesuffix + "&backmx=NO"

      if opt_mxhost:
        updatesuffix = updatesuffix + "&mx=" + opt_mxhost

  logger.logit("Prefix = " + updateprefix)
  logger.logit("Hosts  = " + hostlist)
  logger.logit("Suffix = " + updatesuffix)

  if opt_testrun:
    logger.logit("test run exits here")
    sys.exit()
    
  #
  # check which version of python we are using
  #
  # apache2 ssl returns EOF too soon for python2's ssl library
  # and causes an exception.  apache1 with mod_ssl worked fine.
  # Python 1.5.x works fine also.
  #
  for py_ver in ["2.2", "2.1"]:
    python2 = string.find(sys.version, py_ver)
    if python2 == 0:
      logger.logit("Using python " + py_ver +", https disabled")
      opt_no_https = 1

  #
  # update those hosts 
  #
  if not opt_no_https:
    logline = "trying to open HTTPS connection" 
    logger.logit(logline)
    try:
      if not opt_proxy:
        h2 = httplib.HTTPS(Updatehost)
        logline = "HTTPS connection successful" 
        logger.logit(logline)
      else:
        h2 = httplib.HTTPS(Updatehost, 8245)
        logline = "HTTPS connection successful" 
        logger.logit(logline)
    except:
      logline = "trying to open normal HTTP connection" 
      logger.logit(logline)
      if not opt_proxy:
        h2 = httplib.HTTP(Updatehost)
        logline = "normal HTTP connection successful" 
        logger.logit(logline)
      else:
        h2 = httplib.HTTP(Updatehost, 8245)
        logline = "normal HTTP connection successful" 
        logger.logit(logline)
  else:
    logline = "trying to open normal HTTP connection" 
    logger.logit(logline)
    if not opt_proxy:
      h2 = httplib.HTTP(Updatehost)
      logline = "normal HTTP connection successful" 
      logger.logit(logline)
    else:
      h2 = httplib.HTTP(Updatehost, 8245)
      logline = "normal HTTP connection successful" 
      logger.logit(logline)

  httpdata = "No output from http request."
  errmsg = ""
  errcode = 200
  try:
    logline = "Trying to end headers and get reply with httplib" 
    logger.logit(logline)

    h2.putrequest("GET", updateprefix + hostlist + updatesuffix)
    h2.putheader("HOST", Updatehost)
    h2.putheader("USER-AGENT", Fakeagent)
    authstring = base64.encodestring(opt_username + ":" + opt_password)
    authstring = string.replace(authstring, "\012", "")
    h2.putheader("AUTHORIZATION", "Basic " + authstring)
    h2.endheaders()
    errcode, errmsg, headers = h2.getreply()

    # log the result
    logline = "http code = " + `errcode`
    logger.logit(logline)
    logline = "http msg  = " + errmsg
    logger.logit(logline)

    # try to get the html text
    fp = None
    try:
      fp = h2.getfile()
      httpdata = fp.read()
    except:
      httpdata = "No output from http request."

    if fp:
      fp.close()
      logger.logit("fp closed.")

    logger.logit("Skipping fp close.")

  except:
    logline = "Trying to end headers and get reply with urllib2" 
    logger.logit(logline)

    protocol = "http://"
    theurl = Updatehost + Updatepage

    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, theurl, opt_username, opt_password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)
    try:
      response = urllib2.urlopen(protocol + theurl)
    except IOError, e:
      if hasattr(e, 'reason'):
        errmsg = e.reason
      elif hasattr(e, 'code'):
        errcode = e.code

    # try to get the html text
    try:
      httpdata = response.read()
    except:
      httpdata = "No output from http request."


  # create the output file
  fp = open (Htmlfile, "w")
  fp.write(httpdata)
  fp.close()
  logger.logit("ipcheck.html file created")

  #
  # check the result for fatal errors
  #
  
  # badauth may appear anywhere when errcode is 401
  if string.find(httpdata, "badauth") != -1 and errcode == 401:
    logline = "Invalid username and password specified on command line." 
    logger.logexit(logline)

    #
    # save the error to an ipcheck.err file
    #
    errfile.write("badauth " + opt_username + " " + opt_password, fatal=1)
    sys.exit(-1)

  elif errcode == 404:
    logger.logexit("404 Not Found returned by dyndns server.")
    logger.logexit("Please try again in a few minutes.")
    sys.exit(-1)

  # badsys must begin the resulting text and errcode is 200
  elif httpdata[:6] == "badsys" and errcode == 200:
    logline = "Bad system parameter specified (not dyndns or statdns)." 
    logger.logexit(logline)

    #
    # save the error to an ipcheck.err file
    #
    if opt_static:
      errfile.write("badsys statdns", fatal=1)
    elif opt_custom:
      errfile.write("badsys custom", fatal=1)
    else:
      errfile.write("badsys dyndns", fatal=1)
    sys.exit(-1)

  # badagent must begin the resulting text and errcode is 200
  elif httpdata[:8] == "badagent" and errcode == 200:
    logger.logexit("Badagent contact author at kal@users.sourceforge.net.")
    errfile.write("badagent", fatal=1)
    sys.exit(-1)

  # 911 may appear anywhere when errcode is 500
  elif string.find(httpdata, "911") != -1 and errcode == 500:
    logline = "Dyndns 911 result.  Dyndns emergency shutdown."
    logger.logexit(logline)
    errfile.write("shutdown", fatal=1)
    sys.exit(-1)

  # 999 may appear anywhere when errcode is 500
  elif string.find(httpdata, "999") != -1 and errcode == 500:
    logline = "Dyndns 999 result.  Dyndns emergency shutdown."
    logger.logexit(logline)
    errfile.write("shutdown", fatal=1)
    sys.exit(-1)

  #
  # don't really know what codes go with numhost, dnserr and wxxxx
  # probably errcode 200 but no need to assume this instead
  # assume they will be sent at the beginning of a line
  # we check those codes below
  #

  elif errcode == 200:

    # build the results list
    results = []
    fp = open (Htmlfile, "r")
    for host in hostnames:
      resultline = fp.readline()
      if resultline[-1:] == "\n":
        resultline = resultline[:-1]
      results.append(resultline)
    fp.close()

    # check if we have one result per updatehosts 
    if len(results) == len(updatehosts):
      idx = 0
      success = 0
      for host in updatehosts:
        #
        # use logexit to generate output (email if ran from a cronjob)
        #
        if results[idx][:4] == "good":
          logline = host + " " + results[idx] + " -update successful"
          if opt_quiet:
            logger.logit(logline)
          else:
            logger.logexit(logline)

          # update the localip dyndns found if guess was used
          if opt_guess and not localip:
            p1 = string.find(results[idx], " ")
            localip = string.rstrip(results[idx][p1+1:])
            logger.logit("Dyndns guessed IP: " + localip)

          # set the success update flag
          success = 1

        elif results[idx][:5] == "nochg":
          logline = host + " " + results[idx] + " -abusive if continually repeated"
          logger.logexit(logline)

          # update the localip dyndns found if guess was used
          if opt_guess and not localip:
            p1 = string.find(results[idx], " ")
            localip = string.rstrip(results[idx][p1+1:])
            logger.logit("Dyndns guessed IP: " + `localip`)

        elif results[idx][:7] == "!active":
          logline = host + " " + results[idx] + " -zone not active yet"
          logger.logexit(logline)
          logger.logexit("Try again in an hour")

          # clear localip to remove ipcheck.dat file
          localip = ""

        elif results[idx][:5] == "abuse":
          logline = host + " " + results[idx] + " -hostname blocked for abuse"
          logger.logexit(logline)
          logger.logexit("Use the form at http://support.dyndns.org/dyndns/abuse.shtml")
          logger.logexit("Erase the ipcheck.err file when dyndns notifies you (by email).") 

          # update the localip dyndns found if guess was used
          if opt_guess and not localip:
            p1 = string.find(results[idx], " ")
            localip = string.rstrip(results[idx][p1+1:])
            logger.logit("Dyndns guessed IP: " + `localip`)

          #
          # save the error to an ipcheck.err file
          #
          errfile.write("abuse " + host)
        elif results[idx][:7] == "notfqdn":
          logline = host + " " + results[idx] + " -FQDN hostnames needed"
          logger.logexit(logline)
          errfile.write("notfqdn " + host)
          # set the localip so next update will be made
          localip = "0.0.0.0"

        elif results[idx][:6] == "nohost":
          logline = host + " " + results[idx] + " -hostname not found"
          logger.logexit(logline)
          errfile.write("nohost " + host)
          # set the localip so next update will be made
          localip = "0.0.0.0"

        elif results[idx][:7] == "!active":
          logline = host + " " + results[idx] + " -hostname not activated yet"
          logger.logexit(logline)
          errfile.write("!active " + host)
          # set the localip so next update will be made
          localip = "0.0.0.0"

        elif results[idx][:6] == "!yours":
          logline = host + " " + results[idx] + " -hostname not yours"
          logger.logexit(logline)
          errfile.write("!yours " + host)
          # set the localip so next update will be made
          localip = "0.0.0.0"

        elif results[idx][:7] == "numhost":
          logline = host + " " + results[idx] + " -send ipcheck.html to support@dyndns.org"
          logger.logexit(logline)
          errfile.write("numhost " + host)
          # set the localip so next update will be made
          localip = "0.0.0.0"

        elif results[idx][:6] == "dnserr":
          logline = host + " " + results[idx] + " -send ipcheck.html to support@dyndns.org"
          logger.logexit(logline)
          errfile.write("dnserr " + host)
          # set the localip so next update will be made
          localip = "0.0.0.0"

        elif results[idx][:2] == "wu":
          logline = host + " " + results[idx] + " -wait until entry created"
          logger.logexit(logline)

          # get the wait code HH MM 
          try:
            codeHH = int(results[idx][2:4])
            codeMM = int(results[idx][4:6])
          except:
            codeHH = 0
            codeMM = 0
          codeHHMM = codeHH * 100 + codeMM

          # try to get the current time from the HTTP headers at dyndns 
          datetuple = headers.getdate("Date")
          if datetuple == None:
            logger.logit("Date header not found.  Using local clock.")
            datetuple = gmtime(time.time())
          currHH = datetuple[3]
          currMM = datetuple[4]
          currHHMM = currHH * 100 + currMM

          # compute the HHMM we need to wait
          if (codeHHMM <= currHHMM):
            # The codeHHMM is smaller than GMT of when we received the code.
            # Example: NIC returned 02:30 (codeHHMM) when we tried to update 
            # at 21:30 (currHHMM).  So we should be waiting 21:30 to 24:00
            # plus 00:00 to 02:30 seconds.
            waitHH = (23 - currHH) + codeHH
            waitMM = (60 - currMM) + codeMM
            logger.logit("Wraparound calculation.")
          else:
            waitHH = codeHH - currHH
            waitMM = codeMM - currMM
            logger.logit("Normal calculation.")
          
          # convert to seconds
          waitval = (waitHH * 60 + waitMM) * 60

          logger.logit("currHHMM = " + `currHHMM`)
          logger.logit("codeHHMM = " + `codeHHMM`)
          logger.logit("waitval  = " + `waitval`)

          # convert back to seconds
          #
          # save the until calculation to an ipcheck.wait file
          #
          fp = open (Waitfile, "a")
          fp.write("u " + `waitval` + "\n")
          currtime = time.time()
          fp.write(`time.time()` + "\n")
          fp.close()
          logger.logit("ipcheck.wait file created.")

          # set the localip so next update will be made
          localip = "0.0.0.0"

        elif results[idx][0] == "w":
          logline = host + " " + results[idx] + " -wait entry created"
          logger.logexit(logline)

          #
          # save the waitcode to an ipcheck.wait file
          #
          fp = open (Waitfile, "a")
          fp.write(results[idx] + "\n")
          currtime = time.time()
          fp.write(`time.time()` + "\n")
          fp.close()
          logger.logit("ipcheck.wait file created.")

          # set the localip so next update will be made
          localip = "0.0.0.0"

        elif results[idx][:8] == "!donator":
          logline = host + " " + results[idx] + " -trying donator only feature"
          logger.logexit(logline)
          errfile.write("!donator " + host)
          # set the localip so next update will be made
          localip = "0.0.0.0"

        # looks like the homeip.net domain gives blank lines sometimes???
        elif results[idx]:
          logline = host + " " + results[idx] + " -unknown result line"
          logger.logexit(logline)
        else:
          logger.logexit("BLANK RESULT LINE!  Please forward the following output")
          logger.logexit("(and logfile if you have one) to kal@users.sourceforge.net:")
          logger.logexit("updatehosts:")
          logger.logexit(`updatehosts`)
          logger.logexit("results:")
          logger.logexit(`results`)
          continue

        idx = idx + 1

      if success and opt_execute:
        os.system (opt_execute)

    else:
      logger.logexit("Unrecognized result page in ipcheck.html.")
      
    #
    # write the update data to file
    #
    if localip:
      if opt_offline:
        datfile.setIP("1.0.0.0")
      else:
        datfile.setIP(localip)

      # hostnames == updatehosts in the current version 
      # but that may change in future versions of the client
      datfile.write(hostnames = hostnames)
      logger.logit("ipcheck.dat file updated.")

  elif errcode == 302:
    logger.logexit("302 Temporarily Moved result.  Something is wrong.")
    logger.logexit("Please send the ipcheck.html file and this message to")
    logger.logexit("kal@users.sourceforge.net")
    logger.logexit("=== 302 debug headers ===")
    logger.logexit(`headers.getplist()`)
    sys.exit(-1)


if __name__=="__main__":

  _main(sys.argv)


