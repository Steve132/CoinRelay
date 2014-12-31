#This is the function that defines the thread that listens to the bitcoin network continuously.
#It is called by backends.py.   It uses a websocket to connect to blockchain.info 

import websocket
import json
import thread
import logging
import datetime

#A transaction looks something like this:
#{u'inputs': [{u'prev_out': {u'type': 0, u'addr': u'1MDN9KsvG6AmXnV4Uu9UYV1UBoA1hw38kU', u'value': 224990000}}], u'lock_time': u'Unavailable', u'hash': u'b86ceca2dc829bc15b1e1a66dfef85d018cfe64c6c7aa6956710c4c75bee4af1', u'tx_index': 96440120, u'relayed_by': u'5.9.24.81', u'vin_sz': 1, u'vout_sz': 2, u'time': 1384140910, u'out': [{u'type': 0, u'addr': u'1GgJPtA1CkFUQXZyKvUWMKeRtsToxebGcS', u'value': 91000000}, {u'type': 0, u'addr': u'1Kw3ZBLHNgRyTYCkW4B9znbwiUw9tTJg75', u'value': 133980000}], u'size': 225}
	
#Handle an incoming transaction from the bitcoin network	
def handletx(tx,handlepayment):
	#print(tx['hash'])
	futures=[]
	futures_data=[]
	inputs=[]

	#Look at all address outputs in a given incoming bitcoin transaction to see if we own any of them
	for o in tx['out']:
		if('addr' in o):
			address=o['addr']
			amount=o['value']
			from_addy='none'
			#We need to make sure that we aren't just getting change back.   If one of our addresses is sending this then we have to record who it is from
			if('inputs' in tx):
				if(len(tx['inputs'])):
					from_addy=tx['inputs'][0]['prev_out']['addr']
			if(from_addy != address):
				handlepayment(from_address=from_addy,to_address=address,amount=int(amount),txid=tx['hash'])

#on a block confirm from the bitcoin network report that we got a block
def handleblock(b):
	logging.info("Handling a block"+str(b))
#	process()
	
class Bitcoin(object):
	def __init__(self,on_new_transaction=None,on_new_block=None):
		endpoint='wss://ws.blockchain.info/inv'		#TODO:SECURITY: The endpoint should support SSL (wss://) to prevent man-in-the middle attacks but GAE does not by default.  Must be enabeled
		self.ws=websocket.WebSocketApp(endpoint,
			on_message=self.__socket_message,
			on_error=self.__socket_error,
			on_close=self.__socket_close)
		self.ws.on_open=self.__socket_open
		#self.waiting_transactions=set()
		self.on_new_transaction=on_new_transaction
		self.on_new_block=on_new_block
		
	def __socket_message(self,ws,msg):
		jsid=json.loads(msg)
		op=jsid['op']
		if(op=='status'):
			print 'STATUS:'+jsid['msg']
		elif(op=='utx'):
			tx=jsid['x']
			self.on_new_transaction(jsid['x'])	
			self.__socket_send_message('')
		elif(op=='block'):
			self.on_new_block(jsid['x'])
		else:
			print "UNKNOWN BLOCKCHAIN MESSAGE:"+msg
	
	def __socket_error(self,ws,err):
		ws.keep_running=False
		raise err

	def __socket_close(self,ws):
		logging.info("THE WEBSOCKET CLOSED!")

	def __socket_open(self,ws):
		ws.send('{"op":"unconfirmed_sub"}')
		ws.send('{"op":"blocks_sub"}')

	def __socket_send_message(self,msg):
		self.ws.send(msg)

	#warning
	#def __queued_send(private_key_hex,send_to):
		
	def run(self):
		self.ws.run_forever(ping_interval=10)

#so what is going to happen is that on a new transaction, the transaction
#gets added to the DB.

def block(b):
	logging.info('Recieved block'+str(b))
	#handleblock(b)
	#deferred.defer(handleblock,b,_queue='externalblocks')
def etx(e):
	logging.info('Recieved transaction'+str(e))
	#handletx(e)
	#deferred.defer(handletx,e,_queue='externaltransactions')	
	
b=None
#This function is called to run the wire listener thread.
def run_wire_listener(on_block=block,on_new=etx):
	global b
	
	b=Bitcoin(on_new_block=on_block,on_new_transaction=on_new)
	b.run()
	#This loop makes sure that the bitcoin socket doesn't turn off unless the server shuts down.
	#while True:	
	#	try:
	#		b.run()
	#	except Exception as e:
	#		logging.info(str(e))
	#		logging.info("Caught problem in listener.  Restarting")
		
def stop_handler():
	global b
	b.ws.keep_running=False
	
