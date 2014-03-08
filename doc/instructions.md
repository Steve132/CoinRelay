Control
-------------
Opcode | Summary | Description | Arguments
-------|---------|-------------|----------
return|return|Immediately stop executing the script|None
endif|endif|Must be preceded by a matching 'if'.  Ends a control block for an if statement   |None
nop|no-op|Does nothing.|None
if|if not 0|If the top of the stack is not 0, then find the matching endif and execute the code between them.  Otherwise jump to the matching endif.  Can be nested|None

Information
-------------
Opcode | Summary | Description | Arguments
-------|---------|-------------|----------
price|price currency conversion|Based on the <conversiondirection>, does a conversion of currency.  Converts the value on top of the stack.  Conversion direction is a concatination of iso currency codes (case-insensitive) such as 'usdbtc' to find the number of bitcoin you could buy with the usd value on the stack,  or 'usdeur' or 'xbteur'.  Bitcoin can be listed as xbt or btc.|<conversiondirection> is the direction of currency conversion 6-character string
timestamp|get time of event|Based on the <argument>, pushes several different kinds of unix timestamps onto the stack.  If <argument> is a bitcoin address, look at the blockchain to determine 	the last time the private key for the address was used to sign a transaction on the network.  If <argument> is the string "now", it pushes the unix timestamp for the current time on the stack.  If <argument> is  	a comma,period,hyphen,colon,or space -seperated date, largest denomination first (such as <2021-5-21> or <2051-1-21 13:42:23>, then calculate the appropriate unix timestamp and push it on the stack |<argument> is the kind of timestamp to fetch.
balance|get balance|Checks the blockchain for the balance in bitcoin for the given <address>.  Puts the balance (in nanoXBT) onto the stack | <address> Must be a valid bitcoin address.  The address balance to check
rate|get exchange rates|Based on the <conversiondirection>, gets the current exchange rate and puts it on the stack. See price command for information.  |<conversiondirection> is the direction of currency conversion 6-character string
blockheight|get blockheight|Checks the blockchain for the current block height, puts it into the stack|None

Transactions
-------------
Opcode | Summary | Description | Arguments
-------|---------|-------------|----------
reflect|send bitcoin to source|Pop the top item off of the stack, interpret it as the amount of nanoXBT to send to the address that initiated this transaction.  Append that destination and amount to the current transaction|None
pushtx|send bitcoin|Pop the top item off of the stack, interpret it as the fee in nanoXBT to use in the current transaction. Broadcast the current transaction to the blockchain immediately and reset the current transaction|None
send|send bitcoin|Pop the top item off of the stack, interpret it as the amount of nanoXBT to send to <address>.  Append that destination and amount to the current transaction  |<address> Must be a valid bitcoin address, the address to send to

Memory
-------------
Opcode | Summary | Description | Arguments
-------|---------|-------------|----------
bury|st[-1]->st[p]|Pop the top item off the stack, then insert it into to position p in the stack, where 0 is the bottom of the stack.|<position>...Must be an integer...The template argument for the position to go to.  May be negative to count back off the top of the stack
fetch|st[p]->st[-1]|Go to position p in the stack, where 0 is the bottom of the stack.  Retrieve the item there, remove it, and put it on the stack|<position>...Must be an integer...The template argument for the position to go to.  May be negative to count back off the top of the stack
dup|st[-1]->st[-1],st[-2]|Duplicate the top element of the stack and put the copy on the stack.|None

Logic
-------------
Opcode | Summary | Description | Arguments
-------|---------|-------------|----------
greaterequal|(st[-2] >= st[-1])->st[-1]|Pop the top two elements.  If the first one is greater than or equal to the second, push 1.  Otherwise push 0.|None
less|(st[-2] < st[-1])->st[-1]|Pop the top two elements.  If the first one is less than the second, push 1.  Otherwise push 0.|None
greater|(st[-2] > st[-1])->st[-1]|Pop the top two elements.  If the first one is greater than the second, push 1.  Otherwise push 0.|None
not|(!st[-1])->st[-1]|Pop the top element.  If it is not 0, push 0 onto the stack.  Otherwise push 1 onto the stack|None
equal|(st[-1]==st[-2])->st[-1]|Pop the top two elements.  If they are the same, push 1 onto the stack.  Otherwise push 0.|None
or|(st[-2] or st[-1])->st[-1]|Pop the top two elements.  If either is not 0, push 1 onto the stack.  Otherwise push 0 onto the stack|None
lessequal|(st[-2] <= st[-1])->st[-1]|Pop the top two elements.  If the first one is less than or equal to the second, push 1.  Otherwise push 0.|None
notequal|(st[-1]!=st[-2])->st[-1]|Pop the top two elements.  If they are not the same, push 1 onto the stack.  Otherwise push 0.|None
and|(st[-2] && st[-1])->st[-1]|Pop the top two elements.  If both are not 0, push 1 onto the stack.  Otherwise push 0 onto the stack|None

Arithmetic
-------------
Opcode | Summary | Description | Arguments
-------|---------|-------------|----------
mod|st[-2] % st[-1]->st[-1]|Pop the top two elements,divide the first element by the second, and push the remainder onto the stack|None
abs|abs(st[-1])->st[-1]|Pop the top element and push the absolute value onto the stack|None
min|min(st[-2],st[-1])->st[-1]|Pop the top two elements,push the smallest one back onto the stack|None
bitor|(st[-1] or st[-2])->st[-1]|Pop the top two elements, treat them as binary integers and compute an OR operation between all pairs of bits. push the result onto the stack|None
random|random(0,x)|Pops the top of the stack, then generates a random integer between 0 and st[-1]-1,inclusive, and pushes it on the stack|None
bitinvert|~st[-1]->st[-1]|Pop the top element, treat it as a binary integer and flip all the bits.  push the result onto the stack|None
max|max(st[-2],st[-1])->st[-1]|Pop the top two elements,push the largest one back onto the stack|None
minus_fee|st[-1]-=$default_fee|Subtracts the current default suggested transaction fee from the value on top of the stack|None
div|st[-2]/st[-1]->st[-1]|Pop the top two elements,divide the first element by the second, and push the result onto the stack|None
bitxor|(st[-1] ^ st[-2])->st[-1]|Pop the top two elements, treat them as binary integers and compute an Exclusive-OR operation between all pairs of bits. push the result onto the stack|None
bitand|(st[-1] & st[-2])->st[-1]|Pop the top two elements, treat them as binary integers and compute an AND operation between all pairs of bits. push the result onto the stack|None
sub|st[-2]-st[-1]->st[-1]|Pop the top two elements,subtract the second element from the first, and push the result onto the stack|None
add|st[-2]+st[-1]->st[-1]|Pop the top two elements, add them, and push the result onto the stack|None
lshift|st[-2] << st[-1]->st[-1]|Pop the top two elements,multiply the first element by 2^second, and push the result onto the stack|None
mul|st[-2]*st[-1]->st[-1]|Pop the top two elements,multiply them, and push the result onto the stack|None
pow|st[-2]^st[-1]->st[-1]|Pop the top two elements, and use the second element as the exponent of the first.  Push the result onto the stack|None
nano|constant float to integer|Since there are only integers on the stack and most currency quantities are nanoX...its helpful to be able to load the stack using a float to count nanoelements.  Multiplies 	the floating point value in <arg> by 1e9, and converts it to an integer and puts it on the stack|<arg> a floating point to convert to nano-elemnts and put on the stack
rshift|st[-2] >> st[-1]->st[-1]|Pop the top two elements,divide the first element by 2^second, and push the result onto the stack|None

