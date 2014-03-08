#Idea:  Generate a google site that allows a single API call: generate address

#Generate address takes in a list of >1 address:integer pairs.  The sum of the integers is the total, and each integer divided by the total
#gives the fraction of incoming BTC that hits that address.

#On a payment hit, dump ALL of the unspent outputs from the address
#The only return value of the function is the REAL private key of the address (this is to allow the user to have the coins if blockchain or coinsplit goes down

#Alternately, only one call "fracture key": upload the private key and this causes a split.

#We take a %0.1 fee after mining fees.  (thats 

#We could even actually make a little DSEL (no loops) and embed it into the system to be compiled.  Then, dynamically parse and then "compile" the DSEL to python code.
#WARNING, securely hash all variable names so that way people can't embed code into python.

#This is actually REALLY cool.

#Advanced mode is fine

#Allow manual triggering of an API...but time-limited (last_trigger_time)
#Hardcoded functions for features

#use marshal
