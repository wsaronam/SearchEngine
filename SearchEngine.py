import json
import math
import nltk
import operator
import os
import pathlib
import pickledb
import re
import string
from tkinter import *
from tkinter import ttk
from bs4 import BeautifulSoup
from bs4.element import Comment
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer



root = "C:/Users/Sync/Desktop/project3/WEBPAGES_RAW/"

# List of insignificant words (for query priming):
insigWords = stopwords.words('english') + list(string.punctuation)
#print(insigWords)

# tag_visible by jbochi (StackOverflow)
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    else:
        return True # end


def getContents(filePath):
    '''
    Gets and returns files' HTML contents from the file path
    given as input.
    INPUT MUST BE A FILE TYPE FILE
    '''
    openedContents = open(filePath, 'r', encoding="utf-8")
    contents = openedContents.read()
    openedContents.close()

    soup = BeautifulSoup(contents, "html.parser")
    
    # Text grabbing by jbochi (StackOverflow)
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts) # end


def tokenizeContents(contentsString):
    '''
    Tokenizes the contents of a file and puts them into a list.
    '''
    # Tokenizing by kgraney and malouf (StackOverflow)
    tokenizer = RegexpTokenizer(r"([a-zA-Z]*[-]?\w*[-]?\w+)")
    tokens = tokenizer.tokenize(contentsString.lower()) # end
    
    for token in tokens:
        if token in stopwords.words('english'):
            tokens.remove(token)

    return tokens


def indexTokens(listOfTokens, docID):
    '''
    First, lemmatizes each token then indexes the tokens to prepare
    for database storage.
    '''
    lemmatizer = WordNetLemmatizer()
    
    listOfPairs = []
    for token in listOfTokens:
        token = lemmatizer.lemmatize(token)
        listOfPairs.append((token, docID))

    return listOfPairs


def buildInvertedIndexDB(listOfPairs, dbToDump):
    '''
    Iterates over the list of all token and docID pairings in a parsed
    document and creates/adds onto the inverted index database dictionary
    to be added later into the database file.
    NOTE: As a design choice, we skipped the initial indexing tokens step
    to save writes to memory/RAM and improving indexing speed since it can all
    be done less iterations.
    '''
    counter = 0
    for tup in listOfPairs:
        token = tup[0]
        path = str(tup[1])
        
        if token not in dbToDump:
            valueDict = {}
            valueDict[path] = [counter]
            dbToDump[token] = valueDict
        else:
            if path not in dbToDump[token]:
                dbToDump[token][path] = [counter]
            else:
                dbToDump[token][path].append(counter)

        counter += 1


def dumpDictIntoDatabase(dbToDump):
    '''
    Takes the built dictionary of tokens, paths, and occurences and saves it
    into the inverted index database.
    '''
    db = pickledb.load("database.db", False)

    for k,v in dbToDump.items():
        db.set(k, v)
    
    db.dump()


def createInvertedIndex(root):
    '''
    Runs previously created functions to parse the given files, tokenize
    the texts, and constructs the inverted index database.
    '''
    dbToDump = {}
    numOfDocuments = 0
    
    # File Traversal by Eli Bendersky
    for path, subdirs, files in os.walk(root):
        for name in files:
            filePath = pathlib.PurePath(path, name) # end
            
            if "bookkeeping" not in str(filePath):
                contents = getContents(filePath)
                tokenizedList = tokenizeContents(contents)
                
                listOfTokenPairs = indexTokens(tokenizedList, filePath)
                buildInvertedIndexDB(listOfTokenPairs, dbToDump)
                numOfDocuments += 1

    dumpDictIntoDatabase(dbToDump)
    return numOfDocuments


def calculateTFIDF(numOfDocuments):
    '''
    Iterates through the database and calculates the tf-idf scoring/ranking
    number for each token path.
    '''
    db = pickledb.load("database.db", False)
    tokens = db.getall()

    for token in tokens:
        numOfDocsWithToken = len(token)
        for path, listOfIndices in db.get(token).items():
            numOfAppearancesInDoc = len(listOfIndices)
            # tf-idf calculation formula by Prajal Trivedi
            tfidf = math.log10(numOfDocuments/numOfDocsWithToken, 10) * math.log10(numOfAppearancesInDoc, 10)
            db.get(token)[path].append(tfidf)
    db.dump()


def tokenizeQuery(phrase):
    '''
    Function to query with input ranging from 1 word to sentences. 
    '''
    queryList = []
    queryDict = {}
    # Parse query, remove stopwords, tokenize and add to queryList
    for tokens in nltk.word_tokenize(phrase.lower()):
        if tokens not in insigWords:
            queryList.append(tokens)
    for terms in queryList:
        termF = queryList.count(terms)
        tf = (1 + math.log(termF))
        queryDict[terms] = tf
    return queryDict
    
 
def retrieveQuery(query):
    '''
    Prompts the user for a search query and returns top 10 URLs of results of
    the search query.
    '''
    # Create dicts for score, doc vector length, query vector length.
    score = defaultdict(float)
    doc_length = defaultdict(float)
    queryLength = defaultdict(float)

    searchList = []
    queryDict = tokenizeQuery(query)

    db = pickledb.load("database.db", False)

    for queryToken in queryDict:
        for termList in db[queryToken]:
            if len(termList) > 0:
                for docID, docTFIDF in db[queryToken].items():
                    docTFIDF = docTFIDF[-1]
                    score[docID] += (docTFIDF * queryDict[queryToken] * math.log10(37497 / len(termList)))
                    doc_length[docID] += math.pow(1 + docTFIDF, 2)
                    queryLength[docID] += math.pow(queryDict[queryToken] * math.log10(37497 / len(termList)),2)

    for i in score:
        score[i] /= (math.sqrt(queryLength[i]) * math.sqrt(doc_length[i]))

    numK = 1
    sorted_scores = sorted(score.items(), key = operator.itemgetter(1), reverse=True)
    for x in sorted_scores:
        with open('./WEBPAGES_RAW/bookkeeping.json') as f:
            data = json.load(f)
        bookkeepingIndex = x[0].split("\\")[-2:]
        term = str('/'.join(bookkeepingIndex))
        searchList.append(str(numK) + ". " + data[term])
        numK += 1
        if numK == 11:
            break

    return searchList


'''
run_search_engine_parser(): Run the parser and indexer for our search engine

'''

def run_search_engine_parser():
    numOfDocuments = createInvertedIndex(root)
    calculateTFIDF(numOfDocuments)

'''
search(): Retrieves and displays top-10 queries based on used input. 
'''
def search():
    # Source: http://effbot.org/tkinterbook/listbox.htm
    data = retrieveQuery(searchQuery.get())
    frame = Frame(root)
    scrollbar = Scrollbar(frame, orient=VERTICAL)
    searchResults = Listbox(root, yscrollcommand=scrollbar.set)
    scrollbar.config(command=searchResults.yview)
    
    for val in data:
        searchResults.insert(END, val)
    searchResults.pack(side=LEFT, fill=BOTH, expand=1)
    scrollbar.pack(side=RIGHT, fill=Y)
    frame.pack()
root = Tk()
Label(text="Slightly Below-Average Search Query").pack(padx=25)
searchQuery = Entry(root)
searchQuery.pack()
searchButton = Button(root, text="Search",
                          command=search)
searchButton.pack(pady=(5, 5))
Button(root, text="Quit", command=root.destroy).pack()
root.mainloop()
