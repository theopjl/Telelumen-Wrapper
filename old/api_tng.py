#########################################################
#                                                       #
#                      api_tng.py                       #
#                                                       #
# (c) 2020-2021 Telelumen LLC.  All rights reserved.    #
#                                                       #
# v4.00 - 20 March 2020     Full re-write  rda          #
# v4.10 - 5 August 2020     Port in UDP and LSO         #
# v4.11 - 31 January 2021   Add exception tracking      #
# v4.12 - 8 September 2021    Port to Python 3          #
#########################################################

import sys
import threading
import telnetlib
import socket
from datetime import datetime
import array as array
import struct
import json
import paho.mqtt.client as mqtt
import binascii
import copy
import time
import re
try:
    import netifaces
    NETIFACES_AVAILABLE = True
except ImportError:
    NETIFACES_AVAILABLE = False
    netifaces = None
from multiprocessing import Process

LOGFILE_BASE = 'api_debug'
DATEPART = datetime.now().strftime("-%Y%m%d-%H%M%S")


network_candidate_list = ['192.168.0.', '192.168.1.', '192.168.2.', '192.168.11.', '192.168.3.', '192.168.4.',
	'192.168.5.', '192.168.6.', '192.168.7.', '192.168.8.', '192.168.9.', '192.168.10.']
luminairePort = 57007
disconnectRequestPort = 57011

telnetObj = {}  # dictionary correlating ip address to socket
refused_list = []
# Set Luminaire Network to a class C network prefix on which the luminaires
# reside.  This will usually be the same network as the wireless router.
luminaireNetwork = '0.0.0.'
# The port number is fixed by the Luminaire firmware.  It can be changed
# by configuration message, but this is not recommended as it will break
# backward compatibility with older applications.

socket_list = {}  # dictionary correlating ip address to socket
sendTask = [0 for i in range(0, 256)]
seqtag = 0
db = None

def trace_on():
    db.trace_on()

def trace_off():
    db.trace_off()
    
def console_trace_off():
    db.console_trace_off()

def console_trace_on():
    db.console_trace_on()

def logit(msg):
    db.log_tag(msg)

class dbug:
    global debug
    def __init__ (self, fn, debug_state=False, console_state=False):
        self.trace = False            # Messages in logfile?
        self.console_debug = False  # Messages on STDOUT?
        self.logfile_name = fn
        #self.log_fh = open(self.logfile_name, 'w')
        db = self
        
    def trace_on(self):
        self.trace = True
    
    def trace_off(self):
        self.trace = False
        
    def console_trace_on(self):
        self.console_debug = True
    
    def console_trace_off(self):
        self.console_debug = False
    
    def get_timestamp (self):
        return datetime.now().strftime("%Y%m%d-%H%M%S: ")
        
    def log(self, level, msg):
        if false:   # self.trace:
            s = self.get_timestamp() + level + ':' + msg
            self.log_fh.write(s+'\n')
            if self.console_debug:
                print(s)
            s = sys.exc_info()
            self.log_fh.write(s+'\n')
            if self.console_debug:
                print(s)
            self.log_fh.flush()
        pass
        
        
    def log_tag (self, msg):
        try:
            self.log('TAG', msg)
        except:
            pass

    def log_exception(self, error_fn, msg):
        try:
            self.log('EXCEPTION in %s:%s', (error_fn, msg))
        except:
            pass
            
    def log_error(self, msg):
        try:
            self.log('ERROR', msg)
        except:
            pass

    def log_info(self, msg):
        try:
            self.log('INFO', msg)
        except:
            pass

    def log_warn(self, msg):
        try:
            self.log('WARN', msg)
        except:
            pass

##################################
#### Start internal functions ####
##################################

def get_timestamp():
    global db
    try:
        ts = time.time()
        tss = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ':'
        return tss
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.get_timestamp()', err)
        return ""

################## Basic Communications I/O ##################

TELNET_CONNECTION_TIMEOUT = 6.0

# Create a telnet connection with the device at the specified address & port
def openConnection(ip, portno):
    global db
    try:
        tn = None
        tn = telnetlib.Telnet(ip, portno, TELNET_CONNECTION_TIMEOUT)
        log_str = 'OK: openConnection(%s): returns %s' % (ip, str(tn))
        db.log_info(log_str)
        telnetObj[ip] = tn  # Remember our associated telnet object
        return 0  # Connection OK
    except socket.error as exc:
        if 'Connection refused' in str(exc):
            db.log_info('FAIL:CONNECTION REFUSED %s!' % ip)
            refused_list.append(ip)
        log_str = 'FAIL: openConnection(%s):%s' % (ip, str(exc))
        db.log_info(log_str)

    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.openConnection()', err)
        return -1  # Connection failed
    return -1  # Connection failed


# Open a luminaire at the legacy port # 57007
def openLuminaire(ip, port):
    global db
    try:
        rv = openConnection(ip, port)
        return rv
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.open_luminaire()', err)
        return -1


# Close the luminaire at the specified full IP address
def closeLuminaire(ip):
    global telnetObj
    global socket_list
    global sendTask
    global luminaire_list
    global luminaireTask
    global db

    try:
        telnetobj = telnetObj[ip]
        telnetobj.close()
        telnetObj.clear()
        socket_list.clear()
        sendTask = [0 for i in range(0, 256)]
        luminaireNetwork = '0.0.0.'
        luminaire_list = []
        luminaireTask = [0 for i in range(0, 256)]
        print("-> Connection closed for " + ip  + '\n')
        return 0
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.closeLuminaire()', err)
        print("-> Connection not closed for " + ip + '\n')
        return -1


# Given a list of luminaire full IP addresses, close all of them
def closeListIp(hostlist):
    global db
    try:
        for host_ip in hostlist:
            closeLuminaire(host_ip)
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.closeListIp()', err)


def closeList(lum):
    global db
    try :
        for l in lum :
            closeLuminaire(l.address)
    except :
        err = str(sys.exc_info())
        db.log_exception('api_tng.closeList(lums)', err)
        


# Get a standard luminaire reply, which always ends in (and does not otherwise
# contain) a semicolon:
def getReply(ip):
    global db
    global telnetObj
    try:
        telnetobj = telnetObj[ip]
        reply = telnetobj.read_until(b";").decode()
        info_tag = 'getReply(ip=%s):%s\n' % (ip, reply)
        db.log_info(info_tag)
        return reply
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.getReply()', err)
        try:
            errtag = 'getReply(ip=%s) exception' % (ip)
            log_error(errtag)
            return ""
        except:
            err = str(sys.exc_info())
            db.log_exception('api_tng.getReply()', err)
            return ""

# Get a standard luminaire reply, which always ends in (and does not otherwise
# contain) a semicolon:
def getReplyWithTimeout(ip, timeout):
    global db
    try:
        telnetobj = telnetObj[ip]
        reply = str(telnetobj.read_until(b";", timeout).decode())
        info_tag = 'getReplyWithTimeout(ip=%s, timeout=%s):%s' % (ip, str(timeout), reply)
        db.log_info(info_tag)
        return reply
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.getReplyWithTimeout()', err)
        try:
            errtag = 'getReplyWithTieout(ip=%s) exception' % (ip)
            log_info(errtag)
            return ""
        except:
            err = str(sys.exc_info())
            db.log_exception('api_tng.getReplyWithTimeout()', err)
            return ""

# Just send a message.  Don't wait for a reply. Don't get a reply.
# You can pair this with getReply() to get the equivalent of sendMessage()
def sendMessageRaw(ip, outMsg):
    global db
    global telnetObj
    try:
        telnetobj = telnetObj[ip]
        telnetobj.write((outMsg + '\r').encode())
        info_tag = 'sendMessageRaw(%s):\n\t%s' % (ip, outMsg)
        db.log_info(info_tag)
        return 0
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.sendMessageRaw()', err)
        try:
            errtag = 'sendMessageRaw(ip=%s,msg=%s)' % (ip, outMsg)
            log_error(errtag)
            return -1
        except:
            err = str(sys.exc_info())
            db.log_exception('api_tng.sendMessageRaw()', err)
            return -1

# Send a message and wait for and return the reply from the luminaire
def sendMessage(ip, outMsg):
    sendMessageRaw(ip, outMsg)
    return getReply(ip)

def sendMessageRetries(ip, retries, outMsg):
    global db
    
    try:
        for count in range(0, retries):
            if (count > 0):
                info_tag = 'sendMessageRetries: Retrying - retry #%d' % (count)
                db.log_info(info_tag)
            result = sendMessage(ip, outMsg)
            if (result):
                return result
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.sendMessageRetries()', err)
    return ""

# Note that due to possible stateful sequences of messages, and unexpected
# side-effects of mindlessly repeating a command without considering context,
# this function only retries a command until SOME response is returned.
# If the luminaires are in different states, it might be "normal" to have
# some "complain" with an error code but not others, and retrying a failure
# with no context or knowledge of state in a general function is not wise,
# so we concentrate on making sure the message is delivered and responded to,
# and let higher-level logic decide if further action is required on units that
# respond but return a non-zero (error) return value.
def sendMessageParallel(hostip_list, outmsg, tries=3, timeout=2.0):
    global db
    
    try:
        #####################################################################################
        # can accept list of messages, one per luminaire, or one message to be sent to all
        #
        if isinstance(hostip_list, str):
            hostip_list = [hostip_list]

        if isinstance(outmsg, str):
            outmsg = [outmsg] * len(hostip_list)
        else:
            assert len(outmsg) == len(hostip_list)
        host_msg_dic = dict(list(zip(hostip_list, outmsg)))
        #
        #####################################################################################

        if isinstance(hostip_list, list) == False:
            return -1, [], []  # Garbage in, garbage out.  Must be a list

        try_count = 0
        cmdreply_dict = dict(list(zip(hostip_list, ['' for i in range(0, len(hostip_list))])))
        worklist = [k for k in list(cmdreply_dict.keys()) if ';' not in cmdreply_dict[k]]

        while try_count < tries and len(worklist) > 0:
            try_count = try_count + 1
            # Make a list of all luminaires that haven't yet responded in worklist
            try:
                for ip in worklist:
                    sendMessageRaw(ip, host_msg_dic[ip])
            except:
                err = str(sys.exc_info())
                db.log_exception('api_tng.SendMessageParallel()', err)
                errtag = 'sendMessageParallel(ips=%s,msg=%s,tries=%d,timeout=%f):%s' % \
                     (str(worklist), outmsg, tries, timeout, sys.exc_info()[0])
                log_error(errtag)

            giveup_time = time.time() + timeout
            # Accumulate reponses for the required time
            while time.time() < giveup_time:
                try:
                    for ip in worklist:
                        telnetobj = telnetObj[ip]
                        reply = ''
                        try:
                            reply = str(telnetobj.read_eager())
                            if reply != '':
                                cmdreply_dict[ip] = cmdreply_dict[ip] + reply
                        except:
                            err = str(sys.exc_info())
                            db.log_exception('api_tng.sendMessageParallel()', err)
                except:
                    errtag = 'api_tng.sendMessageParallel(ips=%s,msg=%s,tries=%d,timeout=%f):%s' % \
                         (str(worklist), outmsg, tries, timeout, sys.exc_info()[0])
                    log_error(errtag)
                    err = str(sys.exc_info())
                    db.log_exception('api_tng.sendMessageParallel()', err)

                worklist = [k for k in list(cmdreply_dict.keys()) if ';' not in cmdreply_dict[k]]
                for ip in hostip_list:
                    if ';' not in cmdreply_dict[ip]:
                        cmdreply_dict[ip] = ''

                if len(worklist) == 0:
                    break
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.sendMessageParallel()', err)
        
    return worklist, [(addr, cmdreply_dict[addr]) for addr in hostip_list]

def get_all_drive_levels_raw (ip):
    global db
    try:
        drive_vector = []
        st = generic_message_str_reply(ip, 'PS?')
        rep = st.split(',')

        for ndl in rep:
            drive_vector.append(int(ndl, 16))
    except:
        drive_vector = []
        err = str(sys.exc_info())
        db.log_exception('api_tng.get_all_drive_levels_raw()', err)
    return drive_vector

def get_all_drive_levels (ip):
    global db
    try:
        drive_vector = []
        dv = get_all_drive_levels_raw(ip)
        if len(dv) < 1:
            return []
        for ndl in dv:
            drive_vector.append(float(ndl)/65535.0)
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.get_all_drive_levels()', err)
    return drive_vector

################## Discovery Stuff ##################

maxDiscoverTime = 3.6
luminaireTask = [0 for i in range(0, 256)]
luminaire_list = []

# Return the network part and trailing dot if network may contain Penta/Octa,
# else return None
def is_rfc822_network(net):
    global db
    try:
        # Look for a canonical ip address
        aa = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", net)
        if aa:
            ip_candidate = aa.group()
            if (ip_candidate.startswith('192.168.')):
                ab = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.", net)
                ip_net = str(ab.group())
                return ip_net
        return None
    except:
        err = str(sys.exc_info())
        s = 'api_tng.is_rfc822_network(%s)' % net
        db.log_exception(s, err)
        return None

def find_luminaire_network():
    return network_candidate_list

def __get_serial_number(ip):
    global db
    try:
        # res = ll_command_reply(ip, 'NS')
        res = sendMessage(ip, 'NS')
        return res
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.__get_serial_number()', err)
        return False

def addLuminaire(ip):
    global db
    try:
        if (ip not in luminaire_list):
            luminaire_list.append(ip)
            luminaire_list.sort()
            msg_tag = "addLuminaire(ip=%s)" % ip
            db.log_info(msg_tag)
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.addLuminaire()', err)
        return None

def removeLuminaire(ip):
    global db
    try:
        if (ip in luminaire_list):
            luminaire_list.remove(ip)
            info_tag = "removing Luminaire(%s)" % (ip)
            db.log_info(info_tag)
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.removeLuminaire()', err)
        return None

def __discoveryPoll(address, port):
    global luminaire_network
    global db
    try:
        ipAddy = luminaireNetwork + str(address)
        if (openLuminaire(ipAddy, port) == 0):
            try:
                sn = __get_serial_number(ipAddy)
                if (sn != False):
                    addLuminaire(ipAddy)
                else:
                    removeLuminaire(ipAddy)
            except:
                err = str(sys.exc_info())
                db.log_exception('api_tng.__discoveryPoll()', err)
                removeLuminaire(ipAddy)
        else:
            removeLuminaire(ipAddy)
        return 0
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.__discoveryPoll()', err)
        return -1

###### discover() returns a list of all IP addresses associated with a luminaire.
###### Call this function to find out what luminaires are active on the network.
###### Note that it may take up to a minute after a luminaire is first powered
###### on before it will have successfully connected to the network. 20 seconds
###### is a more typical value.
# Note [start, end) not [start, end]
def is_alive(start_task, end_task):
    global db
    try:
        for i in range(start_task, end_task):
            if (luminaireTask[i].isAlive()):
                return True
        return False
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.is_alive()', err)
        return False



def __discover_one(net, port):
    global luminaireNetwork
    global luminaire_list
    global db
    
    try:
        luminaire_list = []
        refused_list = []

        luminaireNetwork = net
        info_tag = 'discover_one(net=%s): Discovering Luminaires on network ' % luminaireNetwork
        db.log_info(info_tag)

        ### IP = 192.168.x.2 ... 192.168.x.127 inclusive
        # Task# 2..127 inclusive = range(2,128)
        lower_tid = 2
        upper_tid = 254
        ip_offset = 0
        db.log_info('discover_one(2..127):create threads!')
        for i in range(lower_tid, upper_tid):
            nextaddr = luminaireNetwork + str(i+ip_offset)
            luminaireTask[i] = threading.Thread(target=__discoveryPoll, args=(i+ip_offset, port), )
        db.log_info('discover_one():start threads!')
        for i in range(lower_tid, upper_tid):
            luminaireTask[i].start()

        db.log_info('discover_one(): isAlive() wait')

        while (is_alive(lower_tid, upper_tid)):
            time.sleep(1.0)

        db.log_info('discover_one(): isAlive() wait completed')
        ## End first block
     
        db.log_info('discover_one(): Join has completed: exiting')
        luminaire_list.sort()
        db.log_info('discover_one() returns: %s' % str(luminaire_list))
        return luminaire_list
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.__discover_one()', err)
        return luminaire_list


def __discover_all(override_net=None):
    global db
    try:
        if (override_net):
            db.log_info('Attempting discover on ' + override_net + ' only')
            db.log_info('discover(net=%s' % override_net)
            x = __discover_one(override_net, disconnectRequestPort)
            x = __discover_one(override_net, luminairePort)
            return x
        else:
            netlist = find_luminaire_network()
            db.log_info('find_luminaire_network() returns: %s' % str(netlist))
            for nn in netlist:
                lumlist = __discover_one(str(nn), disconnectRequestPort)
                lumlist = __discover_one(str(nn), luminairePort)
                if lumlist:
                    return lumlist  # If any luminaire found, return the list
        return []
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.__discover_all()', err)
        return []

############
# File I/O #
############

def read_script(input_filename):
    global db
    script = []

    try:
        n = open(input_filename, 'rb')
        lines = n.read()
        db.log_info('Opening input filename:%s' % input_filename)
        with open(input_filename, 'rb') as source:
            script = source.read()
            return script
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.read_script()', err)
        return -1


# Compute the XOR 32 of the supplied bytearray.
# It will be padded with 0's to a block size of 512
# to simplify calculations (because all file writes are 
# multiples of 512 anyway, the efficiency impact is minimal/zero.
def compute_xor32(dat):
    global db
    try:
        dl = len(dat)
        leftovers = dl % 512
        if leftovers:
            # Pad data with trailing zeroes, 
            # to make a tidy integer number of file blocks
            addin = 512 - leftovers
            # Here we add addin bytes of end zero padding
            dat = dat + (bytearray(addin))


        xorsum = array.array('L')  # Must be 32 bits
        nextxor = array.array('L')  # Must be 32 bits
        nextxor.append(0)
        xorsum.append(0)  # Start with empty LRC sum

        a = array.array('L')
        b = array.array('L')
        c = array.array('L')
        d = array.array('L')

        a.append(0)
        b.append(0)
        c.append(0)
        d.append(0)

        xorsum[0] = 0
        for i in range(0, dl, 4):
            try:
                a[0] = dat[i + 3]
                b[0] = dat[i + 2]
                c[0] = dat[i + 1]
                d[0] = dat[i]
            except:
                err = str(sys.exc_info())
                db.log_exception('api_tng.compute_xor32()', err)
                return -1
               
            nextxor[0] = (a[0] << 24) | (b[0] << 16) | (c[0] << 8) | d[0]
            xorsum[0] = xorsum[0] ^ nextxor[0]
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.compute_xor32()', err)
    
    return xorsum[0]


def send_block(ip, dat, reliable, lens):
    global db
    try:
        if (len(dat) < lens):
            addin = 512 - len(dat)
            dat = dat + (bytearray(addin))
            # print(len(dat))
            lens = 512
        if (reliable == True):
            lrc = compute_xor32(dat)
            cmd = 'WRITE %08X:' % lrc
        else:
            cmd = 'WRITE '


        for i in range(0, lens):
            cmd = cmd + '%02X' % dat[i]

        # print(cmd+'\n')
        result = sendMessageRetries(ip, 10, cmd)
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.send_block()', err)
    return result




def compute_file_lrc(fn):
    global db
    try:
        data = bytearray(read_script(fn))
        dl = len(data)
        if (dl < 1):
            print('Unable to open file or empty file! Aborting')
            return 0x0
        lrc = compute_xor32(data)
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.compute_file_lrc()', err)
        
    return lrc


def dehexify (s):
    hexlist=[]
    nxt = ''
    for i in range(0, len(s), 2):
        z = int(s[i:i+2], 16)
        hexlist.append(z)
    nxt = bytearray(hexlist)
    return nxt
        
# Receive using OPEN/READAT/LRC paradigm used by Penta and Octa,
# future products
RECEIVE_RETRIES = 10
def receive_file_octa(ip, luminaire_filename, filesys_filename):
    global db
    
    try:
        rxfile = bytearray(0)
        chksum = ''
        retries = 0
        cmd = 'OPEN %s' % luminaire_filename
        while (retries < RECEIVE_RETRIES):
            retries = retries + 1
            result = sendMessage(ip, cmd)

            if '00;' not in result:
                info_tag = "Unable to open file(%s)" % (luminaire_filename)
                db.log_info(info_tag)
                return -1

        result = '00;'
        index = 0
        blox = 0
        retries = 0
        while ('01;' not in result):
            file_sum = 1
            lrc = 0
            while (file_sum != lrc):
                cmd = 'READAT %d\r\n' % index
                # Point to the next data block now
                result = sendMessage(ip, cmd)

                if '00;' not in result:
                    break
                # print('block#', blox)
                blox = blox + 1
                block_data = result.split()
                nxt = bytearray(0)
                for b in block_data:
                    if b.endswith('00;'):
                        pass
                    elif b.startswith('='):
                        chksum = b.split(':')[1]
                    else:
                        w = dehexify(b)
                        nxt = nxt + w
                lrc_val = compute_xor32(nxt)
                lrc_from_cmd = int(chksum, 16)
                # print('LRC = %08X from_cmd=%08X index=%d len(nxt)=%d' % (lrc_val, lrc_from_cmd, index, len(nxt)))
                if (lrc_val == lrc_from_cmd):
                    rxfile = rxfile + nxt
                    index = index + 512

        try:
            with open(filesys_filename, 'wb') as wf:
                wf.write(rxfile)
        except:
            log_error("cannot write file %s" % filesys_filename)
            err = str(sys.exc_info())
            db.log_exception('receive_file_octa()', err)
            return -1
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.receive_file_octa()', err)
    return 0


def receive_file(ip, luminaire_filename, filesys_filename):
    global db
    
    try:
        rxfile = bytearray(0)
        chksum = ""

        cmd = 'OPEN %s' % luminaire_filename
        result = sendMessageRetries(ip, RECEIVE_RETRIES, cmd)

        if '00;' not in result:
            info_tag = "Unable to open file(%s)" % (luminaire_filename)
            db.log_info(info_tag)
            return -1

        result = '00;'
        index = 0

        while ('01;' not in result):
            file_sum = 1
            lrc = 0
            while (file_sum != lrc):
                cmd = 'READAT %d\r\n' % index
                # Point to the next data block now

                result = sendMessageRetries(ip, RECEIVE_RETRIES, cmd)
                if '00;' not in result:
                    break

                block_data = result.split()
                nxt = bytearray(0)
                for b in block_data:
                    if b.endswith('00;'):
                        pass
                    elif b.startswith('='):
                        chksum = b.split(':')
                    else:
                        nxt = nxt + binascii.unhexlify(b)

                lrc_val = compute_xor32(nxt)
                lrc = "%08X" % lrc_val
                file_sum = str(chksum[1])
                if lrc == file_sum:
                    rxfile = rxfile + nxt
                    index = index + 512

        try:
            with open(filesys_filename, 'wb') as wf:
                wf.write(rxfile)
        except:
            log_error("cannot write file %s" % filesys_filename)
            err = str(sys.exc_info())
            db.log_exception('api_tng.receive_octa()', err)
            return -1
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.receive_octa()', err)
        
    return 0


# Legacy Light Replicator file receive: OPEN/READ paradigm
def receive_file_lr(ip, luminaire_filename, filesys_filename):
    global db
    
    try:
        rxfile = ''
        cmd = 'OPEN %s' % luminaire_filename
        result = sendMessageRetries(ip, RECEIVE_RETRIES, cmd)

        if '00;' not in result:
            info_tag = "Unable to open file(%s)" % (luminaire_filename)
            db.log_info(info_tag)
            return -1

        nxt = ''
        result = '00;'
        while '00;' in result:
            # Point to the next data block now
            cmd = 'READ'
            result = sendMessageRetries(ip, RECEIVE_RETRIES, cmd)
            if '00;' in result:
                lines = result.split('\n')
                for s in lines:
                    pos = s.find(':')
                    if pos > 0:
                        s = s[pos + 1:-1].replace(' ', '')
                        nxt = nxt + binascii.unhexlify(s)

        try:
            with open(filesys_filename, 'wb') as wf:
                wf.write(nxt)
        except:
            log_error("cannot write file %s" % filesys_filename)
            err = str(sys.exc_info())
            db.log_exception('api_tng.receive_file_lr()', err)
            return -1
        
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.receive_file_lr()', err)

    return 0

def dump_hex(bytelist):
    global db
    
    try:
        for i in range(0, len(bytelist)):
            if i % 16 == 0:
                st = ('%08x' % i)+': ' + '%02X' % bytelist[i] + ' '
                j = 1
            else:
                st = st + '%02X' % bytelist[i] +' '
                j = j + 1
            if j == 16:
                print(st)
                j = 0
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.dump_hex()', err)

# Send file at inpath to Penta at ip address ip, using
# filename outfn.  Optionally, use LRC redundancy code to ensure reliable receipt.
# Light Replicator does not support LRC, so be sure to set reliable to False.
def legacy_send_file_lrc(ip, inpath, outfn, reliable=True, wait=True):
    global db
    
    try:
        try:
            data = bytearray(read_script(inpath))
        except:
            print('cannot read file')
            err = str(sys.exc_info())
            db.log_exception('legacy_send_file_lrc()', err)
            return -1

        if (isinstance(data, int)):
            return -1

        actual_file_length = len(data)
        # print('send_file; length = ', len(data))

        if (actual_file_length < 1):
            return -1

        leftover = actual_file_length % 512
        if (leftover > 0):
            block_file_length = actual_file_length + (512 - leftover)
            data = data + bytearray(bytearray(0) * (512 - leftover))
        else:
            block_file_length = actual_file_length
            
        # print('len(data) = ', len(data))
        cmd = 'CREATE '
        cmd = cmd + outfn + '\r\n'

        try:
            result = sendMessage(ip, cmd)
        except:
            err = str(sys.exc_info())
            db.log_exception('api_tng.legacy_send_file_lrc()', err)
            return -1

        if ('00;' not in result):
            return -1

        block_count = 0
        bytes_left = block_file_length
        sent_bytes = 0
        size = 0

        while (bytes_left > 0):
            if (bytes_left > 512):
                size = 512
            else:
                size = bytes_left

            while True:
                res = send_block(ip, data[512 * block_count:512 * block_count + size], reliable, size)
                if (res == ""):
                    pass

                if ('42;' in res) and (bytes_left >= 512):      # Invalid LRC - re-send
                    pass
                else:
                    break

            bytes_left = bytes_left - size
            sent_bytes = sent_bytes + size
            block_count = block_count + 1

        filelen = '%08x' % actual_file_length
        if (wait == True):
            cmd = 'CLOSEPAUSED,'
        else:
            cmd = 'CLOSE,'

        cmd = cmd + filelen + '\r\n'
        # print(cmd)

        try:
            result = sendMessageRetries(ip, 10, cmd)
            return 0
        except:
            err = str(sys.exc_info())
            db.log_exception('legacy_send_file_lrc()', err)
            return -1
    except:
        err = str(sys.exc_info())
        db.log_exception('legacy_send_file_lrc()', err)

def send_file_unreliable(ip, inpath, outfn):
    return legacy_send_file_lrc(ip, inpath, outfn, False, False)


def send_vectors_to_devices(devices, drive_level_vectors):
    global db
    
    try:
        for d in devices:
            assert isinstance(d, Device)
            assert d.lumtype in ['Octa', 'Penta']
        assert len(devices) == len(drive_level_vectors)
        messages = []
        for i in range(len(devices)):
            for level in drive_level_vectors[i]:
                assert level >= 0 and level <= 1.0
            messages.append('PS' + ''.join(['%04X' % round(level * (2 ** devices[i].config['Modulation']['PWMBits'] - 1))
                                            for level in drive_level_vectors[i]]))
        sendMessageParallel([d.ip for d in devices], messages)
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.send_vectors_to_devices()', err)
    return

###############################
# Power cycler/MQTT interface #
###############################

def on_message(client, userdata, msg):
    pass
    # print('ON MESSAGE: Topic=%s, Payload=%s' % (msg.topic, msg.payload))


class mqttMessage:
    DEFAULT_BROKER_PORT = 1883  # For now, unencrypted to minimize complexity
    global db
    def __init__(self, ip, port=DEFAULT_BROKER_PORT):
        try:
            self.client = mqtt.Client()
            self.res = self.client.connect(ip, port)
            self.client.on_message = on_message
            self.message_thread = threading.Thread(target=self.loop_forever, args=(), )
            self.message_thread.start()
        except:
            err = str(sys.exc_info())
            db.log_exception('mqttMessage::__init__()', err)

    def subscribe_message(self, topic, qos=1):
        try:
            self.client.subscribe(topic, qos)
        except:
            err = str(sys.exc_info())
            db.log_exception('mqttMessage::subscribe_message()', err)

    def publish_message(self, topic, payload):
        try:
            if self.res == 0:
                self.client.publish(topic, payload)
        except:
            err = str(sys.exc_info())
            db.log_exception('mqttMessage::publish_message()', err)


    def power_on(self, num):
        try:
            onstr = str(num) + ',' + 'on'
            self.publish_message('/power', onstr)
        except:
            err = str(sys.exc_info())
            db.log_exception('mqttMessage::power_on()', err)


    def power_off(self, num):
        try:
            offstr = str(num) + ',' + 'off'
            self.publish_message('/power', offstr)
        except:
            err = str(sys.exc_info())
            db.log_exception('mqttMessage::power_off()', err)


    # Handle messages as they come in, and send out messages as published.
    # A stand-alone thread
    def loop_forever(self):
        try:
            self.client.loop_forever()
        except:
            err = str(sys.exc_info())
            db.log_exception('mqttMessage::loop_forever()', err)


    def loop_start(self):
        try:
            self.client.loop_start()
        except:
            err = str(sys.exc_info())
            db.log_exception('mqttMessage::loop_start()', err)


    def loop_stop(self):
        try:
            self.client.loop_stop()
        except:
            err = str(sys.exc_info())
            db.log_exception('mqttMessage::loop_stop()', err)


##########################################################
# Basic network and discovery operations at start of use #
##########################################################

# Define our Class-C network address here.  Three octets, exactly, with or
# without a trailing dot:
# If the supplied address does not fit this pattern, or this function isn't
# called, then the default values are used from network_candidate_list
def set_network(ip_network):
    global network_candidate_list
    global db
    
    try:
        if ip_network.endswith('.'):
            ip_network = ip_network[0:-1]

        nl = ip_network.split('.')
        lynn = len(nl)
        if lynn == 3:
            network_candidate_list = ['.'.join(nl) + '.']
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.set_network()', err)


    return network_candidate_list

################################
#### End internal functions ####
################################

# UDPmsg: a UDP-based bidirectional communications class.  This is an alpha quality product with
# some important limitations:
# 1. Class C /24 networks only, for now.  To date that's all we've ever shipped anyhow but.
#
# 2. You either need to know the target luminaires' IP addresses a priori somehow, or you need to
#    do a api.discover() to find them.  In the api.discover() case, you create a connection
#    to each luminaire (and disrupt any prior connection-oriented traffic that might be ongoing
#    by another program or user.  If that side-effect is not desired, then another method
#    for remembering IP addresses of target luminaires should be used.
#
# 3. The first network activity must be using UDPmsg.sendto(ip).  This is because it performs
#    some post-socket-related initialization.  In the case where you only want to listen to
#    traffic, a "dummy" 'NS' can be sent to retreive a luminaire's electronic serial number,
#    because this command has no side effects except to create a command and response.
#
#  4. Subsequently, UDP responses may be received by UDPmsg.getfrom(), or messages can be
#     send to the most recently talked-to luminaire again without specifying target address with
#     USPmsg.send()
#

class UDPmsg:
    global db
    # Creating the object creates the socket but doesn't set any of the parameters
    # The user may create a new object per message, or create the object once and
    # continually re-use it.  Either usage style is OK.
    def __init__ (self, timeout=0.1, port=57000):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(timeout)
            self.LUMINAIRE_UDP_PORT = port
            self.MAX_PACKET_SIZE = 1400
            self.seqtag = 1
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::__init__()', err)


    # FIXME Eventually, generalize for at least 8-30 bits.  For now, class C only
    def get_subnet (self, ip, bits):
        try:
            subnet = None
            if bits == 24:
                s = ip.split('.')
                subnet = str(s[0]) + '.' + str(s[1]) + '.' + str(s[2]) # FIXME, only works for bits == 24
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::get_subnet()', err)
        return subnet

    # Getting our own IP address is actually non-trivial and
    # highly platform-dependent.  Expedience wins over style or future-proofness in this
    # particular method.  The approach here is to figure out what subnet we're
    # talking to luminaires on by the first three octets of self.dest_ip
    # (/24 subnet itself a bit of an assumption except we've always done this so far),
    # and traversing the list of all interfaces to find which has an ip address on that subnet.
    # FIXME as time permits
    def get_my_ip(self):
        try:
            # Try netifaces method if available
            if NETIFACES_AVAILABLE:
                subnet = self.get_subnet(self.dest_ip, 24)
                # Traverse all system network interfaces in search of something on that subnet
                for ni in netifaces.interfaces():
                    nd = netifaces.ifaddresses(ni)
                    for k in nd.keys():
                        lr = nd[k]
                        llr = lr[0]
                        if llr['addr'].startswith(subnet):
                            # print('my_ip = ', llr['addr'])
                            return llr['addr']
            else:
                # Fallback method using socket without netifaces
                # Create a UDP socket and connect to the destination to determine our source IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    # Connect to the destination (doesn't actually send data)
                    s.connect((self.dest_ip, self.dest_port))
                    my_ip = s.getsockname()[0]
                    return my_ip
                finally:
                    s.close()
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::get_my_ip()', err)
        return ''

    # In case you know better
    def set_my_ip(self, ip):
        try:
            self.source_ip = ip
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::set_my_ip()', err)


    def _print_parameters(self):
        try:
            print('UDP parameters')
            print('--------------')
            print('Sock:\t\t', self.sock)
            print('Source IP:\t\t', self.source_ip)
            print('Dest IP:\t\t', self.dest_ip)
            print('Source Port:\t\t', self.source_port)
            print('Dest Port:\t\t', self.dest_port)
            print('Seqtag:\t\t', self.seqtag)
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::_print_parameters()', err)

    def _set_tx_parameters(self, dest_ip):
        # Get the source port from the created tx socket
        try:
            self.dest_ip = dest_ip
            self.dest_port = self.LUMINAIRE_UDP_PORT
            self.source_ip = None
            self.source_port = None
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::_set_tx_parameters()', err)
        return
        
    def _print_packet(self, data):
        try:
            bc = 0
            for i in range(0, len(data)):
                if ((i % 16) == 0):
                    print("\n%04x:" % i,)
                sys.stdout.write(' %02X' % int(data[i]))
            print('\n\n\n')
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::print_packet()', err)


    # Format the packet and encapsulate the ASCII CLI portion in the payload
    def _build_packet(self, msg):
        try:
            # Create the next sequence tag
            stag = next_seqtag()
            stagh = (stag >> 8) & 0xFF
            stagl = (stag & 0xFF)
            payload_bytes = len(msg)
            paylenhi = (payload_bytes >> 8) & 0xFF
            paylenlo = (payload_bytes & 0xFF)

            pack = chr(0xAE)+chr(0xEC)  # Message type tag: UDP command = 0xAEEC
            pack = pack + chr(stagh)+chr(stagl)+chr(0)+chr(0)+chr(0)+chr(0)
            pack = pack + chr(paylenhi)+chr(paylenlo)+msg
            # print('********************************')
            # self.print_packet(pack)
            # print('********************************')
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::build_packet()', err)
        return pack

    def _build_packet_raw(self, msg):
        # Create the next sequence tag
        try:
            pack = bytearray(len(msg)+10)	# FIXME sometime soonish should not be needed
            # print('build_packet_raw()')
            pack[0:10] = msg[0:10]
            pack[10:20] = msg[0:10]
            pack[20:] = msg[10:]
            # print('end build_packet_raw()')
            # self._print_packet(pack)
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::_build_packet_raw()', err)
        return pack

    # Send a new message to specified IP port and address parameters
    # This is ALWAYS THE FIRST NETWORK I/O IN ANY PROGRAM, because it performs some set-up
    # as a side-effect.  Various stateful properties of sockets appear to require it.
    # MUST use sendto() at least once for the first message, to set the IP parameters up
    # Afterward, this or send() can be used.  Also, you must call sendto() before attempting
    # to receive for the first time, as well.  In that case a dummy 'NS' message can be sent without
    # side-effect (except a reply containing the serial number)
    def sendto(self, dst_ip, msg):
        try:
            self._set_tx_parameters(dst_ip)
            message = self._build_packet(msg)
            self.sock.sendto(message, (self.dest_ip, self.dest_port))
            self.source_port = self.sock.getsockname()[1]  # For some reason, exception if done earlier
            self.source_ip = self.get_my_ip()
            #self._print_parameters()
        except:
            err = str(sys.exc_info())
            db.log_exception('udpMessage::sendto()', err)
            return -1
        return 0

 
    # Send a new message to specified IP port and address parameters
    # This is ALWAYS THE FIRST NETWORK I/O IN ANY PROGRAM, because it performs some set-up
    # as a side-effect.  Various stateful properties of sockets appear to require it.
    # MUST use sendto() at least once for the first message, to set the IP parameters up
    # Afterward, this or send() can be used.  Also, you must call sendto() before attempting
    # to receive for the first time, as well.  In that case a dummy 'NS' message can be sent without
    # side-effect (except a reply containing the serial number)
    def sendtoraw(self, dst_ip, msg):
        try:
            self._set_tx_parameters(dst_ip)
            message = self._build_packet_raw(msg)
            self.sock.sendto(message, (self.dest_ip, self.dest_port))
            self.source_port = self.sock.getsockname()[1]  # For some reason, exception if done earlier
            self.source_ip = self.get_my_ip()
            #self._print_parameters()
        except:
            err = str(sys.exc_info())
            db.log_exception('UDPMessage::sendtoraw()', err)
            return -1
        return 0

    # Send a new message to previously-established target addresses and ports
    def send(self, msg):
        try:
            message = self._build_packet(msg)
            self.sock.sendto(message, (self.dest_ip, self.dest_port))
        except:
            err = str(sys.exc_info())
            db.log_exception('udpMessage::send()', err)
            return -1
        return 0

    def sendbinary(self, msg):
        try:
            message = self._build_packet_raw(msg)
            self.sock.sendto(message, (self.dest_ip, self.dest_port))
        except:
            err = str(sys.exc_info())
            db.log_exception('udpMessage::sendbinary()', err)
            return -1
        return 0

    def send_lso(self, msg):
        try:
            message = self._build_packet_raw(msg)
            self.sock.sendto(message, (self.dest_ip, self.dest_port))
        except:
            err = str(sys.exc_info())
            db.log_exception('udpMessage::send_lso()', err)
            return -1
        return 0

    # For receiving from wherever we last transmitted to
    def getfrom(self):
        try:
            data, src_addr_and_port = self.sock.recvfrom(self.MAX_PACKET_SIZE)
            return data[10:], src_addr_and_port   # Discard the 10 leading payload bytes (they're transport overhead)
        except:
            err = str(sys.exc_info())
            db.log_exception('udpMessage::getfrom()', err)
            return [],[]

    # Receive from wherever we last transmitted to.  Return overhead bytes (seqtag, msgtype, etc.) as well as payload
    def getfrom_raw(self):
        try:
            data, src_addr_and_port = self.sock.recvfrom(self.MAX_PACKET_SIZE)
            return data, src_addr_and_port   # Discard the 10 leading payload bytes (they're transport overhead)
        except:
            err = str(sys.exc_info())
            db.log_exception('udpMessage::getfrom_raw()', err)
            return [],[]


# Make sure each outgoing message has a unique tag to allow correlation of reply to command
def next_seqtag():
    global seqtag
    global db
    
    try: 
        seqtag = seqtag + 1
        if seqtag > 65535:
            seqtag = 1
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.next_seqtag()', err)
    return seqtag

######################################### Beginning of API-TNG #########################################
## Customers start using the interface from here and downward

class Luminaire:
    global db
    def __init__(self, link_address, link_type='ip'):
        try:
            '''
                Current valid link types are 'ether'
                Ether is given by a dot-notation string e.g. '192.168.2.160'
                DMX is specified by an integer universe channel number, 0 to 512*number of channels
             '''
            assert type(link_type) == str
            if link_type == 'dmx':
                assert type(link_address) == int
            else:
                assert type(link_address) == str

            self.link = link_type
            self.address = link_address
            self.fw_ver = None
            self.electronic_serial_number = None
            self.luminaire_serial_number = None
            self.lumtype = None
            self.channel_map = None
            self.chipset = None
            self.dir = None
            self.free = 0
            self.get_version()
            self.get_electronic_serial_number()
            self.read_type()
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::__init__()', err)

    def send_message(self, cmd):
        try:
            # print('send_message(%s)' % cmd)
            retmsg = sendMessageRetries(self.address, 3, cmd)
            msg = retmsg.replace('\r\n', '\n')
            msg_ret_code = msg.split('\n')[-1][0:-1]
            msg = msg[0:-3] # Omit terminal status code
            try:
                self.last_message_status = int(msg_ret_code)
            except:
                self.last_message_status = 11  # No status from luminaire
                err = str(sys.exc_info())
                db.log_exception('Luminaire::send_message()', err)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::send_message()', err)
        return msg
    
    def send_message_raw(self, cmd):
        try:
            sendMessageRaw(self.address, cmd)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::send_message_raw()', err)


    def get_last_message_status(self):
        try:
            return self.last_message_status
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_last_message_status()', err)
            return -1

    def read_type(self):
        try:
            retval = sendMessage(self.address, 'ID')
            if retval == "":
                print('telnetlib.Telnet object error')
            # if not a communication error, will return a string
            try:
                # LR does not have an 'ID' command.  This returns power data
                # instead.  Beause it's legacy firmware, we'll deduce it's a
                # Light replicator.  No future product will fail the 'ID' command.
                if 'mV' in retval and 'mA' in retval:
                    lumtype = 'LightReplicator'
                    self.lumtype = lumtype
                    return

                lumtype = retval.split('00;')[0].strip().split(': ')[0]
            except:
                err = str(sys.exc_info())
                db.log_exception('Luminaire::read_type()', err)
            self.lumtype = lumtype
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::read_type()', err)
        return

    def reset(self):
        try:
            self.send_message('RESET')
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::reset()', err)
            
        return self.last_message_status

    def get_version(self):
        try:
            msg = self.send_message('VER')
            retval = self.get_last_message_status()
            if retval != 0:
                print('Unexpected return value: %s' % retval)
            msg = msg.replace('\r\n', '').replace('\n', '')
            self.fw_ver = msg
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_version()', err)
        return self.fw_ver

    def get_electronic_serial_number(self):
        try:
            msg = self.send_message('NS')
            retval = self.get_last_message_status()
            if retval:
                print('Unexpected return value: %s' % retval)
            msg = msg.replace('\r\n', '').replace('\n', '')
            self.electronic_serial_number = msg
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_electronic_serial_number()', err)
        return self.electronic_serial_number

    def get_ip_extras(self):
        try:
            msg = self.send_message('GETIP')
            retval = self.get_last_message_status()
            if retval:
                print('Unexpected return value: %s' % retval)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_mac()', err)
        return msg
        
    def get_mac(self):
        try:
            msg = self.send_message('GETIP')
            retval = self.get_last_message_status()
            if retval:
                print('Unexpected return value: %s' % retval)
            msg = msg.split()
            return msg[-1]
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_mac()', err)
        return self.electronic_serial_number
        
        
    def get_luminaire_serial_number(self):
        try:
            lumtype = self.lumtype
            if 'LightReplicator' in lumtype:
                return self.get_electronic_serial_number()

            msg = self.send_message('GETSERNO')
            retval = self.get_last_message_status()
            if retval != 0:
                print('Unexpected return value: %s' % retval)
            msg = msg.replace('\r\n', '').replace('\n', '')
            self.luminaire_serial_number = msg
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_luminaire_serial_number()', err)
        return self.luminaire_serial_number

    def get_channel_map(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                cmd = 'MR'
            else:
                cmd = 'MAP-GET'
            msg = self.send_message(cmd)
            retval = self.last_message_status
            if retval:
                db.log_error('Unexpected return value: %s' % retval)
            msg = msg.replace('\r\n', '').replace('\n', '')
            pos = msg.find('Channel map:')
            if (pos >= 0):
                msg = msg[pos+12:]
            self.channel_map = msg
        except:
            err = str(sys.exc_info())
            db.log_exception('get_channel_map()', err)

        return self.channel_map

    def get_chipset(self):
        try:
            lumtype = self.lumtype

            if 'LightReplicator' in lumtype:
                return 'Unsupported feature on Light Replicator'
            msg = self.send_message('IYAM')
            retval = self.get_last_message_status()
            if retval:
                db.log_error('Unexpected return value: %s' % retval)
            msg = msg.replace('\r\n', '').replace('\n', '')
            self.chipset = msg
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_chipset()', err)
            
        return self.chipset

    def get_temperature(self):
        try:
            lumtype = self.lumtype

            if 'LightReplicator' in lumtype:
                return "Unsupported feature on Light Replicator"
            msg = self.send_message('TEMPC')
            retval = self.last_message_status
            if retval != 0:
                print('Unexpected return value: %s' % retval)
            msg = msg.replace('\r\n', '').replace('\n', '')
            pos = msg.find('Temp(C): ')
            if (pos >= 0):
                msg = msg[pos+9:]
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_temperature()', err)
        return msg

    def get_ip_address(self):
        try:
            return self.address
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_ip_address()', err)
            return '0.0.0.0'

    def get_ip(self):
        return self.get_ip_address()
    
    def get_luminaire_type(self):
        try:
            return self.lumtype
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_luminaire_type()', err)
            return 0
            
    def get_uptime(self):
        try:
            lumtype = self.lumtype
            if 'LightReplicator' in lumtype:
                return "Unsupported feature on Light replicator"
            msg = self.send_message('UPTIME')
            retval = self.get_last_message_status()
            if retval:
                db.log_error('Unexpected return value: %s' % retval)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_uptime()', err)
        return msg

    def get_directory(self):
        try:
            msg = self.send_message('DIR')
            retval = self.get_last_message_status()
            if retval:
                db.log_error('Unexpected return value: %s' % retval)
            lumtype = self.lumtype
       
            if 'LightReplicator' in lumtype:
                lines = msg.split('\n')
                self.dir = []
                for line in lines:
                    j = line.find('`')
                    if j > 0:
                        self.dir.append(line[0:j])
                return self.dir
            else:
                self.dir = msg.split('\n')[1:-3]
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_directory()', err)[1:-3]
        return self.dir
        

    def get_used_blocks(self):
        try:
            msg = self.send_message('DIR')
            retval = self.get_last_message_status()
            free_line = msg.split('\n')[-2]
            used = free_line.split()[0]
            in_use = int(used)
           
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_free_blocks()', err)
        return in_use

    def get_free_blocks(self):
        return 2029 - self.get_used_blocks()
    
    def get_lrc(self, filename):
        try:
            '''
                Return the LRC associated with the named file.  Required for mandatory data integrity check for f/w upgrade
            '''
            lumtype = self.lumtype
            if 'LightReplicator' in lumtype:
                return 'Unsupported feature on Light Replicator'
            cmd = 'LRC ' + filename
            msg = self.send_message(cmd)
            retval = self.get_last_message_status()
            if retval:
                db.log_error('Unexpected return value: %s' % retval)
            msg = msg.replace('\r\n', '').replace('\n', '')
            pos = msg.find('LRC:', 0, -1)
            if pos >= 0:
                return int(msg[4+pos:-1], 16)
            else:
                return 0
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_lrc()', err)
        return 0

    def receive_file(self, luminaire_filename, filesys_filename):
        '''
            Receive a file from the luminaire into local drive at path+filename filesys_filename
        '''
        try:
            lumtype = self.lumtype
            
            if 'LightReplicator' in lumtype:
                self.last_message_status = receive_file_lr(self.address, luminaire_filename, filesys_filename)
            else:
                self.last_message_status = receive_file_octa(self.address, luminaire_filename, filesys_filename)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::receive_file()', err)
            
        return self.last_message_status

    def send_file(self, inpath, outfn, idle_after_load=True):
        '''
            Send a file to the luminaire.  No path info in outfn, but inpath must locate the source on hard drive
        '''
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                lrc = False
                idle_after_load = False     # Not supported in LR
            else:
                lrc = True
            self.last_message_status = legacy_send_file_lrc(self.address, inpath, outfn, lrc, idle_after_load)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::send_file()', err)

        return self.last_message_status

    def delete(self, filename):
        try:
            lumtype = self.lumtype
       
            if 'LightReplicator' in lumtype:
                self.send_message('ERASE ' + filename)
                # For consistency with Octa/Penta, return 9 for file not found
                if self.last_message_status == 1:
                    self.last_message_status = 9
            else:
                self.send_message('DELETE ' + filename)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::delete()', err)
            
        return self.last_message_status

    def format(self):
        try:
            '''
                Non-reversible file system format.  Be sure you really want to do this.
                It will take a couple minutes to complete, so you may want to do this in a thread or task
            '''
            self.MAX_FORMAT_TIME = 400
            sendMessageRaw(self.address, 'FORMAT')
            getReplyWithTimeout(self.address, self.MAX_FORMAT_TIME)
        except:
            err = str(sys.exc_info())
            print(err)
            db.log_exception('Luminaire::format()', err)
        return 0

    def get_current_script(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                return 'Unsupported feature on Light Replicator'
            self.send_message('SYNC')
            msg = self.send_message('CURRENT')
            if self.last_message_status:
                db.log_error('Unexpected return value: %s' % self.last_message_status)
            msg = msg.replace('\r\n', '').replace('\n', '')
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_current_script()', err)
        return msg

    def play_first_script(self):
        try:
            lumtype = self.lumtype

            if 'LightReplicator' in lumtype:
                self.dir = self.get_directory()
                self.reset()    # Can only get to built-in script via reset, not name
                return 0
            else:
                self.send_message('SYNC')
                msg = self.send_message('FIRST')
                msg = msg.replace('\r\n', '').replace('\n', '')
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::play_first_script()', err)
        return self.last_message_status

    def play_last_script(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                self.dir = self.get_directory()
                return self.play(self.dir[-1])
            else:
                self.send_message('SYNC')
                msg = self.send_message('LAST')
                msg = msg.replace('\r\n', '').replace('\n', '')
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::play_last_script()', err)
        return self.last_message_status

    def play_next_script(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                cmd = '+'
            else:
                self.send_message('SYNC')
                cmd = 'NEXT'
            self.send_message(cmd)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminire::play_next_sript()', err)

        return self.last_message_status

    def play_previous_script(self):
        try:
            lumtype = self.lumtype

            if 'LightReplicator' in lumtype:
                cmd = '-'
            else:
                self.send_message('SYNC')
                cmd = 'PREV'

            self.send_message(cmd)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::play_previous_script()', err)
            
        return self.last_message_status

    def play(self, filename, wait=False):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                cmd = 'SETPAT=' + str(filename)
                self.send_message(cmd)
            else:
                if (len(filename) == 0):
                    cmd = 'PLAY'
                else:
                    if (wait):
                        cmd = 'PLAYPAUSED ' + str(filename)
                    else:
                        cmd = 'PLAY ' + str(filename)
                self.send_message(cmd)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::play()', err)
            
        return self.last_message_status

    def pause(self):
        try:
            lumtype = self.lumtype
            if 'LightReplicator' in lumtype:
                cmd = 'Q5'
            else:
                cmd = 'PAUSE'

            self.send_message(cmd)
        except:
            err = str(sys.exc_info())
            db.log_exception('pause()', err)
            
        return self.last_message_status

    def resume(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                self.send_message('Q2')
            else:
                self.send_message('RESUME')
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::resume()', err)
        return self.last_message_status

    def stop(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                self.send_message('Q8')
                self.send_message('B')  # Go dark to be consistent with Octa
            else:
                self.send_message('STOP')
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::stop()', err)
        return self.last_message_status

    def go_dark(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                return self.send_message('B')
            self.send_message('DARK')
            retval = self.last_message_status
            print(retval)
            if retval:
                db.log_error('Unexpected return value: %s' % retval)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::go_dark()', err)
        return retval
        
#### Streaming functions
    def get_stream_info(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                return ""
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_stream_info()', err)
        return self.send_message('STREAM-INFO')
        
    def get_stream_channel(self):
        try:
            chan = 0
            data = self.get_stream_info()

            d = data.split('\n')
            for line in d:
                amatch = re.match('Program stream:', line)
                if amatch:
                    chan = int(line.split(' ')[2])
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_stream_channel()', err)
        return chan
        
    def get_stream_enabled(self):
        try:
            chan = self.get_stream_channel()
            if (chan == 0):
                return False
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_stream_enabled()', err)
            return False
        return True

    def get_stream_leader(self):
        try:
            leader = False
            data = self.get_stream_info()

            d = data.split('\n')
            for line in d:
                amatch = re.match('Stream Leader:', line)
                if amatch:
                    leader = line.split(' ')[2]

            if 'TRUE' in leader:
                return True
        
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_stream_leader()', err)
            return False
        return False

        
    def stream_join(self, channel):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype or channel < 1 or channel > 255:
                return True	        # Error condition
                self.send_message('STREAM-JOIN %d' % channel)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::stream_join()', err)
            return True
        return Fale

    def stream_quit(self):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                return True	        # Error condition
            self.send_message('STREAM-QUIT')
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::stream_quit()', err)
            return True
        return False
        
    def stream_leader(self, leader):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                return True	        # Error condition
            
            if leader:
                self.send_message("STREAM-LEADER TRUE")
            else:
                self.send_message("STREAM-LEADER FALSE")
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::stream_leader()', err)
            return True
        return False

#### Drive level functions
    def get_drive_levels_raw(self):
        try:
            msg = self.send_message('PS?')
            retval = self.last_message_status
            if retval:
                db.log_error('Unexpected return value: %s' % retval)
            msg = msg.replace('\r\n', '').replace('\n', '')
            hexavec = msg.split(',')
            vec = [int(hexavec[i], 16) for i in range(len(hexavec))]
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::get_drive_levels_raw()', err)
        return vec

    def get_drive_levels(self):
        '''
            Return a vector of values from 0.0 to 1.0 representing each channel's current drive level
        '''
        vec = self.get_drive_levels_raw()
        try:
            lumtype = self.lumtype
        except:
            err = str(sys.exc_info())
            db.log_exception('get_drive_levels()', err)
            
        if 'LightReplicator' in lumtype:
            nvec = []
            try:
                for i in range(0,len(vec), 2):
                    pwm = vec[i]
                    am = vec[i+1]
                    intensity = float(pwm*am) / 4128705.0
                    nvec.append(intensity)
            except:
                err = str(sys.exc_info())
                db.log_exception('get_drive_levels()', err)
                pass
            return nvec
        else:
            return [vec[i]/65535.0 for i in range(len(vec))]

    def set_drive_levels_raw(self, drive_vector):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                # 64 values : alternating PWM, AM pairs
                if (len(drive_vector) != 64):
                    return -1
                cmd = 'PA'
                for i in range(0, len(drive_vector), 2):
                    pwm = drive_vector[i]
                    am = drive_vector[i+1]
                    cmd += '%04X%02X' % (pwm, am)
                self.send_message(cmd)
                return self.last_message_status
            else:
                cmd = 'PS'
                for vec in drive_vector:
                    assert vec >= 0
                    assert vec < 65536
                    cmd += '%04X' % vec
                self.send_message(cmd)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::set_drive_levels_raw()', err)
        return self.last_message_status

    def set_drive_levels(self, drive_vector_fractional):
        try:
            lumtype = self.lumtype
        
            if 'LightReplicator' in lumtype:
                cmd = 'PA'
                for vec in drive_vector_fractional:
                    pwm, am = self.__pwm_am_from_drive_level(vec)
                    cmd += '%04X%02X' % (pwm, am)
                self.send_message(cmd)
                return self.last_message_status
            else:
                drive_levels_raw = [int(drive_vector_fractional[i]*65535) for i in range(len(drive_vector_fractional))]
                return self.set_drive_levels_raw(drive_levels_raw)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::set_drive_levels()', err)
            return -1

    def set_drive_level(self, channel, level):
        try:
            lumtype = self.lumtype

            if 'LightReplicator' in lumtype:
                pwm, am = self.__pwm_am_from_drive_level(level)
                msg = 'PC%02d%04X%02X\r\n' % (channel, pwm, am)
            else:
                msg = 'P%02d%04X' % (channel, int(level*65535))
            self.send_message(msg)
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::set_drive_level()', err)
        return self.last_message_status

    # RDA: Directly from ancient lore (algorithm in C# written in 2008 or so)
    def __pwm_am_from_drive_level(self, intensity):
        try:
            tol = 1E-4
            am_bits = 6
            pwm_bits = 16
            am_min = 4

            am_max = (2 ** am_bits) - 1
            pwm_max = (2 ** pwm_bits) - 1

            fam = float(am_max) * intensity
            iam = int(fam)

            if (fam > iam):
                if ((fam - iam) > tol):
                    iam = iam + 1
                if (iam > am_max):
                    iam = 63
            elif (iam > fam):
                if ((iam - fam) > tol):
                    iam = iam + 1
                if (iam > am_max):
                    iam = am_max

            if (iam < am_min):
                iam = am_min

            # 4 <= iam <= 63
            pwm = int(fam * float(pwm_max) / float(iam))
        except:
            err = str(sys.exc_info())
            db.log_exception('Luminaire::__pwm_am_from_drive_level()', err)
        return pwm, iam

def discover(override_net=None):
    global db
    '''
        This is the key and first function to call:  api_tng.discover() or api.discover if you use
        import api_tng as api
    '''
    try:
        luminaire_obj = []
        if override_net:
            # Allow trailing dot, required for internal functions, to be optional if address is specified.
            if override_net.count('.') == 2:
                override_net += '.'
        ip_list = __discover_all(override_net)
        for ip in ip_list:
            luminaire_obj.append(Luminaire(ip, 'ether'))
    except:
        err = str(sys.exc_info())
        db.log_exception('api_tng.discover()', err)
        
    return luminaire_obj[:]


db = dbug(LOGFILE_BASE + DATEPART + '.log')


