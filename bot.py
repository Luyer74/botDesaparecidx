import tweepy  # https://github.com/tweepy/tweepy
import credentials

from bot_wit import BotWit
from time import sleep


ID_MEXICO = credentials.ID_MEXICO
BOT_ID = credentials.BOT_ID
KEYWORDS = [
    "#desaparecido",
    "#desaparecida",
    "#alertaamber",
    "#teestamosbuscando",
    "#alertadebusqueda",
    "#alertaplateada"
]
RESULT_TYPES = [
    "recent",
    "popular"
]
REPLY_STRING = (
    "@{0} Hola! Soy un bot que te ayudará a difundir tu caso, sígueme!"
)
DATE_SINCE = "2020-04-01"
LAST_SEEN_FILE = "last_seen_id.txt"



class Bot():

    def __init__(self):
        self.bot_wit = BotWit(credentials.BOT_WIT_KEY)
        auth = tweepy.OAuthHandler(
            credentials.CONSUMER_KEY,
            credentials.CONSUMER_SECRET
        )

        auth.set_access_token(
            credentials.ACCESS_KEY,
            credentials.ACCESS_SECRET
        )

        self.api = tweepy.API(
            auth,
            wait_on_rate_limit=True
        )


    def get_last_seen_id(self):
        with open(LAST_SEEN_FILE, "r") as file:
            return int(file.read().strip())


    def store_last_seen_id(self, last_seen_id):
        with open(LAST_SEEN_FILE, "w") as file:
            file.write(str(last_seen_id))


    # mention function
    def mention_function(self):
        last_seen_id = self.get_last_seen_id()
        print("Last seen id = {0}".format(last_seen_id))
        mentions = self.api.mentions_timeline(
            last_seen_id,
            tweet_mode='extended'
        )

        mentions.reverse()
        # goes through all mentions
        for mention in mentions:
            print(str(mention.id) + ' - ' + mention.full_text)
            # follows user who mentions
            if not mention.user.following:
                if mention.user.id != BOT_ID:
                    try:
                        mention.user.follow()
                    except tweepy.TweepError as e:
                        print(e)
                        print("follow error")
            # retweets
            if not mention.retweeted:
                # if is a reply
                if mention.in_reply_to_status_id is not None:
                    try:
                        replyid = mention.in_reply_to_status_id
                        newuser = self.api.get_status(replyid)
                    except tweepy.TweepError as e:
                        print(e)
                        print("Mention error")
                        continue
                    # check if it is following itself
                    if newuser.user.id != BOT_ID:
                        # follows original tweet
                        if not newuser.user.following:
                            try:
                                newuser.user.follow()
                            except tweepy.TweepError as e:
                                print(e)
                                print("follow error")
                        # retweets original retweets
                        if not newuser.retweeted:
                            # check if it is a series of replys, if not rt
                            if newuser.in_reply_to_status_id is None:
                                try:
                                    newuser.retweet()
                                    print("Found mention!")
                                    last_seen_id = mention.id
                                    self.store_last_seen_id(
                                        last_seen_id,
                                    )
                                except tweepy.TweepError as e:
                                    print(e)
                                    print("rt error")
                else:
                    #check if mention is quote of another tweet
                    if mention.is_quote_status:
                        #get quote status
                        quotedTweet = self.api.get_status(mention.quoted_status_id)
                        #fav mention
                        try:
                            mention.favorite()
                        except tweepy.TweepError as e:
                            print(e)
                            print("fav error")
                        #retweet quoted
                        try:
                            quotedTweet.retweet()
                            print("Found mention!")
                        except tweepy.TweepError as e:
                                print(e)
                                print("rt error")
                    else:
                        try:
                            mention.retweet()
                            print("Found mention!")
                        except tweepy.TweepError as e:
                            print(e)
                            print("rt error")
                    #store mention id
                    last_seen_id = mention.id
                    self.store_last_seen_id(
                        last_seen_id
                    )


    # searching mentionfunction
    def worker(self):
        foundtweets = False
        # words loop
        for keyword in KEYWORDS:
            tweetcont = 0
            print("Looking for tweets with " + keyword)
            # search for recent and popular
            for result_type in RESULT_TYPES:
                tweets = tweepy.Cursor(
                    self.api.search,
                    q=keyword + " -filter:retweets",
                    count=100,
                    geocode='23.634,-102.55,500km',
                    lang='es',
                    result_type=result_type,
                    since=DATE_SINCE
                ).items(100)

                # search each tweet
                for tweet in tweets:
                    # 3 tweets per keyword
                    if tweetcont != 3:
                        if not tweet.retweeted:
                            print(tweet.id)
                            try:
                                tweet.retweet()
                                tweetcont = tweetcont + 1
                                print("New tweet found!")
                                # check if valid
                                tweetID = tweet.id
                                tweet = self.api.get_status(
                                    tweetID,
                                    tweet_mode='extended'
                                )

                                tweetmessage = tweet.full_text
                                if self.bot_wit.get_intent(tweetmessage):
                                    print(tweet.full_text)
                                    print(tweet.user.location)
                                    print(tweet.id)
                                    print('Valid tweet! Responding...')
                                    self.api.update_status(
                                        REPLY_STRING.format(
                                            tweet.user.screen_name),
                                        tweet.id
                                    )

                                    print("Checking mentions...")
                                    self.mention_function()
                                    foundtweets = True
                                    sleep(1800)
                                else:
                                    print(tweet.full_text)
                                    self.api.unretweet(tweetID)
                                    print('Invalid tweet! Unretweeting...')

                            except tweepy.TweepError as e:
                                print(e)
                                print("Repeats!")
                        else:
                            print("Repeats!")
                    else:
                        print("max tweets")
                        break
        # no tweets found, check mentions
        if not foundtweets:
            print("Checking mentions...")
            self.mention_function()
            sleep(1800)


    def main(self):
        while True:
            print("Checking tweets...")
            self.worker()
            sleep(5)

if __name__ == '__main__':
    Bot().main()
