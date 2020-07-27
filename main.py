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
import secrets
from flask import session


secret_key = secrets.token_urlsafe(16)

app = Flask(__name__)
app.secret_key = "7BOXEyui_8wRiMOU0Pq6LQ"

slots = []


@app.route("/sell", methods = ["GET", "POST"])
def sell():

	if (request.method == "POST"):
	
		itemId = request.form.get("id")
		stock = int(request.form.get("stock"))
		quantity = int(request.form.get("quantity"))
		unitPrice = request.form.get("unitPrice")
	
		
		cleanPrice = int(standardizePrice(unitPrice))
		totalPrice = cleanPrice * quantity

		session["gold"] += totalPrice

		slots = session["slots"]

		for slot in slots:
			if (slot[0] == itemId):
				slot[2] -= quantity
				if (slot[2] == 0):
					slots.pop(0)
				break
				
		session["slots"] = slots
		
		return make_response(redirect("/"))


@app.route("/buy", methods = ["GET", "POST"])
def buy():

	if (request.method == "POST"):

		itemId = request.form.get("id")
		name = request.form.get("name")
		quantity = int(request.form.get("quantity"))
		unitPrice = request.form.get("unitPrice")
		
		if (quantity <= 0):
			#you cannot buy that amount
			return make_response(redirect("/"))
		
		cleanPrice = int(standardizePrice(unitPrice))
		totalPrice = cleanPrice * quantity
		
		if (session["gold"] < totalPrice):
			#you do not have enough gold
			return make_response(redirect("/"))
		
		
		session["gold"] -= totalPrice
		
		totalPrice = '{:,}'.format(totalPrice)
		
		print(itemId, name, quantity, unitPrice, totalPrice)
		
		slot = []
		
		slot.append(itemId)
		slot.append(name)
		slot.append(quantity)
		slot.append(unitPrice)
		slot.append(totalPrice)
		#slot.append(actualPrice)
		
		#Slot 1:
		#[Item ID, Name, Quantity, unitPrice, totalPrice]
		#[50, Shortbow (u), 100, 11, 1100]
		
		slots = []
		if ("slots" in session):
		
			slots = session["slots"]
			#slots = ast.literal_eval(slots)
			
		slots.append(slot)
		
		#Slots:
		#[[Slot 1], [Slot 2], [Slot 3], [Slot 4], [Slot 5], [Slot 6], [Slot 7], [Slot 8]]
		#[[50, Shortbow (u), 100, 11, 1100], [20997, Twisted bow, 2, 1.2b, 2.4b]]
		
		
		#res = make_response(redirect("/"))
		session["slots"] = slots
		
		return make_response(redirect("/"))


@app.route("/", methods = ["GET", "POST"])
def home():
	
	if ("gold" in session):
		gold = session["gold"]
	else:
		session.clear()
		session["gold"] = 100000000
		gold = session["gold"]
	
	gold = '{:,}'.format(gold)
	
	#s = requests.session()
	#s.cookies["foo"] = "bar"
	#print(s.cookies["foo"])
	#s.post('http://localhost/', params={'foo': 'bar'})
	#print(s.cookies)
	
	if ("slots" in session):
		slots = session["slots"]
		#slots = ast.literal_eval(slots)
		
		threads = []
		
		for i in range (0, len(slots)):
			
			t = threading.Thread(target = updatePrices, args = (slots[i],))
			t.start()
			threads.append(t)
		
		for thread in threads:
			thread.join()
			
		#print(slots)
		
		
	else:
		slots = []
	
	
	if (request.method == "GET"):
	
		return render_template("index.html", slots = slots, gold = gold)
			
	else:
		
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
		results = []
		
		for i in range (0, count):
			t = threading.Thread(target = getPrices, args = (results, entry[i],))
			t.start()
			threads.append(t)
		
		for thread in threads:
			thread.join()
		
		#print(results)
		
		return render_template("index.html", items = results, slots = slots, gold = gold)
		
	
	
	
def updatePrices(slot):
	
	url = "https://secure.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item=" + slot[0]
	
	response = requests.get(url).json()
	
	item = {}
	item = response["item"]
	
	slot.append(item["current"]["price"])
	
	
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
	
def getPrices(results, id):

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