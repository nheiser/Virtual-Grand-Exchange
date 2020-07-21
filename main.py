from flask import Flask
from flask import request
from flask import render_template
from flask import make_response
from flask import redirect

import requests
import json

app = Flask(__name__)

@app.route("/", methods = ["GET", "POST"])
def home():
	
	if (request.method == "GET"):
	
		return render_template("index.html")
	
	else:
	
		text = request.form.get("name").lower()
		#tolower
		url = "https://rsbuddy.com/exchange/summary.json"
		
		response = requests.get(url)
		response = response.json()
		
		items = {}
		items = response
		
		
		itemDict = []
		#itemDict = {}
		
		for id in items:
		
			entry = []
		
			if (items[str(id)]["name"].lower().find(text) > -1):
				entry.append(id)
				entry.append(items[str(id)]["name"])
				#entry = {id, items[str(id)]["name"]}
				print(entry)
				itemDict.append(entry)
				#itemDict[id] = items[str(id)]["name"]
				#print(id, items[str(id)]["name"])
			
		return render_template("index.html", items = itemDict)
	

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)