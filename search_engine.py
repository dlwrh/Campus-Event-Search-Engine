import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import linear_kernel
from nltk.stem.lancaster import LancasterStemmer
from textblob import Word
from autocorrect import spell
import sys
import datetime
import time
from nltk.corpus import wordnet
from itertools import chain
import nltk
import webbrowser
from textblob import TextBlob

reload(sys)
sys.setdefaultencoding('utf-8')

def split_into_lemmas(message):
    message = message.decode('ascii', 'ignore').lower()
    stemmer = LancasterStemmer()
    words = TextBlob(message).words
    words_lemma = [Word(word).lemmatize("v") for word in words]
    stem_words = [stemmer.stem(word) for word in words_lemma]
    outstring = " ".join(stem_words)
    return outstring

def autocorrect(s):
    s = s.lower()
    l = s.split()
    l = [spell(i) for i in l]
    outs = " ".join(l)
    return outs

def syn_expand(query):
	result = ""
	for word in query.split():
		synonyms = wordnet.synsets(word)
		synonyms_set =  set(chain.from_iterable([word.lemma_names() for word in synonyms]))
		for w in synonyms_set:
			result += w + " "
	weight = len(result.split())/2
	final_result = (query + " ")* weight + result
	return final_result

## time
now = str(datetime.date.today())
today = time.strptime(now,"%Y-%m-%d")

# load data
with open("eventnew.txt","r") as datafile:
    event_json = datafile.read()
    events_dic = json.loads(event_json)

print len(events_dic)

## future event
future_events_list = []
future_events_tb_list = []
for i in events_dic:
    try:
        if time.strptime(events_dic[i]["date_end"],"%Y-%m-%d") > today:
            future_events_tb_list.append(split_into_lemmas((events_dic[i]["event_title"]+" ")*3+ events_dic[i]["description"].decode('ascii', 'ignore')))
            future_events_list.append(events_dic[i]["description"].decode('ascii', 'ignore'))
    except:
        pass
print len(future_events_list)

# past event
past_events_list = []
past_events_tb_list = []
for i in events_dic:
    try:
        if time.strptime(events_dic[i]["date_end"],"%Y-%m-%d") < today:
            past_events_tb_list.append(split_into_lemmas((events_dic[i]["event_title"]+" ")*3+ events_dic[i]["description"].decode('ascii', 'ignore')))
            past_events_list.append(events_dic[i]["description"].decode('ascii', 'ignore'))
    except:
        pass
print len(past_events_list)

## all event
events_list = []
events_tb_list = []

for i in events_dic:
    try:
        events_tb_list.append(split_into_lemmas((events_dic[i]["event_title"]+" ")*3+ events_dic[i]["description"].decode('ascii', 'ignore')))
        events_list.append(events_dic[i]["description"].decode('ascii', 'ignore'))
    except:
        pass

time_selection = raw_input("You are searching for future(f)/past(p)/all(a) event?\t")

## TfidfTransformer
if time_selection == "a":
    vectorizer = TfidfVectorizer(min_df=1,ngram_range=(1,2))
    tfidf = vectorizer.fit_transform(events_tb_list)
elif time_selection == "f":
    vectorizer = TfidfVectorizer(min_df=1,ngram_range=(1,2))
    tfidf = vectorizer.fit_transform(future_events_tb_list)
elif time_selection == "p":
    vectorizer = TfidfVectorizer(min_df=1,ngram_range=(1,2))
    tfidf = vectorizer.fit_transform(past_events_tb_list)
else:
    exit()

while True:
# query input
    q = raw_input("Search: ")
    r = raw_input("Are you searching for "+autocorrect(q) +"? Y/N\t")
    if r == "Y":
        q = autocorrect(q)
    elif r == "N":
        pass
    else:
        "Wrong input!"

    query = [split_into_lemmas(syn_expand(q))]
    querytfidf = vectorizer.transform(query)
    cosine_similarities = linear_kernel(querytfidf, tfidf).flatten()
    related_docs_indices = cosine_similarities.argsort()[:-100:-1]
    related_docs_indices = list(related_docs_indices)[::-1]
    print query

    with open("tags.txt","r") as tagfile:
        tag_json = tagfile.read()
        tag_dic = json.loads(tag_json)
        tag_list = sorted(tag_dic.keys(), key = lambda x:tag_dic[x])
        #tag_list = [i.lower() for i in tag_list]


    ## output
    has_search_tag = False
    search_tag_list = []
    for tag in tag_list:
        if tag.lower() in autocorrect(q):
            has_search_tag = True
            search_tag_list.append(tag)


    out_dic = {}
    out_count = 1
    out_list = []
    if has_search_tag:
        for tag in search_tag_list:
            if time_selection == "a":
                for j in events_dic:
                    try:
                        if tag in events_dic[j]["tags"]:
                            if events_dic[j]["description"].decode('ascii', 'ignore') not in out_list:
                                out_list.append(events_dic[j]["description"].decode('ascii', 'ignore'))
                                out_dic[out_count] = j
                                out_count += 1
                    except:
                        pass

            elif time_selection == "f":
                for j in events_dic:
                    try:
                        if time.strptime(events_dic[j]["date_end"],"%Y-%m-%d") > today:
                            if tag in events_dic[j]["tags"]:
                                if events_dic[j]["description"].decode('ascii', 'ignore') not in out_list:
                                    out_list.append(events_dic[j]["description"].decode('ascii', 'ignore'))
                                    out_dic[out_count] = j
                                    out_count += 1
                    except:
                        pass
            else:
                for j in events_dic:
                    try:
                        if time.strptime(events_dic[j]["date_end"],"%Y-%m-%d") < today:
                            if tag in events_dic[j]["tags"]:
                                if events_dic[j]["description"].decode('ascii', 'ignore') not in out_list:
                                    out_list.append(events_dic[j]["description"].decode('ascii', 'ignore'))
                                    out_dic[out_count] = j
                                    out_count += 1
                    except:
                        pass



    if time_selection == "a":
        out_event_list = list(set([events_list[i] for i in related_docs_indices]))

        for i in out_event_list:
            if i in out_list:
                continue
            else:
                for j in events_dic:
                    try:
                        if events_dic[j]["description"].decode('ascii', 'ignore') == i:
                            # print str(out_count), events_dic[j]["event_title"]
                            out_dic[out_count] = j
                            out_list.append(i)
                            out_count += 1
                            break
                    except:
                        pass

    elif time_selection == "f":
        out_event_list = list(set([future_events_list[i] for i in related_docs_indices]))
        for i in out_event_list:
            if i in out_list:
                continue
            else:
                for j in events_dic:
                    try:
                        if time.strptime(events_dic[j]["date_end"],"%Y-%m-%d") > today:
                            if events_dic[j]["description"].decode('ascii', 'ignore') == i:
                                out_dic[out_count] = j
                                out_list.append(i)
                                out_count += 1
                                break
                    except:
                        pass
    else:
        out_event_list = list(set([past_events_list[i] for i in related_docs_indices]))
        for i in out_event_list:
            if i in out_list:
                continue
            else:
                for j in events_dic:
                    try:
                        if time.strptime(events_dic[j]["date_end"],"%Y-%m-%d") < today:
                            if events_dic[j]["description"].decode('ascii', 'ignore') == i:
                                out_dic[out_count] = j
                                out_list.append(i)
                                out_count += 1
                                break
                    except:
                        pass

    temp_count = 1
    for c in range(1,out_count):
        temp = events_dic[out_dic[c]]
        print c,temp["event_title"],temp["date_end"]
        temp_count += 1
        if temp_count> 20:
            break

    while True:
        detailId = raw_input("Please Select One Event: (Enter 'back' to search another term)")
        if detailId == "back":
            break
        try:
            webbrowser.open("https://events.umich.edu/event/"+out_dic[int(detailId)][:5])
        except:
            print "Wrong input"


    
