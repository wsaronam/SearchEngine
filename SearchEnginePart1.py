import os
import re
import pathlib
import nltk
import pickledb
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
from bs4.element import Comment




root = "C:/Users/Sync/Desktop/project3/WEBPAGES_RAW/35"


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
    TODO: Lemmatization/Stemming and keep hyphens.
    '''
    # Tokenizing by kgraney and malouf (StackOverflow)
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(contentsString.lower()) # end

    for token in tokens:
        if token in stopwords.words('english'):
            tokens.remove(token)

    return tokens


def indexTokens(listOfTokens, docID):
    '''
    Indexes the tokens to prepare for database storage.
    '''
    listOfPairs = []
    for token in listOfTokens:
        listOfPairs.append((token, docID))

    return listOfPairs


def buildInvertedIndexDB(listOfPairs):
    '''
    Iterates over the list of all token and docID pairings in a parsed
    document and creates/adds onto the inverted index database.

    NOTE: As a design choice, we skipped the initial indexing tokens step
    to save writes to memory/RAM and improving indexing speed since it can all
    be done less iterations.
    '''
    db = pickledb.load("database.db", False)
    
    counter = 0
    for tup in listOfPairs:
        token = tup[0]
        path = str(tup[1])
        
        if db.exists(token) == False:
            valueDict = {}
            valueDict[path] = [counter]
            db.set(token, valueDict)
        else:
            currentDict = db.get(token)
            if path not in currentDict:
                currentDict[path] = [counter]
            else:
                currentDict[path].append(counter)
            
            db.set(token, currentDict)

        counter += 1
    
    db.dump()


def createInvertedIndex(root):
    '''
    Runs previously created functions to parse the given files, tokenize
    the texts, and constructs the inverted index database.
    '''
    # File Traversal by Eli Bendersky
    for path, subdirs, files in os.walk(root):
        for name in files:
            filePath = pathlib.PurePath(path, name) # end

            if "bookkeeping" not in str(filePath):
                contents = getContents(filePath)
                tokenizedList = tokenizeContents(contents)
                
                listOfTokenPairs = indexTokens(tokenizedList, filePath)

                buildInvertedIndexDB(listOfTokenPairs)
    

def retrieveQuery():
    query = input("Enter search query: ")




print("Creating Inverted Index...")
createInvertedIndex(root)
print("Inverted Index Creation Completed!")
#retrieveQuery()

