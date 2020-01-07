'''
Description : 	This script basically displays/refreshes a concise list of top ranked crypto currencies.

Usage		: 	cryptoPrices.py <parameters_not_yet_thought_of>

Author		:	Saikat Biswas

References : 	
				https://docs.bitfinex.com/v2/reference
				https://min-api.cryptocompare.com/
				https://coinmarketcap.com/api/
				https://www.cryptocompare.com/api
				https://www.binance.com/restapipub.html
				
				http://cryptocurrenciesstocks.readthedocs.io/overview.html				#Genereal API consoloditaion from various exchanges
				
'''

from __future__ import print_function
from time import sleep
import urllib2
import json
from pprint import pprint
import subprocess
import os
import sys

'''
#Complete Ticker list (67 tickers) for reference
ticker_list = ["tBTCUSD","tLTCUSD","tLTCBTC","tETHUSD","tETHBTC","tETCBTC","tETCUSD","tRRTUSD","tRRTBTC","tZECUSD","tZECBTC","tXMRUSD","tXMRBTC","tDSHUSD","tDSHBTC","tBCCBTC","tBCUBTC","tBCCUSD","tBCUUSD","tBTCEUR","tXRPUSD","tXRPBTC","tIOTUSD","tIOTBTC","tIOTETH","tEOSUSD","tEOSBTC","tEOSETH","tSANUSD","tSANBTC","tSANETH","tOMGUSD","tOMGBTC","tOMGETH","tBCHUSD","tBCHBTC","tBCHETH","tNEOUSD","tNEOBTC","tNEOETH","tETPUSD","tETPBTC","tETPETH","tQTMUSD","tQTMBTC","tQTMETH","tBT1USD","tBT2USD","tBT1BTC","tBT2BTC","tAVTUSD","tAVTBTC","tAVTETH","tEDOUSD","tEDOBTC","tEDOETH","tBTGUSD","tBTGBTC","tDATUSD","tDATBTC","tDATETH","tQSHUSD","tQSHBTC","tQSHETH","tYYWUSD","tYYWBTC","tYYWETH"]
'''
url_cryptocompare_price	= "https://min-api.cryptocompare.com/data/pricemulti?fsyms=BTC,ETH,DASH&tsyms=BTC,USD,EUR"

url_bitfinex_status		= "https://api.bitfinex.com/v2/platform/status"
url_bitfinex_symbols	= "https://api.bitfinex.com/v1/symbols"
url_bitfinex_price		= "https://api.bitfinex.com/v2/ticker/"						#eg. :: "https://api.bitfinex.com/v2/ticker/tBTCUSD"
url_bitfinex_candles 	= "https://api.bitfinex.com/v2/candles/trade"				#eg. :: "https://api.bitfinex.com/v2/candles/trade:15m:tBTCUSD/hist"

ticker_list 			= []
retries					= 3															#No. of retries to server when not responding
cool_down_period		= 15														#No. of seconds to wait before requesting the server again. Waits cool_down_period*iteration (secs), where iteration<retries
lookback_columns_count	= 11

#ignore_ticker_list		= ["*ETH", "BTG*", "ETPETH"]								#Add "*" to substitute the cryptocurrency with all possible symbols
#ignore_ticker_list		= ["*ETH"]
ignore_ticker_list		= ["*ETH", "*USD"]

#fav_ticker_list		= ["tBTCUSD"]												#Adds these tickers to ticker_list, no matter what
fav_ticker_list			= ["tBTCUSD","tLTCUSD","tLTCBTC","tETHUSD","tETHBTC","tXRPUSD","tXRPBTC","tIOTUSD","tIOTBTC","tXMRUSD","tXMRBTC"]

class CryptoPrices:
	ticker			= ""
	ticker_content 	= None							#Ticker json data in the form of python list
	candle_content 	= None	

	current_price	= 0
	url_bitfinex_candles	= ""
	url_bitfinex_price		= ""
	
	def __init__(self, ticker, duration):
		self.ticker 		= ticker
		self.ticker_content = None
		self.candle_content = None
		
		self.current_price 	= 0
		
		self.url_bitfinex_price		= url_bitfinex_price + ticker
		self.url_bitfinex_candles	= url_bitfinex_candles + ":" + duration + ":" + ticker + "/hist" 
		
		self.check_api_server_status()
		
	def check_refresh_print(self, duration):
		for i in range(duration,0,-1):
			print (str(i) + " second(s) left..", end='\r')
			sleep(0.5)
		print ("Task completed successfully..    ")
		
	def check_clear_screen(self, duration):
		for i in range(duration,0,-1):
			print (str(i) + " second(s) left..")
			#subprocess.call("clear")
			sleep(0.5)		
			os.system("cls")
	
	#Requesting specific data from url and exits if not successfull. Returns the json data list
	def request_data_once(self, url):
		
		#print ("Requesting data for " + url + ".. ")
		raw_data = ""
		
		try:
			raw_data	= urllib2.urlopen(url)
		except Exception as e:
			#print ("Could not request server, error = %s" %e)
			#sys.exit(1)
			pass
			
		if raw_data=="" or raw_data.getcode() != 200:			#Exits if status is not 200
			#print ("Bad response for " + url)
			#sys.exit(1)
			return []
			
		output	= json.loads(raw_data.read())
		#pprint(output)
		
		return output

	#Requests server for a fixed number of times after waiting for a while, when server is not responding.
	def request_data(self, url):
		count = 0
		while True:
			output = self.request_data_once(url)
			if not output == []:
				return output
			count = count + 1
			if (count<=retries):
				waiting_time = cool_down_period*count
				#print ("API Server not responding to requests. Trying again in %s secs.." %waiting_time)
				sleep(waiting_time)
			else:
				break
		print ("Server is not responding after " + str(retries) + " retries. Please try again after some time. Exiting process..")
		sys.exit(1)
		
	#Checks the API Server status and proceeds if it is responding	
	def check_api_server_status(self):
		server_status_response = self.request_data(url_bitfinex_status)
		if not server_status_response[0]==1:
			print ("Bitfinex API server not operative. Exiting..")
			sys.exit(1)
		
	#Processes and calculates percent change in price, between each columns/duration of the candles
	def parse_candle_data(self):

		percent_list		= []
		self.current_price 	= old_price = float(self.candle_content[0][2])
		#print (self.ticker[1:] + " " + str("%0.4e" %self.current_price), end=',')
		print (self.ticker[1:] + " " + str("%0.4e" %self.current_price) + "\n")
		
		for trade in self.candle_content[1:lookback_columns_count]:
			trade = [ float(x) for x in trade ]											#Typecasts all string elements in candle_content to float
			percent_change = ((old_price - trade[2])/trade[2])*100						#We always use the closing price in our calculation. "old_price" in the sense it was trade[2] in the previous iteration. In reality, "old_price" is more like recent_price

			#print ("\t%0.4f (%s%.2f%%)" %(trade[2], indicator, percent_change), end=',')
			#print ("\t%s (%s)" %(format_float(trade[2]), format_percent_change(percent_change)), end=',')	
			print ("%s \t (%s)" %(format_float(trade[2]), format_percent_change(percent_change)))	
			
			percent_list.append(percent_change)											#Saving the percent changes to a list
			
			old_price = trade[2]					

		#Handling the cumulutative percent list	
		percent_list = generate_cumulative_list(percent_list)
		percent_list = ", ".join([("%s" %format_percent_change(per_change)) for per_change in percent_list])
		#print ("\t\t[" + percent_list + "]\n")
		print ("\n[" + percent_list + "]\n\n")

	#Returns True, if word is present in myList, returns False otherwise	
	def compare_string_in_list(self, word, myList):
		for ignoreTicker in myList:
			i = 0
			while (i<len(ignoreTicker)):
				if ignoreTicker[i] == "*" or ignoreTicker[i] == word[i]:				#If character is * or it matches we look further
					i = i + 1
					continue
				else:
					break
			if i == len(ignoreTicker):													#If word was matched till the end return True
				return True
		return False																	#Returns False if the word could not be matched in the list
	
	#Returns a processed list of tickers after querying the API server
	def handle_ticker_list(self):
		global ignore_ticker_list
		
		#Get the list of tickers the server provide
		orig_ticker_list = self.request_data(url_bitfinex_symbols)
		orig_ticker_list = [ticker.upper() for ticker in orig_ticker_list]
		
		ticker_list		 	= []
		ignore_ticker_list	= [ ticker.replace("*","***") for ticker in ignore_ticker_list ]
		
		#Weeding out ETH trades and adding "t" to ticker
		
		for ticker in orig_ticker_list:
			if not self.compare_string_in_list(ticker, ignore_ticker_list):
				ticker_list.append("t" + ticker)
				
		return ticker_list
	
		
	def handle_candle(self):
		
		self.candle_content = self.request_data(self.url_bitfinex_candles)						#Requesting candle data from url
		self.parse_candle_data()																#Process candle data
		
	
	def handle_ticker(self):
		print ("Requesting ticker data for " + self.ticker + ".. ")
		content 			= urllib2.urlopen(self.url_bitfinex_price).read()	
		self.ticker_content = json.loads(content)		
		#pprint(self.ticker_content)	

#Returns the cumulative percent list, when feeded an input list
def generate_cumulative_list(myList):
	for i in range(len(myList)-1, 0, -1):
		myList[i-1] = myList[i-1] + myList[i]
	return myList
#Returns a signed formatted string decimal number	
def format_percent_change(value):
	new_val = str("%0.2f%%" %value)
	if value>=0.0:
		return "+" + new_val
	else:
		return new_val	
		
#Returns only the significant digits of the value without any "." or "e". Not Scalable or comparable with other AltCoins, but only among itself	
def format_float(value):
	significant_val = ("%0.4e" %value).split("e")[0].replace(".","")
	return significant_val
	
def main():
	global ticker_list
	
	candle_duration	= "15m"	
	
	
	#When we want to obtain the list of tickers generically. Mostly when we want a full analysis. 
	#When this is commented we append from fav_ticker_list anyways. SO only those tickers come in to play, and we need not care about ignore_ticker_list then
	
	altCoin_prices 	= CryptoPrices("", "")
	ticker_list		= altCoin_prices.handle_ticker_list()
	
	ticker_list		= sorted(list(set(ticker_list).union(fav_ticker_list)))				#Adding  tickers in fav_ticker_list explicitly. Sorting it for better comparison.
	
	for currentTicker in ticker_list:
		cryptoPrices = CryptoPrices(currentTicker, candle_duration)
		cryptoPrices.handle_candle()
		#pass
	#cryptoPrices.check_refresh_print(5)
	#cryptoPrices.check_clear_screen(5)
	
main()