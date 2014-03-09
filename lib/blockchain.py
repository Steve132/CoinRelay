import pybitcointools.bci as bci
import pybitcointools as pbtc
import json
import random
import urllib2
import urllib
import logging
import datetime
import time
import traceback

blockchain_timeout=10000
#default_fee=100000 #0.0001*1e9
default_fee=100000 #0.001*1e9 (for Gox)
num_blockchain_retries=2

last_request=datetime.datetime.utcnow()
request_persecond=0.428571;
request_quota=5*60.0;
request_time_left=request_quota;

#basically, time_remaining=5 minutes.
#every time a request takes less than request_persecond, subtract that from the time remaining.
#every time it takes more, add that to the time remaining (up to 5)
#if you have no time remaining, delay request_persecond
#if you have 

def request_wait():
	now_time=datetime.datetime.utcnow()
	now_duration=(now_time-last_request).total_seconds()
	request_time_left+=(request_per_second-now_duration)
	if(request_time_left < 0):
		time.sleep(request_persecond)
		request_wait()
	elif(request_time_left > request_quota):
		request_time_left=request_quota
	

def make_request(*args):
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0'+str(random.randrange(1000000)))]
	request_wait()
	try:
		return opener.open(*args).read().strip()
	except Exception,e:
		try:
			p = e.read().strip()
		except: 
			p = e
			raise Exception(p)
def _bci_request(url):
	for x in range(num_blockchain_retries):
		try:
			return bci.make_request(url)
		except Exception as e:
			logging.info("Blockchain request failed.  at Retrying... AT")
			#logging.info(traceback.format_exc())
			
	
	raise BackendServerNotResponding()

def getaddressinfo(address):
	br=json.loads(_bci_request(url='https://blockchain.info/address/%s?format=json&limit=1' % (address)))
	brc=_bci_request(url='https://blockchain.info/q/addressbalance/%s?confirmations=6' % (address))
	return {'balance':int(brc)*10,
		'unconfirmed_balance':br['final_balance']*10, #nanobtc
		'last_accessed': (0 if len(br['txs']) < 1 else br['txs'][0]['time'])}

def getaddresslastsenttime(address):
	br=json.loads(_bci_request(url='https://blockchain.info/address/%s?format=json&limit=1&filter=1' % (address)))
	return (0 if len(br['txs']) < 1 else br['txs'][0]['time'])

def send_p(btc_private_key,amount,to,fee=default_fee,message=''):
	br=_bci_request(url='https://blockchain.info/merchant/%s/payment?to=%s&amount=%d&note=%s&fee=%d' % (btc_private_key,to,int(amount/10),message,int(fee/10)))
	brj=json.loads(br)
	logging.info("SEND2 RESULT:"+br)
	if('error' in brj):
		raise BackendServerError(brj['error'])
	return brj

#def send(btc_private_key,amount,to,fee=default_fee,message=''):
#	br={}
#	from_addy=utils.private_key2address(btc_private_key)
#	while('tx_hash' not in br):
#		try:
#			br=send_p(btc_private_key,amount,to,fee,message)
#		except:
#			br=findtx_tofrom(from_addy,to)
#
#	return br

def sendmany(btc_private_key,outputs,fee=default_fee):
	modded_outputs=dict([(k,int(v/10)) for k,v in outputs.iteritems()])
	mos=json.dumps(modded_outputs)
	print ("outs: %s" % (mos))
	outstring=urllib.urlencode({'recipients':mos,'fee':int(fee/10)})
	br=_bci_request(url='https://blockchain.info/merchant/%s/sendmany?%s' % (btc_private_key,outstring))
	brj=json.loads(br)
	logging.info("SEND2 RESULT:"+br)
	if('error' in brj):
		raise BackendServerError(brj['error'])
	return brj

def findtx_tofrom(from_address,to_address):
	try:
		brc=_bci_request(url='https://blockchain.info/address/%s?format=json' % (to_address))
		logging.info("FINDTX RESULT:"+brc)
		address_stuff=json.loads(brc)
		for a in address_stuff['txs']:
			if(a['inputs'][0]['prev_out']['addr']==from_address):
				return {'tx_hash':a['hash']}
		return {}
	except:
		return {}	

class BackendServerNotResponding(Exception):
	def __init__(self):
		super(Exception,self).__init__('One of the backend servers is not responding to the request.  Please try again later.')
class BackendServerError(Exception):
	def __init__(self,s):
		super(Exception,self).__init__('BackendServer reported: '+s)
class NoTransactionError(Exception):
	def __init__(self,s):
		super(Exception,self).__init__('Transaction does not exist')

def getbalance(address,confirmations=0):
	brc=_bci_request(url='https://blockchain.info/q/addressbalance/%s?confirmations=%s' % (address,str(confirmations)))
	return int(brc)*10

def getpublickey(address):
	brc=_bci_request(url='https://blockchain.info/q/pubkeyaddr/%s' % (address))
	if(brc==''):
		return None
	else:
		return brc

def getblockheight():
	brc=_bci_request(url='https://blockchain.info/q/getblockcount')
	if(brc==''):
		return None
	else:
		return int(brc)

def getexchangerates():
	brc=_bci_request(url='https://blockchain.info/ticker')
	return json.loads(brc)

def checkconfirmations(txid):
	url='https://blockchain.info/tx/%s?format=json' % (txid)
	p=_bci_request(url=url)
	if(p.strip()=='Transaction not found'):
		raise NoTransactionError(txid)
	br=json.loads(p)
	if('block_height' in br):
		br2=json.loads(_bci_request(url='https://blockchain.info/latestblock'))
		txheight=br['block_height']
		return br2['height']-txheight+1
	else:
		return 0

