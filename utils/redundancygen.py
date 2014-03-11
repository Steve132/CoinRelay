import lib.pybitcointools as pybtct
import lib.blockchain as bci
import sys
#This takes in a sub coinscript and outputs a 'redundant' version of it.

if(len(sys.argv) < 1):
	print """redundancygen.py <script.crs> <num_redundancies (integer)> <number_of_hours for a node to be 'offline (integer)>
	This script outputs to the current directory copies of the script as 'redunXXX.crs' for a redundant-safe version of the script.crs to be put on multiple nodes in case one goes down.
	
	It does so by taking a small amount of the balance from each script and sending it to one of a series of 'dead-mans' addresses every time a transaction is made.  Then, the next node checks all the previous 
	addresses to see if they have gone 'down' yet before running the script copy'.

	The private keys for the dead-mans addresses are output in plaintext to redun_keys.txt .  This file should be immediately deleted after the keys are imported into a wallet"""
	exit()

inputfile=open(sys.argv[1],'r').read()	#The script file to output
num_redundancies=int(sys.argv[2])	#number of reduns
num_seconds=int(sys.argv[3])*3600	#number of seconds
checkamount=bci.default_fee

def new_keypair():
	pk=pybtct.random_key()
	addr=pybtct.privkey_to_address(pk)
	return addr,pk

redundancy_keypairs=[new_keypair() for x in range(num_redundancies)]
address_list=[x[0] for x in redundancy_keypairs]

outfile = """%s
if
	%d send<%s>
	$default_fee pushtx
#-----BEGIN SUBSCRIPT
	%s
#-----END SUBSCRIPT
endif
"""


#Send_remote command...could send from a remote address that you fill up 
#would make this dead-man's switch truely anonymous...doesn't matter for now tho

def gen_address_check(addresslist):
	if(len(addresslist) < 1):
		return "1"
	if(len(addresslist) == 1):
		return "timestamp<now> timestamp<%s> sub %d greater\n" %(addresslist[0],num_seconds)
	h=len(addresslist)/2
	return gen_address_check(addresslist[:h])+gen_address_check(addresslist[h:])+'and\n'	#Recursive binary tree AND.  Has a possibility of O(n/2) checks instead of O(n).  (Can also do a tail list to check activity or something...might be faster) 

def gen_redundancy(index):
	checks=gen_address_check(address_list[:index])
	outredun=outfile % (checks,checkamount,address_list[index],inputfile)
	return outredun

keysfile=open('redun_keys.txt','w')
for x in range(num_redundancies):
	redunfile=open('redun%d' % (x),'w')
	keysfile.write("%d %d\n" % redundancy_keypairs[x])
	redunfile.write(gen_redundancy(x))







