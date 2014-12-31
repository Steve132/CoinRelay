import pybitcointools
from secure_random import secure_random
from binascii import hexlify
from google.appengine.ext import ndb
import googleappengine

class RegisteredListener(ndb.Model):
	address=ndb.StringProperty(required=True)
	address_private_key = ndb.StringProperty(required=True,indexed=False)
	last_triggered=ndb.DateTimeProperty(auto_now_add=True)
	auto_trigger=ndb.BooleanProperty(default=True)
	runtime_function_code=ndb.BlobProperty(indexed=False)

#There can only be one address associated with the PK
def update(source_code,address_private_key=None):
	if(not address_private_key):
		address_private_key=hexlify(secure_random(32))

	address=pybitcointools.privkey_to_address(address_private_key)
	
class NoRuleException(Exception):
	def __init__(self):
		super(NoRuleException,self).__init__("No rule associated with this address")
