import sqlite3
from sqlite3 import Error
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

def get_name(ID): # Returns employees' name by Telegram id
	conn = sqlite3.connect('IDS.db')
	cur = conn.cursor()
	q = "select NAME from IDS where ID = {}".format(ID)
	res = cur.execute("select count(NAME) from IDS where ID = {}".format(ID))
	for i in res:
			falg = i[0] > 0
	if falg:
		res = cur.execute(q)
		for i in res:
				name = i[0]
	else:
		name = 'NO'
	conn.close()
	return name

def insert_name(ID, name): # Adds new user to the database
 	conn = sqlite3.connect('IDS.db')
 	cur = conn.cursor()
 	if get_name(ID) == 'NO':
 		q = "insert into IDS (ID,NAME) values ({},'{}')".format(ID,name)
 		cur.execute(q)
 		conn.commit()
 	else:
 		q = "update IDS set NAME = '{}' where ID={}".format(name,ID)
 		cur.execute(q)
 		conn.commit()
 	conn.close() 

def get_statuses(): # Parses google form and gets possible ftatuses
	statuses = []
	text = requests.get('https://docs.google.com/forms/d/e/1FAIpQLScTYOs-Z7qggWYZoldE-pA7zWMHqh1svjLhtTVu7b_V4mwNkw/viewform')
	soup = BeautifulSoup(text.content, 'html.parser')
	for i in soup.find_all('span'):
	  try:
	    if i['dir'] == 'auto':
	      if len(i.text.split(' ')) != 2:
	        if i.text[-1] != ':': statuses += [i.text]
	  except:
	    pass
	return statuses

def get_names(): # Parses google form and gets possible names
	names = []
	text = requests.get('https://docs.google.com/forms/d/e/1FAIpQLScTYOs-Z7qggWYZoldE-pA7zWMHqh1svjLhtTVu7b_V4mwNkw/viewform')
	soup = BeautifulSoup(text.content, 'html.parser')
	for i in soup.find_all('span'):
	  try:
	    if i['dir'] == 'auto':
	      if len(i.text.split(' ')) == 2:
	        names += [i.text]
	  except:
	    pass
	return names

def no_report_today(user_id): # Parses given answers and checks if todays report already exists 
	r = requests.get('https://docs.google.com/spreadsheet/ccc?key=1orkTbC4G8vcYlyDdPZPS3gZRBa2XT2CBMErj6U6myYk&output=csv')
	data = r.content
	df = pd.read_csv(BytesIO(data), index_col=0)
	name = get_name(user_id)
	return name not in df[df['Date'] == str(datetime.now().month)+'/'+str(datetime.now().day)]['Employee'].values
 
def insert_report(name, status, comment = None): # Submits post request to the server
	url = 'https://docs.google.com/forms/d/e/1FAIpQLScTYOs-Z7qggWYZoldE-pA7zWMHqh1svjLhtTVu7b_V4mwNkw/formResponse'
	day = datetime.now().day
	month = datetime.now().month
	form_data = {
	"entry.1618580712_day":day,
	"entry.1618580712_month":month,
	"entry.1266868708":status,
	"entry.1962697237":name
	}
	if comment is not None: 
		form_data['entry.1063605673'] = comment
	requests.post(url, data=form_data)
	return 'Отчет отправлен!'

if __name__ == '__main__':
	#print('Functions live here')
	r = requests.get('https://docs.google.com/spreadsheet/ccc?key=1orkTbC4G8vcYlyDdPZPS3gZRBa2XT2CBMErj6U6myYk&output=csv')
	data = r.content
	df = pd.read_csv(BytesIO(data), index_col=0)
	print df
