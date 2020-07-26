from flask import Flask
from flask import request
from flask import render_template
from flask import make_response
from flask import redirect

import requests
import json
import threading
from http import cookies
from flask import jsonify
import ast

app = Flask(__name__)

results = []


@app.route("/buy", methods = ["GET", "POST"])
def buy():

	if (request.method == "POST"):

		itemId = request.form.get("id")
		name = request.form.get("name")
		quantity = int(request.form.get("quantity"))
		unitPrice = request.form.get("unitPrice")
		
		unitPrice = int(standardizePrice(unitPrice))
		
		totalPrice = unitPrice * quantity
		
		print(itemId, name, quantity, unitPrice, totalPrice)
		
		slot = []
		
		slot.append(itemId)
		slot.append(name)
		slot.append(quantity)
		slot.append(unitPrice)
		slot.append(totalPrice)
		
		#Slot 1:
		#[Item ID, Name, Quantity, unitPrice, totalPrice]
		#[50, Shortbow (u), 100, 11, 1100]
		
		slots = []
		if ("slots" in request.cookies):
		
			slots = request.cookies.get("slots")
			slots = ast.literal_eval(slots)
			
		slots.append(slot)
		
		#Slots:
		#[[Slot 1], [Slot 2], [Slot 3], [Slot 4], [Slot 5], [Slot 6], [Slot 7], [Slot 8]]
		#[[50, Shortbow (u), 100, 11, 1100], [20997, Twisted bow, 2, 1.2b, 2.4b]]
		
		
		res = make_response(redirect("/"))
		res.set_cookie("slots", str(slots))
		
		
		return res


@app.route("/", methods = ["GET", "POST"])
def home():
	
	if ("slots" in request.cookies):
		slots = request.cookies.get("slots")
		slots = ast.literal_eval(slots)
	else:
		slots = []
	
	
	if (request.method == "GET"):
	
		return render_template("index.html", slots = slots)
			
	else:
		
		results.clear()
		text = request.form.get("name").lower()
		
		print(text)
		url = "https://rsbuddy.com/exchange/summary.json"
		
		response = requests.get(url).json()
		
		items = {}
		items = response
		
		entry = []
		count = 0
		
		for id in items:
		
			if (items[id]["name"].lower().find(text) > -1):
			
				count = count + 1
				entry.append(id)
				
			if (count >= 10):
				break
				
		threads = []
		
		for i in range (0, count):
			t = threading.Thread(target = getPrices, args = (entry[i],))
			t.start()
			threads.append(t)
		
		for thread in threads:
			thread.join()
		
		print(results)
		
		return render_template("index.html", items = results, slots = slots)
		
	
def standardizePrice(price):

	#Possible Prices:
	
	#Price: 1 - 999 => do nothing
	#Price: 1,000 - 9,999 => 1000 - 9999 #price.replace(",", "")
	#Price: 10.0k - 999.9k => 10000 - 999900 #price.replace(".", ""), price.replace("k", "00")
	#Price: 1.0m - 999.9m => 1000000 - 999900000 #price.replace(".", ""), price.replace("m", "00000")
	#Price: 1.0b - 2.1b => 1000000000 - 2100000000 #price.replace(".", ""), price.replace("b", "00000000")

	price = price.replace(",", "")
	price = price.replace(".", "")
	price = price.replace("k", "00")
	price = price.replace("m", "00000")
	price = price.replace("b", "00000000")

	return price
	
def getPrices(id):

	url = "https://secure.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item=" + id
	
	response = requests.get(url).json()
	
	item = {}
	item = response["item"]
	
	data = []
	
	data.append(id)
	data.append(item["name"])
	data.append(item["current"]["price"])
	
	results.append(data)

	

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)