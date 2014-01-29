import wikipedia
import math
from flask import Flask, request, redirect
import twilio.twiml
from wikipedia import DisambiguationError
import pymongo
from pymongo import MongoClient

# Setup server/DB
client = MongoClient()
db = client['MyApp']
searched = db['searched']
app = Flask(__name__)

# If not using MongoDB -----------------------------
# Using a dictionary of objects
#savedSearches = {}
#class SavedSearch:
	#'Class for saving searches to use later'
	
	#def __init__(self, message, suggestions, site):
		#self.message = message
		#self.suggestions = suggestions
		#self.site = site
#-------------------------------------------------

@app.route("/", methods=['GET', 'POST'])
def quickFacts():
	body = request.values.get('Body', None)
	
	# Empty message handling
	if body == None or body == "" or body.count(" ") == len(body):
		return(str(twilio.twiml.Response()
		       .message("Please don't send blank texts\n Thanks!")))
		
	
	# Using MongoDB --------------------------------------
	check = searched.find_one({"query" : body.lower()})
	resp = twilio.twiml.Response()
	if not check == None:
		# If search is saved in the DB, reuse value
		message = check['message']
		suggestions = check['suggestions']
		site = check['site']
		print("dat mongo")
	else:
		# If search is unique, search Wikipedia
		try:
			message, suggestions, site = getWikiString(body)
			resp.message(message[0:len(message)/2]
			 + message[(len(message)/2):(len(message)-1)]
			 + "\nMore Info: en.m.wikipedia.org/wiki/" + site
			 + "\n\n"
			 + suggestions
			 + "\n\nYou're welcome!")
		except:
			
			message = "I couldn't find anything on what you were looking for. Please try again."
			resp.message(message)
	# -----------------------------------------------------
	
    #If not using MongoDB -------------------------------------
	#if body.lower() in savedSearches:
		#prevSearch = savedSearches[body]
		#message = prevSearch.message
		#suggestions = prevSearch.suggestions
		#site = prevSearch.site
	#else:
		#message, suggestions, site = getWikiString(body)
	#----------------------------------------------------------
	
	return str(resp)
	
def getWikiString(body):
	# Prints number and request on terminal - debugging
	from_number = request.values.get('From', None)
	print(str(from_number) + " requested: " + str(body))
	
	# Get a list of searches using opens source wikipedia library
	searches = wikipedia.search(body)
	
	# Handling case with no search results
	if len(searches) == 0:
		return(str(twilio.twiml.Response()
		       .message("I couldn't find anything, sorry")))
		
	# Wierd way to ensure no errors occur with the wikipedia library
	try:
		message = wikipedia.summary(searches[0], 3)
		site = searches[0]
		searches.remove(searches[0])
	except DisambiguationError:
		message = wikipedia.summary(searches[2], 3)
		site = searches[2]
		searches.remove(searches[2])
	except:
		message = wikipedia.summary(searches[1], 3)
		site = searches[3]
		searches.remove(searches[1])
	
	# formatting for the link
	site = site.replace(" ", "_")
	
	# formatting for suggestions
	suggestions = "Related: "
	formatting = 0
	for stuff in searches:
		# Removing user query from suggestions - redundant
		if stuff == body:
			continue
		if formatting == 0:
			suggestions = suggestions + "'" + stuff + "'"
			formatting = 1
		else:
			suggestions = suggestions + ", '" + stuff + "'"	
			
	suggestions += "."
	
	# Using MongoDB ------------------------------------
	# Inserting new document into DB
	newSearch = {
				 'query' : body.lower(), # all lower case to reliably access values
				 'message' : message,
				 'suggestions' : suggestions,
				 'site' : site
				} 
				
	searched.insert(newSearch)
	# ----------------------------------------------------
	
	#If not using MongoDB -------------------------------------------------
	#savedSearches[body.lower()] = SavedSearch(message, suggestions, site)
	#----------------------------------------------------------------------
		
	return (message, suggestions, site)

if __name__ == "__main__":
	app.run(debug=True)
