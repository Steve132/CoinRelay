import pybitcointools
from secure_random import secure_random
from binascii import hexlify
from google.appengine.ext import ndb
import splitasm


class SplitRule(ndb.Model):
	address=ndb.StringProperty(required=True)
	address_private_key = ndb.StringProperty(reqired=True,indexed=False)
	last_triggered=ndb.DateTimeProperty(auto_now_add=True)
	auto_trigger=ndb.BooleanProperty(default=True)
	runtime_function_code=ndb.PickleProperty()

#trigger on address add
									#There can only be one splitrule with the associated address in the DB
									#When language launches, convert entire DB for maintenance

def split(targets,address_private_key=None,auto_trigger=True):
	if(not address_private_key):
		address_private_key=hexlify(secure_random(32))

	address=pybitcointools.privkey_to_address(address_private_key)
	
def trigger(address):
	sr=SplitRule.get(key_name=address)
	if(not sr):
		raise NoRuleException()

	
	


class NoRuleException(Exception):
	def __init__(self):
		super(NoRuleException,self).__init__("No rule associated with this address")
