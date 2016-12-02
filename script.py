from SPARQLWrapper import SPARQLWrapper, JSON
from BeautifulSoup import BeautifulSoup, Comment
import urllib
import re
from sets import Set
import json, nltk
from nltk.corpus import wordnet as wn
from nltk.stem.snowball import SnowballStemmer

with open('mapper.json') as data_file:    
    data = json.load(data_file)
stringMatch = "dbpedia.org"

NN = []
foo = []
NNP = []
properties = []
possibleProperties = []
possibleQuery = ""
typeMap = {}
abstractSentences = []
possibleProperties = []
queryString = ""
relevantSentences = []

def getTypeOfProperties(source):
	ret = source.split('/')
	if stringMatch in ret:
		key = ret[-1]
		value = ret[-2]
		if ret[-2] == "property":
			if key not in typeMap.keys():
				typeMap[key] = "dbp"
		elif ret[-2] == "ontology" : 
			if key not in typeMap.keys():
				typeMap[key] = "dbo"

def return_wiki(query):
	query = query + " wikipedia "
	proxies = {}
	proxies['http'] = "http://proxy.iiit.ac.in:8080"
	proxies['https'] = "http://proxy.iiit.ac.in:8080"
	site = urllib.urlopen('http://duckduckgo.com/lite/?q=' + query, proxies = proxies)
	data = site.read()

	bs = BeautifulSoup(data)
	all_links = []
	for link in bs.findAll('a'):
	    all_links.append(link.get('href'))

	return str(all_links[0].split('/')[-1])

def stripURI(uri) :
	if stringMatch in uri.split('/'):
		return uri.split('/')[-1].strip('u')

def isAffix(source, target):
	return source.lower() in target.lower()

def getAffix(source):
	ret = []
	for items in properties:
		if isAffix(source, items):
			ret.append(items)
	return ret

def secondLevelFilter(firstLevelFilter, tokenizedQuestion):
	ret = []
	maxi = 0;
	# for tokens in tokenizedQuestion:
	# 	print tokens

	for items in firstLevelFilter:
		cnt = 0
		for tokens in tokenizedQuestion:
			uniqueSynset = []
			for synset in wn.synsets(tokens):
				for lemma in synset.lemmas():
					uniqueSynset.append(lemma.name())
			uniqueSynset = list(set(uniqueSynset))
			for token in uniqueSynset:
				if isAffix(token, items):
					cnt = cnt + 1 +  3 * (token == tokens)
					break;
		# print items, cnt
		if cnt > maxi:
			maxi = cnt
			ret = []
			ret.append(items)
		elif cnt == maxi:
			ret.append(items)
	return ret

#def 

def modify(source):
	return source.split("/")[-1]


def getScore(answer, question):
	score = 0
	# print answer
	# print "---------------------"
	# print question
	if len(answer) < 5:
		return score
	for words in question:
		for word in answer:
			if len(word) > 3:
				score = score + (isAffix(word, words) + isAffix(words, word))
				score = score + (word == words) * len(words) 
			#else:	
			#	score = score +  * len(words
	return score

def getRelevantSentences(abstractSentences, tokenizedQuestion):
	stemmer = SnowballStemmer("english")
	ret = []
	score = []
	idx = 0
	for items in abstractSentences:
		if idx > 1: 
			score.append([-1 * getScore(items.split(' '), tokenizedQuestion), idx])
		idx = idx + 1
	# print score
	score = sorted(score)
	# print score
	for index in range(0, 3):
		ret.append(abstractSentences[score[index][1]])
	return ret



print "HELLO WORLD! HOW CAN I HELP YOU?"

# print minEditDistR("death", "deathPlace")
sparql = SPARQLWrapper("http://dbpedia.org/sparql")

while True:

	question = raw_input()
	#question = question.lower()
	tokenizedQuestion = nltk.word_tokenize(question)
	taggedQuestion = nltk.pos_tag(tokenizedQuestion)
	print taggedQuestion
	tokenizedQuestion = []
	for items in taggedQuestion:
		items = list(items)
		items[0] = items[0].lower()
		if items[1] == 'NNP' :
			NNP.append(items[0])
		if items[1] == 'NN' or (items[1] == 'NNS') or (items[1] == 'VB'): 
			NN.append(items[0])
		if items[1] == "WRB" :
			items[0] = data["WRB"][items[0]]
		tokenizedQuestion.append(items[0])

	for items in NNP:
		queryString += str(items) + " "
		
	if len(NNP) == 0: 
		for items in NN:
			queryString += str(items) + " "
	dbpediaURI = return_wiki(queryString)
	sparqlQueryProperty = """ PREFIX db: <http://dbpedia.org/resource/>
							  PREFIX prop: <http://dbpedia.org/property/>
							  PREFIX onto: <http://dbpedia.org/ontology/>
							  select ?property ?value 
							  where{ 
								{
								   db:""" + dbpediaURI + """ ?property ?value. 
								}
								union{
								    ?value ?property db:""" + dbpediaURI + """
								}
							}
	
								"""
	print sparqlQueryProperty
	sparql.setQuery(sparqlQueryProperty)
	print '\n\n*** JSON Example'
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	#print results
	for result in results["results"]["bindings"]:

	    getTypeOfProperties(result["property"]["value"])
	    # print stripURI(result["property"]["value"])
	    if stripURI(result["property"]["value"]) is not None:
	    	properties.append(str(stripURI(result["property"]["value"])))
	# print properties
	properties = list(set(properties))
	print properties
	# print len(properties)
	for nn in NN:
		print nn
		for synset in wn.synsets(nn):
			for lemma in synset.lemmas():
				# print lemma.name()					
				possibleProperties.extend(getAffix(lemma.name()))

	possibleProperties = list(set(possibleProperties))
	print possibleProperties
	sparqlQuery = " PREFIX rdfs: <https://www.w3.org/1999/02/22-rdf-syntax-ns#> "
	sparqlQuery = sparqlQuery + " SELECT ?label WHERE { <http://dbpedia.org/resource/"	
	sparqlQuery = sparqlQuery + dbpediaURI + "> "
	gotAnswer = False
	if len(possibleProperties) != 0:
		secondFilterProperties = secondLevelFilter(possibleProperties, tokenizedQuestion)
		print secondFilterProperties
		for items in secondFilterProperties:
			sparqlTempQuery = sparqlQuery + typeMap[items] + ":" + items + " ?label }"
			# print sparqlTempQuery
			sparql.setQuery(sparqlTempQuery)
			print '\n\n*** JSON Example'
			sparql.setReturnFormat(JSON)
			results = sparql.query().convert()
			# print results
			if len(results["results"]["bindings"]) != 0:
				gotAnswer = True
				for result in results["results"]["bindings"]:
					print items + " : " + modify(result["label"]["value"])			
		
	if len(possibleProperties) == 0 or (gotAnswer == False) :
		
		sparqlQuery = sparqlQuery + "dbo:abstract ?label "
		sparqlQuery = sparqlQuery + "FILTER (langMatches(lang(?label),'en')) } "
		# print sparqlQuery
		sparql.setQuery(sparqlQuery)
		print '\n\n*** JSON Example'
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		# print results
		for result in results["results"]["bindings"]:
			# print result["label"]["value"]

			abstractSentences = result["label"]["value"].split('.')
			foo = ""
			for items in abstractSentences[0]:
				try :
					foo = foo + str(items)
				except UnicodeEncodeError:
					foo = foo + ""
			relevantSentences.append(foo)
			foo = " "
			for items in abstractSentences[1]:
				try :
					str(items)
				except UnicodeEncodeError:
					foo = foo + str(items)
			relevantSentences.append(foo)

			for i in range(2, len(abstractSentences)):
				try:
					abstractSentences[i] = str(abstractSentences[i])
				except UnicodeEncodeError:
					abstractSentences[i] = ""

			# print abstractSentences
			relevantSentences.append(getRelevantSentences(abstractSentences, tokenizedQuestion))
			print relevantSentences		
			# for items in relevantSentences:
			# 	for words in items:
			# 		print words + " ",
			# 	print ".\n"

	NN = []
	NNP = []
	properties = []
	possibleProperties = []
	possibleQuery = ""
	typeMap = {}
	abstractSentences = []
	possibleProperties = []
	queryString = ""
	relevantSentences = []
	# sparqlQuery = " PREFIX rdfs: <https://www.w3.org/1999/02/22-rdf-syntax-ns#> "
	# sparqlQuery = sparqlQuery + " SELECT ?label WHERE { <"
	# if wrb == "" :
	# 	parse = data["query"][nn]
	# else :
	# 	ne = data["WRB"][wrb]
	# 	parse = data["query"][nn][ne]
	# sparqlQuery = sparqlQuery + str(data["parser"][parse]["WHERE"]) + nnp + "> " + "dbo:" + str(data["parser"][parse]["dbo"])
	# sparqlQuery = sparqlQuery + " ?label }"
	# print sparqlQuery
	# sparql.setQuery(sparqlQuery)
	
# y = """ PREFIX rdfs: <https://www.w3.org/1999/02/22-rdf-syntax-ns#>SELECT ?label """ + """ WHERE { <http://dbpedia.org/resource/Spain> dbo:populationTotal ?label } """



# JSON example
