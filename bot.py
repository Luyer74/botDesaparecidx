import tweepy
import time
from bot_wit import BotWit

print('Hola uwu')

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_KEY = ''
ACCESS_SECRET = ''

bot_wit = BotWit("")
idMexico = 110978
botId = '143555567'
file_name = 'last_seen_id.txt'
keywords = ["#desaparecido", "#desaparecida", "#alertaamber", "#teestamosbuscando", "#alertadebusqueda"]
resultTypes = ['recent', 'popular']
searchword = []
date_since = '2019-11-01'


auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

def retrieve_last_seen_id(file_name):
    f_read = open(file_name, 'r')
    last_seen_id = int(f_read.read().strip())
    f_read.close()
    return last_seen_id

def store_last_seen_id(last_seen_id, file_name):
    f_write = open(file_name, 'w')
    f_write.write(str(last_seen_id))
    f_write.close()
    return

#mention function
def mentionfunction():
    last_seen_id = retrieve_last_seen_id(file_name)
    print(last_seen_id)
    mentions = api.mentions_timeline(last_seen_id, tweet_mode = 'extended')
    mentions.reverse()
    #goes through all mentions
    for mention in mentions:
        print(str(mention.id) + ' - ' + mention.full_text)
        #follows user who mentions
        if not mention.user.following:
            if mention.user.id != botId:
                try:
                    mention.user.follow()
                except tweepy.TweepError as e:
                    print(e)
                    print("follow error")
        #retweets
        if not mention.retweeted:
            #if is a reply
            if mention.in_reply_to_status_id is not None:
                try:
                    replyid = mention.in_reply_to_status_id
                    newuser = api.get_status(replyid)
                except tweepy.TweepError as e:
                    print(e)
                    print("Mention error")
                    continue
                #check if it is following itself
                if newuser.user.id != botId:
                    #follows original tweet
                    if not newuser.user.following:
                        try:
                            newuser.user.follow()
                        except tweepy.TweepError as e:
                            print(e)
                            print("follow error")
                    #retweets original retweets
                    if not newuser.retweeted:
                        #check if it is a series of replys, if not rt
                        if newuser.in_reply_to_status_id is None:
                            try:
                                newuser.retweet()
                                print("Found mention!")
                                last_seen_id = mention.id
                                store_last_seen_id(last_seen_id, file_name)
                            except tweepy.TweepError as e:
                                print(e)
                                print("rt error")
            else:
                try:
                    mention.retweet()
                    print("Found mention!")
                    last_seen_id = mention.id
                    store_last_seen_id(last_seen_id, file_name)
                except tweepy.TweepError as e:
                    print(e)
                    print("rt error")

#searching mentionfunction
def mainfunction():
    foundtweets = False
    #words loop
    for i in range(len(keywords)):
        tweetcont = 0
        searchword.append(keywords[i] + " -filter:retweets")
        print("Looking for tweets with " + keywords[i])
        #search for recent and popular
        for j in range(len(resultTypes)):
            tweets = tweepy.Cursor(api.search,q=searchword[i],count=100,geocode='23.634,-102.55,500km',lang='es',result_type=resultTypes[j],since=date_since).items(100)
            #search each tweet
            for tweet in tweets:
                #3 tweets per keyword
                if tweetcont != 3:
                    if not tweet.retweeted:
                        print(tweet.id)
                        try:
                            tweet.retweet()
                            tweetcont = tweetcont + 1
                            print("New tweet found!")
                            #check if valid
                            tweetID = tweet.id
                            tweet = api.get_status(tweetID, tweet_mode = 'extended')
                            tweetmessage = tweet.full_text
                            if bot_wit.get_intent(tweetmessage):
                                print(tweet.full_text)
                                print(tweet.user.location)
                                print(tweet.id)
                                print('Valid tweet! Responding...')
                                api.update_status('@' + tweet.user.screen_name + ' Hola! Soy un bot que te ayudará a difundir tu caso, sígueme!', tweet.id)
                                print("Checking mentions...")
                                mentionfunction()
                                foundtweets = True
                                time.sleep(1800)
                            else:
                                print(tweet.full_text)
                                api.unretweet(tweetID)
                                print('Invalid tweet! Unretweeting...')

                        except tweepy.TweepError as e:
                            print(e)
                            print("Repeats!")
                    else:
                        print("Repeats!")
                else:
                    print("max tweets")
                    break
    #no tweets found, check mentions
    if not foundtweets:
        print("Checking mentions...")
        mentionfunction()
        time.sleep(1800)

#loop
while True:
    print("Checking tweets...")
    mainfunction()
    time.sleep(5)
