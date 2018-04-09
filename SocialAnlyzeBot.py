
# coding: utf-8

# In[ ]:


import tweepy
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
from datetime import datetime, timezone

from matplotlib.legend_handler import HandlerLine2D

from config import (consumer_key,
                    consumer_secret,
                    access_token,
                    access_token_secret)

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# In[ ]:


analyzer = SentimentIntensityAnalyzer()
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())


# In[ ]:


def perform_analysis(target_user):
    compound_list = []
    positive_list = []
    negative_list = []
    neutral_list = []
    tweet_list=[]
    account_list=[]
 
    for x in range(0, 25):
        public_tweets=api.user_timeline(target_user, page=x)
        for tweet in public_tweets:
            result=analyzer.polarity_scores(tweet["text"])
            compound_list.append(result["compound"])
            positive_list.append(result["pos"])
            negative_list.append(result["neg"])
            neutral_list.append(result["neu"])
            tweet_list.append(tweet["text"])
            account_list.append(target_user)
           
    analyze_tweet_df=pd.DataFrame({"User":account_list,
                                   "Compound":compound_list,
                                   "Positive":positive_list,
                                   "Negative":negative_list,
                                   "Neutral":neutral_list,
                                    "Tweet":tweet_list
                                 })
   ####Plotting. Do not want to send DataFrame as an arughment so plotting it same function 
    try:
        with plt.style.context('seaborn-dark'):
            plt.figure(figsize=(12,9))
            plt.xlim([len(analyze_tweet_df)*-1,0])
            plt.ylim(-1,1)
            plt.ylabel("Tweet Polarity")
            plt.xlabel("Tweets Ago")
            plt.grid(color='white', linestyle='-', linewidth=1.25)
            plt.title(f"Sentiment Analysis {datetime.now().strftime('%m/%d/%Y')}")
            g,=plt.plot(range(len(analyze_tweet_df)*-1,0), compound_list, marker="o", linewidth=0.75, alpha=0.8, color="steelblue",label=f"Tweets\n{target_user}")
            #plt.legend([g],[f"Tweet {target_user}"])
            #plt.legend([g],loc='upper right',bbox_to_anchor=(1.20, 1))
            plt.legend( handler_map={g: HandlerLine2D(numpoints=1)},loc='upper right',bbox_to_anchor=(1.12, 1))
            plt.savefig(f"{target_user}{datetime.now().strftime('%m-%d-%Y')}.png")
    except:
        print("There is an issue creating plot")
        return "ERROR_IN_CREATING_IMAGE"
    return f"{target_user}{datetime.now().strftime('%m-%d-%Y')}.png"


# In[ ]:


def AnalyazeString(tweet_text):
    #If analyze word missing then no need to analyze
    #print(tweet_text)
    if("analyze" in tweet_text.replace(':','').lower()):
        split_text=tweet_text.split(" ")
    else:
        return {"exist":False}

    # If users don't exist then No need to analyze
    try:
        my_user=api.me()["screen_name"]
        mention_user=api.get_user(split_text[2])["screen_name"]
    except:
        return {"exist":False}
    
    if(split_text[0].replace('@','').lower()!=my_user.lower()):
        return {"exist":False}

    #Second argument
    if(split_text[1].replace(':','').lower()!="analyze"):
        return {"exist":False}

    if not mention_user:
        return {"exist":False}
    #If everything looks good then send true
    return {"exist":True,"mention_user":split_text[2]}


# In[ ]:


##starting main program
## Search analysis tweet. 
mybotname="@redhotmarket"

### This variable will be used for search tweet id greater than last one.
search_tweetid=0

while(True):
    #Keeping aside first find for analyze
    first_found=True
    
    #This will check if it's been published already within a day
    Already_published=False
   
    tweets=api.search(mybotname,rpp=100,since_id=search_tweetid)
    
    for tweet in tweets["statuses"]:
        ### Filtering tweets. It will parse tweet to check if it's called for analyze
        analyzeString_result=AnalyazeString(tweet["text"])
        
        if(analyzeString_result["exist"]):
            print(analyzeString_result)
            if(first_found):
                first_found=False
                #print(analyzeString_result["mention_user"])
                first_analyze=analyzeString_result["mention_user"]
                first_create=tweet["created_at"]
                first_tweetid=tweet["id"]
                first_tweetedby=tweet["user"]["screen_name"]
            else:
                if((first_analyze==analyzeString_result["mention_user"]) and ((datetime.strptime(first_create, "%a %b %d %H:%M:%S %z %Y")-datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S %z %Y")).seconds <=86400)):
                    print(datetime.strptime(first_create, "%a %b %d %H:%M:%S %z %Y"))
                    print(datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S %z %Y"))
                    Already_published=True
                    break

    ##If Analaysis is completed for same user then reply to user.Else publish the result
    if(Already_published):
        print(f"{first_analyze} is already published")
        api.update_status(f"Hi @{first_tweetedby}, analysis for @{first_analyze} completed within 24hrs. Try later",first_tweetid)
    elif((datetime.strptime(str(datetime.now(timezone.utc).strftime("%a %b %d %H:%M:%S %z %Y")),"%a %b %d %H:%M:%S %z %Y")-datetime.strptime(first_create, "%a %b %d %H:%M:%S %z %Y")).seconds <=120):
        #print(first_analyze)
        imgname=perform_analysis(first_analyze)
        #print(imgname)
        if(imgname !="ERROR_IN_CREATING_IMAGE"):
            api.update_with_media(imgname,f"Thank you @{first_tweetedby} for using my plot !!")
            print(f"Thank you @{first_tweetedby} for using my plot !!")
    else:
        print("Nothing to print")
   #perform_analysis(first_analyze)
    #Initializing variables. THis will ensure on second run variables don't have old values
    first_analyze=''
    first_create=''
    first_tweetid=''
    first_tweetedby=''
    analyzeString_result={}

    search_tweetid=first_tweetid
    time.sleep(120)

