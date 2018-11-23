import json
import math
import nltk
import os
import pathlib
import pickledb
import re
from bs4 import BeautifulSoup
from bs4.element import Comment
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer




root = "C:/Users/Sync/Desktop/project3/WEBPAGES_RAW/"


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

            tfidf = math.log(numOfDocuments/numOfDocsWithToken, 10) * math.log(numOfAppearancesInDoc, 10)
            db.get(token)[path].append(tfidf)

    db.dump()
    
 
def retrieveQuery():
    '''
    Prompts the user for a search query and returns URLs of results of
    the search query.
    '''
    lemmatizer = WordNetLemmatizer()
    query = input("Enter search query: ").lower()
    query = lemmatizer.lemmatize(query)
    

    db = pickledb.load("database.db", False)
    queryDict = db.get(query)

    with open('./WEBPAGES_RAW/bookkeeping.json') as f:
    	data = json.load(f)

    for k in queryDict:
        bookkeepingIndex = k.split("\\")[-2:]
        term = str('/'.join(bookkeepingIndex))
        print(data[term])




#numOfDocuments = createInvertedIndex(root)
#calculateTFIDF(numOfDocuments)
#print("Number of documents: " + str(numOfDocuments))
retrieveQuery()
