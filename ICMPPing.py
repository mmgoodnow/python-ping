# All needed modules have been imported here
from socket import *
import os
import sys
import struct
import time
import select
import binascii  

# Define how many pings will be sent
ICMP_ECHO_REQUEST = 8		

# Checksum function is complete and can be used directly
def checksum(string): 
	csum = 0
	countTo = (len(string) // 2) * 2  
	count = 0

	while count < countTo:
		thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
		csum = csum + thisVal 
		csum = csum & 0xffffffff  
		count = count + 2
	
	if countTo < len(string):
		csum = csum + ord(string[len(string) - 1])
		csum = csum & 0xffffffff 
	
	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff 
	answer = answer >> 8 | (answer << 8 & 0xff00)
	return answer 
	
def receiveOnePing(mySocket, ID, timeout, destAddr):
	timeLeft = timeout
	
	while 1:
		# Receive a packet
		
		startedSelect = time.time()
		whatReady = select.select([mySocket], [], [], timeLeft)
		howLongInSelect = (time.time() - startedSelect)
		if whatReady[0] == []:
		    return
		
		# Fetch the ICMPHeader from the IP, and read information about TTL, 
		# icmpType, code, checksum, packetID and sequence
		
		timeReceived = time.time()
		recPacket, addr = mySocket.recvfrom(1024)
		TTL = ord(recPacket[8])
		icmpHeader = recPacket[20:28]
		type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
				
		# Print ping results
		
		if packetID == ID:
			byte = struct.calcsize("d") 
			timeSent = struct.unpack("d", recPacket[28:28 + byte])[0]
			return "Reply from %s: bytes=%d time=%fms TTL=%d" % (destAddr, len(recPacket), (timeReceived - timeSent)*1000, TTL)
		
		# Otherwise print timed out
		
		timeLeft = timeLeft - howLongInSelect
		if timeLeft <= 0:
			return "Request timed out."

def sendOnePing(mySocket, destAddr, ID):
	# Header is type (8), code (8), checksum (16), id (16), sequence (16)
	
	# Make a dummy header with a 0 checksum
	# and interpret strings as packed binary data
	
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, ID, 1)
	data = struct.pack("d", time.time())
	
	# Calculate the checksum on the data and the dummy header, using checksum function above
	
	chksum = checksum(header + data)
	
	# Get the right checksum according to the operating system you are using (e.g., linux, windows), and put in the header
	
	if sys.platform == 'darwin':
	    chksum = htons(chksum) & 0xffff
	    #Convert 16-bit integers from host to network byte order.
	else:
	    chksum = htons(chksum)
	    
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, chksum, ID, 1)
	
	# Construct ping packet by assembling header and data
	
	packet = header + data
	
	# Send out the ping packet
	mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str


# doOnePing function is complete and can be used directly		
def doOnePing(destAddr, timeout): 
	icmp = getprotobyname("icmp")

	# SOCK_RAW is a powerful socket type
	mySocket = socket(AF_INET, SOCK_RAW, icmp)
	
	myID = os.getpid() & 0xFFFF  # Return the current process i
	sendOnePing(mySocket, destAddr, myID)
	delay = receiveOnePing(mySocket, myID, timeout, destAddr)
	
	mySocket.close()
	return delay

# ping function is complete and can be used directly	
def ping(host, timeout=1):
	# timeout=1 means: If one second goes by without a reply from the server,
	# the client assumes that either the client's ping or the server's pong is lost
	dest = gethostbyname(host)
	print("Pinging " + dest + " using Python:")
	print("")
	# Send ping requests to a server separated by approximately one second
	while True :  
		delay = doOnePing(dest, timeout)
		print(delay)
		time.sleep(1)# one second
	return delay

# Specify the host to be pinged	
ping("google.com")

