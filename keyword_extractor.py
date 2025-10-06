import requests
import json
import pandas as pd


keyword=input('Add your keyword: ')


def api_call(keyword):
    
    keywords = [keyword]
     
    url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + keyword
    response = requests.get(url, verify=False)
    suggestions = json.loads(response.text)
    
    
    for word in suggestions[1]:
        keywords.append(word)
        
   
    prefixes(keyword,keywords)
    suffixes(keyword,keywords)
    numbers(keyword,keywords)
    get_more(keyword,keywords)
    clean_df(keywords,keyword)
    
   
        
def prefixes(keyword,keywords):

    prefixes = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','y','x','y','z','how','which','why','where','who','when','are','what']    
    
    for prefix in prefixes:
        print(prefix)
        url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + prefix + " " + keyword 
        response = requests.get(url, verify=False)
        suggestions = json.loads(response.text)
        
        kws = suggestions[1]
        length = len(kws)
        
        for n in range(length):
            print(kws[n])
            keywords.append(kws[n])
            

            
def suffixes(keyword,keywords):
 
    suffixes =['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','y','x','y','z','like','for','without','with','versus','vs','to','near','except','has']
       
    for suffix in suffixes:
        print(suffix)
        url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + keyword + " " + suffix 
        response = requests.get(url, verify=False)
        suggestions = json.loads(response.text)
        
        kws = suggestions[1]
        length = len(kws)
        
        for n in range(length):
            print(kws[n])
            keywords.append(kws[n])  
 
       
def numbers(keyword,keywords):
   
    for num in range(0,10):
        print(num)
        url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + keyword + " " + str(num)
        response = requests.get(url, verify=False)
        suggestions = json.loads(response.text)
        
        kws = suggestions[1]
        length = len(kws)
        
        for n in range(length):
            print(kws[n])
            keywords.append(kws[n]) 
       
def get_more(keyword,keywords):
        for i in keywords:
            print(i)
            url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + i
            response = requests.get(url, verify=False)
            suggestions = json.loads(response.text)
            
            keywords2 =  suggestions[1]
            length = len(keywords2)
                       
            
            for n in range(length):
                print(keywords2[n])
                keywords.append(keywords2[n])
                print(len(keywords))
            
                   
            if len(keywords) >= 1000: 
                print('###Finish here####')
                break
         
            
def clean_df(keywords,keyword):
    
    keywords = list(dict.fromkeys(keywords)) 
    new_list = [word for word in keywords if all(val in word for val in keyword.split(' '))]
    df = pd.DataFrame (new_list, columns = ['Keywords'])
    print(df)
    df.to_csv(keyword+'-keywords.csv')


api_call(keyword)