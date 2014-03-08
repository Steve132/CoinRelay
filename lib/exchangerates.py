import blockchain
from datetime import datetime,timedelta

rates=blockchain.getexchangerates()
last_rates=datetime.utcnow()

def _update_rates():
	global rates
	global last_rates
	n=datetime.utcnow()
	if((n-last_rates).total_seconds() > 60):		#one minute update exchange rates
		rates=blockchain.getexchangerates()
		last_rates=n
	return rates

def _ratelookup(code,direction='last'):
	rate=_update_rates()
	code=code.strip().upper()
	if(code=='XBT' or code=='BTC'):
		return 1.0
	else:
		return rate[code]['last']
		

def convert(amount,from_code,to_code):
	rate=_ratelookup(to_code,'sell') / _ratelookup(from_code,'buy')
	return amount*rate
