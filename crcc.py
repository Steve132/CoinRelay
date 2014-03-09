#!/usr/bin/env python

import coinrelay
import lib.bitcoin_listener
import lib.pybitcointools
import os.path,os
import logging
from shutil import copy
import traceback

import os
import errno
import sys

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def _compileandassemble(fp):
	compiled=coinrelay.compile_coinscript(open(fp,'r').read())
	print "File %s Compiled as:\n%s" % (fp,compiled)
	assembled=coinrelay.assemble_coinscript(compiled,fp)
	return assembled

def _loadfile(address):
	make_sure_path_exists('.crdb')
	fp=os.path.join('.crdb',address+'.crs')
	cfp=os.path.join('.crdb',address+'.crb')
	kfp=os.path.join('.crdb',address+'.key')
	
	kfpe=os.path.exists(kfp)
	cfpe=os.path.exists(cfp)
	fpe=os.path.exists(fp)
	
	if(not kfpe):
		return False
	elif(fpe):
		if(cfpe and os.stat(cfp).st_mtime >= os.stat(fp).st_mtime):
			return open(cfp,'rb').read()
		else:
			assembled=_compileandassemble(fp)
			open(cfp,'wb').write(assembled)
			return assembled
			
	elif(cfpe):
		return open(cfp,'rb').read()
	else:
		return False
	
def _trigger_response(rt,from_address,to_address,amount,txid):
	try:
		lf=_loadfile(to_address)
		if(lf):
			print "Script triggered for %s" % to_address
			btc_private_key=open(os.path.join('.crdb',to_address+'.key')).read().strip()
			result=rt.run_coinscript(lf,btc_private_key,in_amount=int(amount)*10,in_address=from_address,balance=None)
			print rt.pretty_print_logs(result)
	except:
		print "Error in coinscript runtime:"
		traceback.print_exc(file=sys.stdout)

def listen():
	print "Now listening to the bitcoin network for transactions."
	rt=coinrelay.runtime(debugmode=True)
	
	def handle(from_address,to_address,amount,txid):
		print from_address,to_address
		return _trigger_response(rt,from_address,to_address,amount,txid)

	def htx(txid):
		print "Heard Transaction: %s" % (txid['hash'])
		lib.bitcoin_listener.handletx(txid,handle)	

	lib.bitcoin_listener.run_wire_listener(on_new=htx)

def update(source_file,private_key=lib.pybitcointools.random_key()):
	make_sure_path_exists('.crdb')
	#if(len(private_key) > 
	myaddress=lib.pybitcointools.privkey_to_address(private_key)
	copy(source_file,os.path.join('.crdb',myaddress+'.crs'))
	open(os.path.join('.crdb',myaddress+'.key'),'w').write(private_key)#lib.pybitcointools.hex_to_b58check(private_key))
	print "A copy of %s was made, listening on address %s" % (source_file,myaddress)
	
def test(source_file,balance='1.0',input_amount='0.1'):
	rt=coinrelay.testruntime()
	assembled=_compileandassemble(source_file)
	result=rt.run_coinscript(assembled,int(1e9*float(balance)),int(1e9*float(input_amount)))
	print rt.pretty_print_logs(result)

def trigger(to_address,from_address,amount='10000000',txid='<no tx id>'):
	rt=coinrelay.runtime(debugmode=True)
	return _trigger_response(rt,from_address,to_address,int(amount),txid)
	

def help():
	print """
CoinRelay Standalone Client+Compiler
Usage:	%s [command] [command arguments]
Commands:
	help	
		Display this message
	test	<source_file.crs> [balance <float> (defaults to 1.0)] [transaction in amount <float> (defaults to 0.1)]	
		Compile and test a script.  This command compiles and executes the script on the cmdline to see what would happen.  Prints the generated python intermediate code, and runs the script assuming a
		balance and input triggered the transaction.  All commands with side effects (such as send and reflect) are simulated not sent to the blockchain.
	update	<source_file.crs> [private_key]
		Update the backend database in the current directory to listen for 'script'.  This can be done while crcc.py is running in 'listen' mode in another process, or before listen mode is run to prepare the database
	listen
		Starts the coinrelay standalone client in 'listen' mode.  This is the production mode.  Using the database, ( found in the .crdb folder in the current directory), it listens to incoming messages from the blockchain and runs the associated scripts in the database registered to an address if the address exists.
	
	trigger <to_address> <from_address> [amount <int> (defaults to 10000000)] [txid]
		This immediately ACTUALLY executes the code in the database that is registered to <to_address>, as if a transaction with <txid> from <from_address> to <to_address> occurred.  This is useful for creating cron jobs
		to trigger coinscript code or responding to other events instead of a blockchain.

Aliases:
	register:	alias for 'update'
	serve:		alias for 'listen'
	compile:	alias for 'test'
	execute:	alias for 'trigger'
"""
			
if __name__=="__main__":
	if(len(sys.argv) > 1):
		funcarg=sys.argv[1]
	else:
		funcarg='help'
	funcs={"listen":listen,"serve":listen,"register":update,"update":update,"test":test,"compile":test,"help":help}
	funcs[funcarg](*sys.argv[2:])
