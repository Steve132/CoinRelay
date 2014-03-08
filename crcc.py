#!/usr/bin/env python

import language
import lib.bitcoin_listener
import lib.pybitcointools
import os.path,os
import logging
from shutil import copy

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
	compiled=language.compile_coinscript(open(fp,'r').read())
	print "File %s Compiled as:\n%s" % (fp,compiled)
	assembled=language.assemble_coinscript(compiled,fp)
	return assembled

def _loadfile(address):
	make_sure_path_exists('db')
	fp=os.path.join('db',address+'.crs')
	cfp=os.path.join('db',address+'.crb')
	kfp=os.path.join('db',address+'.key')
	
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
		

def serve():
	print "Now listening to the bitcoin network for transactions."
	rt=language.runtime(debugmode=True)
	def handlepayment(from_address,to_address,amount,txid):
		lf=_loadfile(to_address)
		if(lf):
			print "Script triggered for %s" % to_address
			btc_private_key=open(os.path.join('db',to_address+'.key')).read().strip()
			result=rt.run_coinscript(lf,btc_private_key,in_amount=int(amount)*10,in_address=from_address,balance=None)
			print rt.pretty_print_logs(result)
			
	def htx(txid):
		print "Heard Transaction: %s" % (txid['hash'])
		lib.bitcoin_listener.handletx(txid,handlepayment)

	lib.bitcoin_listener.run_wire_listener(on_new=htx)

def update(source_file,private_key=lib.pybitcointools.random_key()):
	make_sure_path_exists('db')
	#if(len(private_key) > 
	myaddress=lib.pybitcointools.privkey_to_address(private_key)
	copy(source_file,os.path.join('db',myaddress+'.crs'))
	open(os.path.join('db',myaddress+'.key'),'w').write(private_key)
	print "A copy of %s was made, listening on address %s" % (source_file,myaddress)
	
def test(source_file,balance='1.0',input_amount='0.1'):
	rt=language.testruntime()
	assembled=_compileandassemble(source_file)
	result=rt.run_coinscript(assembled,int(1e9*float(balance)),int(1e9*float(input_amount)))
	print rt.pretty_print_logs(result)

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
			Update the backend database in the current directory to listen for 'script'.  This can be done while the client is running in 'serve' mode, or in preparation for a server.
			
		

if __name__=="__main__":
	if(len(sys.argv) > 1):
		funcarg=sys.argv[1]
	else:
		funcarg='serve'
	funcs={"serve":serve,"update":update,"test":test}
	funcs[funcarg](*sys.argv[2:])
