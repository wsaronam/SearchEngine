import os
import re
import pathlib
import nltk
import json
import pickledb
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
from bs4.element import Comment


root = "./WEBPAGES_RAW"

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
    openedContents = open(filePath, 'r', encoding="utf-8", errors='ignore')
    contents = openedContents.read()
    openedContents.close()

    soup = BeautifulSoup(contents, "html.parser")
    
    # Text grabbing by jbochi (StackOverFlow)
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts) # end


def tokenizeContents(contentsString):
    '''
    Tokenizes the contents of a file and puts them into an array.
    TODO: Lemmatization/Stemming and keep hyphens.  lowercase everything
    '''
    # Tokenizing by kgraney and malouf (StackOverflow)
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(contentsString) # end

    for token in tokens:
        if token in stopwords.words('english'):
            tokens.remove(token)

    return tokens

def indexTokens(listOfTokens, listOfPairs, docID):
    '''
    Indexes the tokens into a database.
    '''
    for token in listOfTokens:
        listOfPairs.append((token, docID))


def constructInvertedIndex(listOfPairs):
    '''
    '''
    invertedIndex = {}
    
    for tup in listOfPairs:
        if tup[0] not in invertedIndex:
            # add to dict
            newToken = {}
            newToken[str(tup[1])] = 1
            invertedIndex[tup[0]] = newToken
        else:
            # add to dict of existing token
            if str(tup[1]) in invertedIndex[tup[0]]:
                # incrememnt value
                invertedIndex[tup[0]][str(tup[1])] += 1
            else:
                # add new path and frequency to the invertedindex dict
                invertedIndex[tup[0]][str(tup[1])] = 1

    return invertedIndex
                

def createInvertedIndex(root):
    '''
    '''
    counter = 0
    listOfTokenPairs = []
    
    # File Traversal by Eli Bendersky
    for path, subdirs, files in os.walk(root):
        for name in files:
            filePath = pathlib.PurePath(path, name) # end

            if "bookkeeping" not in str(filePath):
                contents = getContents(filePath)
                tokenizedList = tokenizeContents(contents)
                
                indexTokens(tokenizedList, listOfTokenPairs, filePath)
                counter += 1
                print(counter)

    invertedIndex = constructInvertedIndex(listOfTokenPairs)
    print(invertedIndex)
    
    with open("data.json", "w") as outfile:
        json.dump(invertedIndex, outfile)


def retrieveQuery():
    query = input()
    jdata = json.load



    
print("Creating Inverted Index...")    
createInvertedIndex(root)
print("Completed!")

