import tweepy
import time

print('Hola uwu')

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_KEY = ''
ACCESS_SECRET = ''

idMexico = 110978
botId = '143555567'
file_name = 'last_seen_id.txt'
keywords = ["#desaparecido", "#desaparecida", "#alertaamber", "#teestamosbuscando"]
searchword = []
date_since = '2019-11-01'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

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
def mainfunction():
    last_seen_id = retrieve_last_seen_id(file_name)
    print(last_seen_id)
    mentions = api.mentions_timeline(last_seen_id, tweet_mode = 'extended')
    #goes through all mentions
    for mention in (mentions):
        print("Found mention!")
        print(str(mention.id) + ' - ' + mention.full_text)
        last_seen_id = mention.id
        store_last_seen_id(last_seen_id, file_name)
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
                replyid = mention.in_reply_to_status_id
                newuser = api.get_status(replyid)
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
                        try:
                            newuser.retweet()
                        except tweepy.TweepError as e:
                            print(e)
                            print("rt error")
            else:
                try:
                    mention.retweet()
                except tweepy.TweepError as e:
                    print(e)
                    print("rt error")

#searching mainfunction
def secondaryfunction():
    for i in range(len(keywords)):
        tweetcont = 0
        searchword.append(keywords[i] + " -filter:retweets")
        print("Looking for tweets with " + keywords[i])
        tweets = tweepy.Cursor(api.search,q=searchword[i],count=100,geocode='23.634,-102.55,500km',lang='es',result_type="recent",since=date_since).items(50)

        for tweet in tweets:
            if tweetcont != 4:
                if not tweet.retweeted:
                    print(tweet.text)
                    print(tweet.user.location)
                    print(tweet.id)
                    try:
                        tweet.retweet()
                        tweetcont = tweetcont + 1
                        api.update_status('@' + tweet.user.screen_name + ' Hola! Soy un bot que te ayudará a difundir tu caso, sígueme!', tweet.id)
                        print("New tweet found!")
                        print("Checking mentions...")
                        mainfunction()
                        time.sleep(1200)

                    except tweepy.TweepError as e:
                        print(e)
                        print("Repeats!")
                else:
                    print("Repeats!")
            else:
                print("max tweets")
                break
#loop
while True:
    print("Checking tweets...")
    secondaryfunction()
    time.sleep(5)
