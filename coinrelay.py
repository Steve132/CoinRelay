import re
import lib.pybitcointools as pybitcointools
import lib.blockchain as blockchain
import lib.exchangerates as exchangerates
from calendar import timegm
from datetime import datetime
import marshal
import random
from string import maketrans

_funcparamre=re.compile(r'(#.*)$|(\d+)|\$(\w+)|(\w+)\s*(<[^>]*>)?',flags=re.MULTILINE)

class Transaction(object):
	def __init__(self,source_addy):
		self.sends={}
		self.source_addy=source_addy
	def add(self,amount,address):
		self.sends[address]=self.sends.get(address,0)+amount
	def clear(self):
		self.sends={}
	def __str__(self):
		return 'Transaction(%s->%s)' % (self.source_addy,str(self.sends))
	def value(self):
		return sum([v for k,v in self.sends.iteritems()])

class baseruntime(object):
	def run_coinscript(self,mcompiled_code,btc_private_key,in_amount,in_address,balance=None):
		myaddress=pybitcointools.privkey_to_address(btc_private_key)
		if(balance==None):				
			balance=blockchain.getbalance(myaddress)
			
		st=[]
		sa={	'balance':balance,
			'in':in_amount,
			'spent':0,
			'default_fee':blockchain.default_fee
		}
		loca = {'in_address':in_address,
		        'my_address':myaddress,
			'pk':btc_private_key }
		tx=Transaction(myaddress)
		lg=[]
		compiled_code=marshal.loads(mcompiled_code)
		safe_scope={'sa':sa,'st':st,'rt':self,'tx':tx,'lg':lg}
		safe_scope.update(loca)
		self.saref=sa	#BAD...can't be run in parallel.
		self.stref=st	#BAD...can't be run in parallel...TODO fix this
		exec compiled_code in safe_scope
		self.logevent(lg,-1,'<end program>')
		return lg

	def price_query(self,amount,direction,scheme=None):	#TODO,scheme...only scheme is 'blockchain'
		return int(exchangerates.convert(amount,direction[:3],direction[3:]))
		

	def log(self,string):
		print 'SCRIPT LOG:'+string

	def get_balance(self,addr):
		return blockchain.getbalance(addr)
	def get_blockheight(self):
		return blockchain.getblockheight()
	def get_address_last_send_timestamp(self,addr):
		return blockchain.getaddresslastsenttime(addr)
		
	def get_now(self):
		return timegm(datetime.utcnow().utctimetuple())
	def get_random(self,cei):
		return random.randint(0,cei)	#TODO: NOT SECURE
	def logevent(self,ls,i,cmd):
		ls.append({'si':i,'cmd':cmd,'st':list(self.stref),'sa':dict(self.saref.copy())})
		#self.logstate.append({'st':list(self.stref)})
	def pretty_print_logs(self,ls):
		
		catlen=[0,0,0]
		def se(r):
			return [str(x) for x in [r['si'],r['cmd'],r['sa']['spent']]]

		for r in ls:
			for i,p in enumerate(se(r)):
				catlen[i]=max(len(p),catlen[i])

		s="token spent st\n"
		formatstring="%%%ds %%%ds %%%ds " % tuple(catlen)
		
		for r in ls:
			ps=se(r)
			s+=formatstring % tuple(ps) + str(r['st']) +'\n'
		return s
	
	def push_tx_to_blockchain(self,pk,tx,fee=0):
		if(self._push_tx_action(pk,tx,fee)):
			self.saref['balance']-=tx.value()+fee
			tx.clear()
		
			
#Test addresses
#5JwaFNNKwEnnNfXmYiUuTJkao8YjR8BsUpvwqNZJ2kdjziWm2Ek,1testp2A3NBcCNKqE2isK7mFAPQPnGmKs
#5KWPWdgDYjFsL6hq1RCaw1JcguUquscUris1ST3dKJzcknXSUBC,1srcFhv3dJqfxbgGHyJfMythtgtHzbQtG
#5Jmhc4q8eaTzKZLvo8YD1NEsjP9eSXRgV1gugJsigJQRjaEcRhz,1dstBr7MEq7WUn6DDy8DCtMZL3S1GMtMY
class testruntime(baseruntime):
	def __init__(self):
		super(testruntime,self).__init__()
	def run_coinscript(self,mcompiled_code,balance=int(1e9),amount_in=int(1e9)):
		return baseruntime.run_coinscript(self,mcompiled_code,btc_private_key='5JwaFNNKwEnnNfXmYiUuTJkao8YjR8BsUpvwqNZJ2kdjziWm2Ek',balance=balance,in_amount=amount_in,in_address='1srcFhv3dJqfxbgGHyJfMythtgtHzbQtG')
	def _push_tx_action(self,pk,tx,fee=0):
		print "ACTION:pushed transaction "+str(tx)+" to blockchain with a fee of %d" % (fee)
		return True

class runtime(baseruntime):
	def __init__(self,debugmode=False):
		super(runtime,self).__init__()
		self.debugmode=debugmode
	
	def _push_tx_action(self,pk,tx,fee=0):
		try:
			blockchain.sendmany(pk,tx.sends,fee)
			return True
		except:
			return False

	def logevent(self,ls,i):
		if(self.debugmode):
			baseruntime.logevent(self,ls,i)


def compile_coinscript(text,debug=True):
	tokens=_tokenize(text)
	return _translate_tokens(tokens,compilerflags={'debugmode':debug})
	

def assemble_coinscript(python_source,crfile):
	return marshal.dumps(compile(python_source,'<code from %s.py>' % (crfile),'exec'))	
		
def _funclookup(opname):
	f=globals()['_func_'+opname]
	return f
	
def _tokenize(functext):
	return _funcparamre.findall(functext)
def _compile_literal(lit):
	return "st.append(%s)" % (lit),0
def _compile_argument(argname):
	return "st.append(sa['%s'])" % (argname),0
def _compile_op(num_args,opstring):
	return """
a=st[-%d:]
del st[-%d:]
r=%s
st.append(r)
""" % (num_args,num_args,opstring),0

def _classify_token(c):
	if(c[1]):
		return "literal",c[1]
	if(c[2]):
		return "environment",c[2]
	if(c[3]):
		return "instruction",c[3]+'%s'%(c[4])
	if(c[0]):
		return "comment",c[0]

def _compile_token(c,cls):
	if(cls=="literal"):	#Literal integer
		return _compile_literal(c[1])
	if(cls=="environment"):	#Argument input
		return _compile_argument(c[2])
	if(cls=="instruction"):	#function call
		arglist=[]
		if(c[4]):
			arglist=c[4].strip('<>').split(',')
		f=_funclookup(c[3].lower())
		#print f(*arglist)
		return f(*arglist)
	if(cls=="comment"):
		return c[0],0
	return "",0#throw an error here
	
def _translate_tokens(tokens,compilerflags):
	indentlevel=0
	funcout=""
	i=0
	for c in tokens:
		cls,tokenstr=_classify_token(c)
		code,indentchange=_compile_token(c,cls)				#compile the token
		if(compilerflags['debugmode'] and cls != "comment"):
			code=('rt.logevent(lg,%d,"%s")\n' % (i,tokenstr))+code
			i+=1
		funcout+=('\n'+code).replace('\n','\n'+'\t'*indentlevel)	#indent the code
		
		indentlevel+=indentchange
	return funcout

def _func_add():
	"""(Arithmetic|st[-2]+st[-1]->st[-1]|Pop the top two elements, add them, and push the result onto the stack)"""
	return _compile_op(2,"a[0]+a[1]")
def _func_sub():
	"""(Arithmetic|st[-2]-st[-1]->st[-1]|Pop the top two elements,subtract the second element from the first, and push the result onto the stack)"""
	return _compile_op(2,"a[0]-a[1]")
def _func_mul():
	"""(Arithmetic|st[-2]*st[-1]->st[-1]|Pop the top two elements,multiply them, and push the result onto the stack)"""
	return _compile_op(2,"a[0]*a[1]")
def _func_div():
	"""(Arithmetic|st[-2]/st[-1]->st[-1]|Pop the top two elements,divide the first element by the second, and push the result onto the stack)"""
	return _compile_op(2,"a[0]/a[1]")
def _func_mod():
	"""(Arithmetic|st[-2] % st[-1]->st[-1]|Pop the top two elements,divide the first element by the second, and push the remainder onto the stack)"""
	return _compile_op(2,"a[0] % a[1]")
def _func_rshift():
	"""(Arithmetic|st[-2] >> st[-1]->st[-1]|Pop the top two elements,divide the first element by 2^second, and push the result onto the stack)"""
	return _compile_op(2,"a[0] >> a[1]")
def _func_lshift():
	"""(Arithmetic|st[-2] << st[-1]->st[-1]|Pop the top two elements,multiply the first element by 2^second, and push the result onto the stack)"""
	return _compile_op(2,"a[0] << a[1]")
def _func_pow():
	"""(Arithmetic|st[-2]^st[-1]->st[-1]|Pop the top two elements, and use the second element as the exponent of the first.  Push the result onto the stack)"""
	return _compile_op(2,"a[0] ** a[1]")
def _func_max():
	"""(Arithmetic|max(st[-2],st[-1])->st[-1]|Pop the top two elements,push the largest one back onto the stack)"""
	return _compile_op(2,"max(a[0],a[1])")
def _func_min():
	"""(Arithmetic|min(st[-2],st[-1])->st[-1]|Pop the top two elements,push the smallest one back onto the stack)"""
	return _compile_op(2,"min(a[0],a[1])")
def _func_abs():
	"""(Arithmetic|abs(st[-1])->st[-1]|Pop the top element and push the absolute value onto the stack)"""
	return _compile_op(1,"max(a[0],-a[0])") 

def _func_bitinvert():
	"""(Arithmetic|~st[-1]->st[-1]|Pop the top element, treat it as a binary integer and flip all the bits.  push the result onto the stack)"""
	return _compile_op(1,"~a[0]")
def _func_bitand():
	"""(Arithmetic|(st[-1] & st[-2])->st[-1]|Pop the top two elements, treat them as binary integers and compute an AND operation between all pairs of bits. push the result onto the stack)"""
	return _compile_op(2,"a[0] & a[1]")
def _func_bitor():
	"""(Arithmetic|(st[-1] or st[-2])->st[-1]|Pop the top two elements, treat them as binary integers and compute an OR operation between all pairs of bits. push the result onto the stack)"""
	return _compile_op(2,"a[0] | a[1]")
def _func_bitxor():
	"""(Arithmetic|(st[-1] ^ st[-2])->st[-1]|Pop the top two elements, treat them as binary integers and compute an Exclusive-OR operation between all pairs of bits. push the result onto the stack)"""
	return _compile_op(2,"a[0] ^ a[1]")


def _func_and():
	"""(Logic|(st[-2] && st[-1])->st[-1]|Pop the top two elements.  If both are not 0, push 1 onto the stack.  Otherwise push 0 onto the stack)"""
	return _compile_op(2,"1 if (a[0] and a[1]) else 0")
def _func_or():
	"""(Logic|(st[-2] or st[-1])->st[-1]|Pop the top two elements.  If either is not 0, push 1 onto the stack.  Otherwise push 0 onto the stack)"""
	return _compile_op(2,"1 if (a[0] or a[1]) else 0")
def _func_not():
	"""(Logic|(!st[-1])->st[-1]|Pop the top element.  If it is not 0, push 0 onto the stack.  Otherwise push 1 onto the stack)"""
	return _compile_op(1,"0 if a[0] else 1")

def _func_equal():
	"""(Logic|(st[-1]==st[-2])->st[-1]|Pop the top two elements.  If they are the same, push 1 onto the stack.  Otherwise push 0.)"""
	return _compile_op(2,"int(a[0] == a[1])")
def _func_notequal():
	"""(Logic|(st[-1]!=st[-2])->st[-1]|Pop the top two elements.  If they are not the same, push 1 onto the stack.  Otherwise push 0.)"""
	return _compile_op(2,"int(a[0] != a[1])")
def _func_less():
	"""(Logic|(st[-2] < st[-1])->st[-1]|Pop the top two elements.  If the first one is less than the second, push 1.  Otherwise push 0.)"""
	return _compile_op(2,"int(a[0] < a[1])")
def _func_lessequal():
	"""(Logic|(st[-2] <= st[-1])->st[-1]|Pop the top two elements.  If the first one is less than or equal to the second, push 1.  Otherwise push 0.)"""
	return _compile_op(2,"int(a[0] <= a[1])")
def _func_greater():
	"""(Logic|(st[-2] > st[-1])->st[-1]|Pop the top two elements.  If the first one is greater than the second, push 1.  Otherwise push 0.)"""
	return _compile_op(2,"int(a[0] > a[1])")
def _func_greaterequal():
	"""(Logic|(st[-2] >= st[-1])->st[-1]|Pop the top two elements.  If the first one is greater than or equal to the second, push 1.  Otherwise push 0.)"""
	return _compile_op(2,"int(a[0] >= a[1])")

def _func_dup():
	"""(Memory|st[-1]->st[-1],st[-2]|Duplicate the top element of the stack and put the copy on the stack.)"""
	return "st.append(st[-1])",0
def _func_fetch(position):
	"""(Memory|st[p]->st[-1]|Go to position p in the stack, where 0 is the bottom of the stack.  Retrieve the item there, remove it, and put it on the stack|<position>...Must be an integer...The template argument for the position to go to.  May be negative to count back off the top of the stack)"""	
	return "st.append(st.pop(%d))" % (int(position))
def _func_bury(position):
	"""(Memory|st[-1]->st[p]|Pop the top item off the stack, then insert it into to position p in the stack, where 0 is the bottom of the stack.|<position>...Must be an integer...The template argument for the position to go to.  May be negative to count back off the top of the stack)"""	
	return "st.insert(%d,st.pop())" % (int(position))

def _func_send(address):
	"""(Transactions|send bitcoin|Pop the top item off of the stack, interpret it as the amount of nanoXBT to send to <address>.  Append that destination and amount to the current transaction  |<address> Must be a valid bitcoin address, the address to send to)"""
	return """
ad=st.pop()
tx.add(ad,'%s')
sa['spent']+=ad
""" % (address),0

def _func_reflect():
	"""(Transactions|send bitcoin to source|Pop the top item off of the stack, interpret it as the amount of nanoXBT to send to the address that initiated this transaction.  Append that destination and amount to the current transaction)"""
	return """
ad=st.pop()
tx.add(ad,in_address)
sa['spent']+=ad""",0
def _func_pushtx():	#TODO: balance should be updated if it succeeds
	"""(Transactions|send bitcoin|Pop the top item off of the stack, interpret it as the fee in nanoXBT to use in the current transaction. Broadcast the current transaction to the blockchain immediately and reset the current transaction)"""
	return "rt.push_tx_to_blockchain(pk,tx,fee=st.pop())",0

def _func_return():
	"""(Control|return|Immediately stop executing the script)"""
	return "return",0
def _func_if():
	"""(Control|if not 0|If the top of the stack is not 0, then find the matching endif and execute the code between them.  Otherwise jump to the matching endif.  Can be nested)"""
	return "if(st.pop()):",1
def _func_endif():
	"""(Control|endif|Must be preceded by a matching 'if'.  Ends a control block for an if statement   )"""
	return "",-1
def _func_nop():
	"""(Control|no-op|Does nothing.)"""
	return "",0

#def _func_log():
#	"""(Control|print|Prints the top integer off the stack as a "LOG" statement )"""
#	return "rt.log(str(st.pop()))",0

def _func_balance(address):
	"""(Information|get balance|Checks the blockchain for the balance in bitcoin for the given <address>.  Puts the balance (in nanoXBT) onto the stack | <address> Must be a valid bitcoin address.  The address balance to check)"""
	#checks the balance of a given address,puts it on the stack
	return "st.append(rt.get_balance('%s'))" % (address),0
def _func_blockheight():
	"""(Information|get blockheight|Checks the blockchain for the current block height, puts it into the stack"""
	#checks the latest block in the blockchain on the stack
	return "st.append(rt.get_blockheight())",0
def _func_timestamp(*argument):
	"""(Information|get time of event|Based on the <argument>, pushes several different kinds of unix timestamps onto the stack.  If <argument> is a bitcoin address, look at the blockchain to determine
	the last time the private key for the address was used to sign a transaction on the network.  If <argument> is the string "now", it pushes the unix timestamp for the current time on the stack.  If <argument> is 
	a comma,period,hyphen,colon,or space -seperated date, largest denomination first (such as <2021-5-21> or <2051-1-21 13:42:23>, then calculate the appropriate unix timestamp and push it on the stack |<argument> is the kind of timestamp to fetch."""
	argument=' '.join(argument)
	if(argument=="now"):
		return "st.append(rt.get_now())",0
	if(set(argument).issubset(pybitcointools.get_code_string(58))):	
		return "rt.address_last_send_timestamp('%s')" % (argument[0]),0
	
	arglist=[int(x) for x in argument.translate(maketrans('-.~,:','     ')).split()]
	return "st.append(%d)" % (timegm(datetime(*arglist).utctimetuple())),0
	#if():	#parse date attempt
	#	return "todo",0

#def _func_address(addrarg):	#maybe this is dangerous...think hard about whether int versions of addresses can go on the stack.but this lets you do checks like source verification and stuff.  Or dynamic sends.  Also makes "reflect' command obsolete
#	if(addrarg=='this'):
		

def _func_price(direction='usdxbt',scheme=None):
	"""(Information|price currency conversion|Based on the <conversiondirection>, does a conversion of currency.  Converts the value on top of the stack.  Conversion direction is a concatination of iso currency codes (case-insensitive) such as 'usdbtc' to find the number of bitcoin you could buy with the usd value on the stack,  or 'usdeur' or 'xbteur'.  Bitcoin can be listed as xbt or btc.|<conversiondirection> is the direction of currency conversion 6-character string)"""
	if(not scheme):
		return "st.append(rt.price_query(st.pop(),direction='%s'))" % (direction),0
	else:
		return "st.append(rt.price_query(st.pop(),direction='%s',scheme='%s'))" % (direction,scheme),0
def _func_rate(direction='usdxbt',scheme=None):
	"""(Information|get exchange rates|Based on the <conversiondirection>, gets the current exchange rate and puts it on the stack. See price command for information.  |<conversiondirection> is the direction of currency conversion 6-character string)"""
	if(not scheme):
		return "st.append(rt.price_query(1000000000,direction='%s'))" % (direction),0
	else:
		return "st.append(rt.price_query(1000000000,direction='%s',scheme='%s'))" % (direction,scheme),0
def _func_nano(fl):	#converts the floating point constant to nanoamounts.  This is useful for currencies
	"""(Arithmetic|constant float to integer|Since there are only integers on the stack and most currency quantities are nanoX...its helpful to be able to load the stack using a float to count nanoelements.  Multiplies
	the floating point value in <arg> by 1e9, and converts it to an integer and puts it on the stack|<arg> a floating point to convert to nano-elemnts and put on the stack)"""
	return "st.append(%d)" % (int(float(fl)*1e9)),0

def _func_random():
	"""(Arithmetic|random(0,x)|Pops the top of the stack, then generates a random integer between 0 and st[-1]-1,inclusive, and pushes it on the stack)"""
	return "st.append(rt.get_random(st.pop()))",0
def _func_minus_fee():
	"""(Arithmetic|st[-1]-=$default_fee|Subtracts the current default suggested transaction fee from the value on top of the stack)"""
	return "st[-1]-=sa['default_fee']",0
def _func_minus_spent():
	"""(Arithmetic|st[-1]-=$default_fee|Subtracts the current 'accounted for' spend amount from the value on top of the stack)"""
	return "st[-1]-=sa['spent']",0

#TODO: Feature....send using ANOTHER private key.  This is serious mojo, it allows you to read and write program state into the blockchain...put this off till version 2..maybe send_remote
#maybe addresses as integers (like timestamp)
	
#if __name__=='__main__':
#	import sys
#	text=open(sys.argv[1],'r').read()
#	rt=testruntime()
#	pyfunc=rt.compile_coinscript(text)
#	print pyfunc
#	pyob=rt.assemble_coinscript(pyfunc)
#	print rt.run_coinscript(pyob)	#Todo, add a bitcoin private key
#	#print rt.logstate
	

def print_markdown_documentation():
	categories={}
	for k,v in globals().iteritems():
		if(k[:6]=='_func_'):
			vdoc=v.__doc__.replace('<','&lt;').replace('>','&gt;').strip("()").split("|")
			funcname=k[6:]
			category=vdoc[0]
			summary=vdoc[1]
			description=vdoc[2].replace('\n',' ')
			if(len(vdoc) > 3):
				args=vdoc[3]
			else:
				args="None"
			
			cat=categories.get(category,[])
			cat.append((funcname,summary,description,args))
			categories[category]=cat
	for k,c in categories.iteritems():
		print k
		print '-------------'
		print 'Opcode | Summary | Description | Arguments'
		print '-------|---------|-------------|----------'
		for op in c:
			print '%s|%s|%s|%s' % (op[0],op[1],op[2],op[3])
			#print op,stuff
		print ''

if __name__=='__main__':
	print_markdown_documentation()
		
	
