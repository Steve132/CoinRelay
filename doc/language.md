CoinRelay Language Reference and Tutorial
===================

Introduction
--------------

This document is the language reference and tutorial for the CoinRelay language version 1.0.  It describes the syntax and grammar for CoinRelay scripts.  

Computational Model
-----------

####Runtime Model

CoinRelay scripts are written to be attached to bitcoin address and private_key pair at runtime (called the 'host address' or just 'host').  This implicit address represents the address that is 'executing' the script.
The host address is a part of the runtime environment of each script.  In addition, the script is executed in response to a transaction that deposits unspent outputs into the host address.  Upon detecting a transaction that 
directs outputs to the host address, the client loads, compiles, and executes the script that is registered to that address.  

The first address on the inputs is called the 'source' address.


####Programming Model

The coinrelay computational model is of a simple stack machine with no dynamic loops, no subroutines and no recursion.  There is only one dynamic data type: Integer.  The 'stack' is a data structure of first-in-last-out integers.   The 'top' of the stack is the most recently added integer.

In addition to the stack there are also 'environment literals'. This is an $ followed by an alphanumeric string.  There is a fixed set of alphanumeric strings that correspond to integer values that the interpreter populates at runtime.  For example,  '$default_fee' expands to the current minimum recommended transaction fee at the time of executing the script.  A full list of all currently supported environment literals is below

CoinRelay source code is a series of whitespace-delimited 'commands'.  Each space-seperated 'command' in CoinRelay is a single instruction that performs some operation on the stack, usually reading inputs from the stack and pushing outputs onto the stack.  Commands may have additional side-effects that do not effect the stack, such as sending a transaction or modifying an environment variable.   Commands are executed in-order from first to last in the text file, ignoring whitespace.  

There are three types of 'commands':
 * A literal integer.  A literal integer surrounded by whitespace in the command stream pushes that integer onto the stack.
 * An 'environment literal'.  This is a string literal with a '$' prefix that expands to an integer from the environment variables.  See below for the list of currently supported environment variables.
 * An 'instruction'.  This is an alphanumeric command in the command stream.  It corresponds to an operation that the stack machine will perform.

Furthermore, each instruction (but not literals) may have compile-time 'arguments', which are specified after the command inside opening '&lt;' and closing '&gt;' symbols.  Arguments are comma-seperated and are interpreted compile-time
according to the definition of the instruction.

A complete list of all instructions can be found in [doc/instructions.py](doc/instructions.py)

####List of Environment Literals

Literal| Description
-------|------------
$in    | The amount of bitcoin that was deposited into the host address during the transaction that triggered this instance of the script. (in nanoXBT, See below)
$balance | The amount of bitcoin that is unspent in the host address during the time of the transaction
$spent | This is the total amount that the script has spent so far by performing operations that append value to the current ready transaction
$default_fee | This is the current default fee recommendation


>#####VERY IMPORTANT note on currency:
>***All currency amounts are given in units of nanoXXX where XXX is the iso code for that currency.***  This breaks the convention of many other bitcoin systems for the following reasons:  
> * Because it is currency we wish to used fixed-point integer arithmetic so that our results are deterministic and do not depend on machine rounding-order.  This means we need some base exponent to convert fractional currencies to whole parts.
> * In order to reduce confusion and encourage simplicity the base exponent for all currencies should be the SAME.   
> * The smallest unit of measure of XBT/BTC is the 'satoshi' which is a base exponent of 1e8.  This means that all of our quantities have to be at least 1e8.  
> * 1e8 is not a metric prefix, and is thus hard to remember.  But 1e9 IS a metric prefix (1 billionth, or nano) and is 1000^3.

Tutorial
------------------

####Lesson 0: Hello, World

Your first coinrelay script is fairly simple.  You want to invoice a number of customers for orders, and instead of order numbers you want to use addresses on the blockchain for each order.  Because your product order is all a fixed
size, now all you have to do is make a new address for each order, then to check if it was paid you just check the blockchain.  Cool!  

Of course, you have to make sure that you actually get your money somehow, and manually going and sweeping all the orders is a pita.  Besides, you don't want your money in your main address MINE after you go through and sweep, you want it to show up IMMEDIATELY and get little pings on your phone.  

What you need is a coinrelay script that lets you generate new order addresses that when paid automatically forward to your account MINE.  Lets do it.

	#order_relay.csa
	$balance minus_fee 				#When you get a transaction on the order address, push the entire balance minus the fee on the stack
	send<1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3>	#Send it to your main address.
	$default_fee pushtx				#Use the default fee and push the transaction to the blockchain.

Cool!  Now, start your coinrelay client in one process with 

	$ python crcc.py listen &

Now, you may generate order addresses and add them to the DB in one command with 

	$ python crcc.py update order_relay.csa

The new address will be printed to stdout, and any funds sent to it will activate the script.

Lets examine that process a little more closely.  Suppose funds in the amount of 0.142 XBT come in to the host address.  Lets look a little closer at what happens.

Each command above is processed seperately.  Despite the use of formatting and whitespace to 'group' certain commands (such as $balance, and minus_fee), each command actually happens totally
independantly.  Lets take a look at what happens when the 0.142 XBT hits the host address.

Command | Stack | Description
--------|-------|------------
$balance|[142000000]|The balance of the account goes on the stack.  It is all unspent outputs, including the one that triggered the script.
minus_fee|[141900000]|The command 'minus_fee' subtracts the default fee of 0.0001 XBT from the top of the stack
send<1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3>|[]|The value on top of the stack is appended to the outgoing transaction, ready to be sent
$default_fee|[100000]|The default fee of 0.0001 XBT is put on top of the stack
pushtx|[]|The top of the stack is used as the fee, the current transaction is pushed to the blockchain, directing 0.1419XBT to the address 1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3

This is exactly what we want to happen.  Relay effective!

####Lesson 1: Splitting

Now imagine that your accountant turns to you and says "uh,oh...this isn't good.  We need to set aside 18% for corporate taxes for your LLC that is making the devices.  It can't all just funnel into your personal accounts."
No problem.  We are going to rewrite the above to account for that

	#order_taxes.csa
	$balance minus_fee 				#When you get a transaction on the order address, push the entire balance minus the fee on the stack
	18 mul 100 div				#Put $balance-fee)*(18/100) on the stack and make a copy
	send<1taxTPm9Jw9aaQD5J2kiVuEe3gV37pvsG>		#send %18 to taxes
	$balance minus_fee minus_spent			#Put whatever you haven't spent on the stack
	send<1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3>	#Send the rest to yourself
	$default_fee pushtx				#push the transaction to the network

Lets look at this line by line again


Command | Stack | Description
--------|-------|------------
$balance|[142000000]|The balance of the account goes on the stack.  It is all unspent outputs, including the one that triggered the script.
minus_fee|[141900000]|The command 'minus_fee' subtracts the default fee of 0.0001 XBT from the top of the stack
18	|[141900000,18]|Push the constant 18 on the stack.
mul	|[2554200000]| 141900000*18
100	|[2554200000,100] | Push 100 on the stack
div	|[25542000]|2554200000/100
send<1taxTPm9Jw9aaQD5J2kiVuEe3gV37pvsG> |[]|The value on top of the stack is appended to the outgoing transaction, ready to be sent to the address
$balance|[142000000]|The balance of the account (from the beginning)
minus_fee|[141900000]|Subtract the fee
minus_spent|[116358000]| Subtract the total current spent amount of 25542000
send<1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3>|[]|Send to self
$default_fee|[100000]|The default fee of 0.0001 XBT is put on top of the stack
pushtx|[]|The top of the stack is used as the fee, the current transaction is pushed to the blockchain.

Two important things to note with this example. The first has to do with percentages.  Notice that we do x*18 / 100.  The order matters.  
If we did x/100,*18, we'd possibly truncate some digits of the integer.  This doesn't matter, but if our percentage was much more accurate, like 1224231241/10000000000, then truncating the bottom 10 digits would be extremely bad/erroneous.

The second thing to notice is that we seem to be doing some work more than once.  Lets see if we can re-write it to avoid unnecessary calculation:

	$balance minus_fee 				#When you get a transaction on the order address, push the entire balance minus the fee on the stack
	dup 18 mul 100 div				#Put $balance-fee)*(18/100) on the stack and make a copy
	send<1taxTPm9Jw9aaQD5J2kiVuEe3gV37pvsG>		#send %18 to taxes
	minus_spent			#Put whatever you haven't spent on the stack
	send<1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3>	#Send the rest to yourself
	$default_fee pushtx				#push the transaction to the network

This looks weird, but lets see how it works

Command | Stack | Description
--------|-------|------------
$balance|[142000000]|The balance of the account goes on the stack.  It is all unspent outputs, including the one that triggered the script.
minus_fee|[141900000]|The command 'minus_fee' subtracts the default fee of 0.0001 XBT from the top of the stack
dup	|[141900000,141900000]|Duplicate the result
18	|[141900000,141900000,18]|Push the constant 18 on the stack.
mul	|[141900000,2554200000]| 141900000*18
100	|[141900000,2554200000,100] | Push 100 on the stack
div	|[141900000,25542000]|2554200000/100
send<1taxTPm9Jw9aaQD5J2kiVuEe3gV37pvsG> |[141900000]|The value on top of the stack is appended to the outgoing transaction, ready to be sent to the address
minus_spent|[116358000]| Subtract the total current spent amount of 25542000
send<1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3>|[]|Send to self
$default_fee|[100000]|The default fee of 0.0001 XBT is put on top of the stack
pushtx|[]|The top of the stack is used as the fee, the current transaction is pushed to the blockchain.

1 less operation.  Haha!

####Lesson 2: Nano and Rates

Suppose now you realize that you can't just keep all your profits in bitcoin.  Each one of your widgets has a fixed-cost of production of $23.42, and you need to actually be able to pay your suppliers!  If you 
don't reserve enough money in USD to pay for your widgets, then a fall in the price of bitcoin might make you insolvent while you get the parts ordered up...oh no! 

To fix this, we are going to set each order to automatically send bitcoin for the production costs to your wallet at coinbase that is set to auto-convert to USD.  The address for that is
1USDByngFScmVsgKXbSKFESqruuBaN3dx.   However, how do you *dynamically* reserve exactly $23.42 worth of bitcoin?  You could just pick an amount, but the poitn is that you need to respnd to changing exchange rates.

This is where the 'price' command comes in.  It reads an amount of currency on the stack and performs a currency conversion using the current market value (current implementations take it from blockchain.info).  It takes as 
an argument a six-character string 'XXXYYY' where XXX is the currency to convert from and YYY is the currency to convert to.

For example, picking up where we left off on our tax example, we are going to modify it to incorporate our fixed-cost of production

	$balance minus_fee 				#When you get a transaction on the order address, push the entire balance minus the fee on the stack
	dup 18 mul 100 div				#Put $balance-fee)*(18/100) on the stack and make a copy
	send<1taxTPm9Jw9aaQD5J2kiVuEe3gV37pvsG>		#send %18 to taxes
	minus_spent					#Put whatever you haven't spent on the stack

	23420000000					#$23.42 in nanoUSD
	price<usdbtc>					#Convert 23.42 from dollars to bitcoin using market rates at time of reciept
	send<1USDByngFScmVsgKXbSKFESqruuBaN3dx>		#send it to your coinbase wallet to be converted
	
	$balance minus_fees minus_spent			
	send<1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3>	#Send the rest to yourself
	$default_fee pushtx				#push the transaction to the network

Hopefully we don't need to analyze the stack trace of this example, but you can see how it works.

Of course, magic numbers like 23420000000 look really ugly in this code.   This brings us to our second command for this lesson: the 'nano' command.

The nano command lets us avoid these ugly constants.  It takes a single argument at compile time, a floating-point number to be converted to nano-units and truncated to an integer.  Our example becomes

	$balance minus_fee 				#When you get a transaction on the order address, push the entire balance minus the fee on the stack
	dup 18 mul 100 div				#Put $balance-fee)*(18/100) on the stack and make a copy
	send<1taxTPm9Jw9aaQD5J2kiVuEe3gV37pvsG>		#send %18 to taxes
	minus_spent					#Put whatever you haven't spent on the stack

	nano<23.24>					#$23420000000 on the stack
	price<usdbtc>					#Convert 23.42 from dollars to bitcoin using market rates at time of reciept
	send<1USDByngFScmVsgKXbSKFESqruuBaN3dx>		#send it to your coinbase wallet to be converted
	
	$balance minus_fees minus_spent			
	send<1C6wmFUj6HF9aqRZucWEMa7xuTr6Z8sQj3>	#Send the rest to yourself
	$default_fee pushtx				#push the transaction to the network

####Lesson 3: Control Flow

Coming soon

####Lesson 4: Timestamps

Coming soon

####Lesson 5: Reflection and Games

Coming soon





