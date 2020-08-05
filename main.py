from flask import Flask
from flask import request
from flask import render_template
from flask import make_response
from flask import redirect

import requests
import json
import threading
from flask import jsonify
import secrets
import datetime
from flask import session
import uuid


secret_key = secrets.token_urlsafe(16)

app = Flask(__name__)
app.secret_key = "7BOXEyui_8wRiMOU0Pq6LQ"


@app.route("/sell", methods = ["GET", "POST"])
def sell():

	if (request.method == "POST"):
	
		id = request.form.get("id")
		pos = request.form.get("pos")
		itemId = request.form.get("itemId")
		stock = int(request.form.get("stock"))
		quantity = int(request.form.get("quantity"))
		unitPrice = request.form.get("unitPrice")
	
		if (quantity <= 0):
			#you cannot buy that amount
			return make_response(redirect("/"))
		
		
		if (unitPrice <= 0):
			#database is down, you cannot buy this item now
			return make_response(redirect("/"))
		
		
		cleanPrice = int(standardizePrice(unitPrice))
		totalPrice = cleanPrice * quantity


		slots = session["slots"]

		if ( not slots[pos]["id"] == uuid.UUID(id)):
			return make_response(redirect("/"))
		
		session["gold"] += totalPrice

		newQuantity = slots[pos]["quantity"]
		
		newQuantity -= quantity
		slots[pos]["quantity"] = newQuantity
		
		newSlots = {}
		
		if (newQuantity <= 0):
			
			slots.pop(pos)
			for slot in slots:
				if (slot > pos):
					newSlots[str(int(slot) - 1)] = slots[slot]
				else:
					newSlots[slot] = slots[slot]
		
		
			slots = newSlots
			

		session["slots"] = slots
		print(session["slots"])
		
		return make_response(redirect("/"))


@app.route("/buy", methods = ["GET", "POST"])
def buy():

	if (request.method == "POST"):

		itemId = request.form.get("id")
		name = request.form.get("name")
		quantity = int(request.form.get("quantity"))
		unitPrice = request.form.get("unitPrice")
		icon = request.form.get("icon")
		
		if (quantity <= 0):
			#you cannot buy that amount
			return make_response(redirect("/"))
		
		cleanPrice = int(standardizePrice(unitPrice))
		totalPrice = cleanPrice * quantity
		
		if (session["gold"] < totalPrice):
			#you do not have enough gold
			return make_response(redirect("/"))
		
		slots = {}
		
		if ("slots" in session):
		
			slots = session["slots"]
		else:
			session["slots"] = {}
			
		length = len(slots) + 1
		
		if (length > 8):
			#you cannot buy any more items
			return make_response(redirect("/"))
		
		session["gold"] -= totalPrice
		
		
		totalPrice = '{:,}'.format(totalPrice)
		
		slot = {}
		
		slot["id"] = uuid.uuid4()
		slot["itemId"] = itemId
		slot["name"] = name
		slot["quantity"] = quantity
		#slot["quantity"] = '{:,}'.format(quantity)
		slot["unitPrice"] = unitPrice
		slot["totalPrice"] = totalPrice
		slot["icon"] = icon
		slot["currentPrice"] = unitPrice
		
		session["slots"][str(length)] = slot
		
		print(session["slots"])
		
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
	
	if ("slots" in session):
		slots = session["slots"]
		
		if ("updated" not in session or needUpdate(session["updated"])):
		
			threads = []
			
			for slot in slots:
			
				t = threading.Thread(target = updatePrices, args = (slots, slot))
				t.start()
				threads.append(t)
		
			for thread in threads:
				thread.join()
			
			session["updated"] = datetime.datetime.now()
		
	else:
		slots = {}
	
	
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
		
			if (text in items[id]["name"].lower()):
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
		
		results.sort()
		
		return render_template("index.html", items = results, slots = slots, gold = gold)
		
		
def needUpdate(date):

	newDate = datetime.datetime.now()
	
	time_diff = newDate - date

	seconds = time_diff.total_seconds()
	minutes = seconds / 60
	
	if (minutes >= 30):
		return True
		
	return False
	
	
def updatePrices(slots, pos):
	
	url = "https://secure.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item=" + slots[pos]["itemId"]
	
	response = requests.get(url).json()
	
	item = {}
	item = response["item"]
	
	slots[pos]["currentPrice"] = item["current"]["price"]
	
	
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
	
	name = item["name"]
	
	data.append(id)
	data.append(name)
	data.append(item["current"]["price"])
	data.append(item["icon"])
	
	name.replace(" ", "+")
	
	url = "https://secure.runescape.com/m=itemdb_oldschool/" + name + "/viewitem?obj=" + id
	
	data.append(url)
	
	results.append(data)


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)