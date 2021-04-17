import tweepy  # https://github.com/tweepy/tweepy
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import ucredentials
import requests
from bot_wit import BotWit
from time import sleep


ID_MEXICO = ucredentials.ID_MEXICO
BOT_ID = ucredentials.BOT_ID
BANNEDID = [1231085650415366145, 156679524, 109105795, 510622252, 140630292, 1233249435326599168, 2440710531, 1229080680, 1303547842741534723, 1223799471961706496, 1232732937495310337, 2451775405, 1285701537088409600, 1273177907561627651, 2868288303, 3254924130]
KEYWORDS = [
    "#desaparecido",
    "#desaparecida",
    "#alertaamber",
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
LAST_SEEN_MESSAGE = "last_seen_message.txt"


class Bot():


    def __init__(self):
        self.counter = 0
        #wit
        self.bot_wit = BotWit(ucredentials.BOT_WIT_KEY)
        #fb
        self.page_token = ucredentials.FACEBOOK_KEY
        self.page_id = "101518154964830"
        #firebase
        # Fetch the service account key JSON file contents
        self.cred = credentials.Certificate('keys.json')

        #twitter credentials
        auth = tweepy.OAuthHandler(
            ucredentials.CONSUMER_KEY,
            ucredentials.CONSUMER_SECRET
        )

        auth.set_access_token(
            ucredentials.ACCESS_KEY,
            ucredentials.ACCESS_SECRET
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


    def get_last_seen_message(self):
        with open(LAST_SEEN_MESSAGE, "r") as file:
            return int(file.read().strip())


    def store_last_seen_message(self, last_seen_message):
        with open(LAST_SEEN_MESSAGE, "w") as file:
            file.write(str(last_seen_message))


    def postFacebook(self, tweet):
        tweet_text = tweet.full_text
        tweet_user = tweet.user.screen_name
        ent = tweet.entities
        urls = tweet.entities['urls']
        if 'media' in ent:
            #get image url
            images = tweet.entities['media']
            img_url = images[0]['media_url']
            print("\nPosting to facebook...")
            #post
            post_message = tweet_user + " pide tu ayuda para difundir lo siguiente:\n \"" + tweet_text + "\""
            post_message = post_message.replace('#', '/')
            post_message = post_message.replace('@', '/')
            fb_url = f"https://graph.facebook.com/{self.page_id}/photos?url={img_url}&access_token={self.page_token}"
            fb_post = requests.post(fb_url).json()
            print(fb_post)
            #update post with message
            post_id = fb_post['post_id']
            fb_url_update = f"https://graph.facebook.com/{post_id}?message={post_message}&access_token={self.page_token}"
            updated_post = requests.post(fb_url_update).json()
            print(updated_post)
            return
        elif urls:
            print("\nPosting to facebook...")
            link_tweet = urls[0]['expanded_url']
            post_message = tweet_user + " pide tu ayuda para difundir lo siguiente:\n \"" + tweet_text + "\""
            post_message = post_message.replace('#', '/')
            post_message = post_message.replace('@', '/')
            fb_url = f"https://graph.facebook.com/{self.page_id}/feed?message={post_message}&link={link_tweet}&access_token={self.page_token}"
            fb_post = requests.post(fb_url).json()
            print(fb_post)
            return

    def insertData(self, tweet, search_id):
        # Initialize the app with a service account, granting admin privileges
        ref = db.reference('/')
        #get data
        tweet_dateF = tweet.created_at
        tweet_date = tweet_dateF.strftime("%Y-%m-%d, %H%M%S")
        tweet_date = tweet_date[:10]
        user_verified = tweet.user.verified
        if user_verified:
            verified = 1
        else:
            verified = 0

        #hashtags
        try:
            hashtag_objects = tweet.entities['hashtags']
        except (AttributeError, KeyError):
            hashtag_objects = []
            print("No hashtags found")
        #check media if it exists
        try:
            media_urls = tweet.entities['media']
        except (AttributeError, KeyError):
            media_urls = []
            print("No media found")

        #check if user is following
        try:
            friendship = self.api.show_friendship(source_id=BOT_ID, target_id=tweet.user.id)
            if friendship[1].following:
                isFollowing = 1
            else:
                isFollowing = 0
        except:
            isFollowing = 0

        #INSERT INTO TWEETS
        tweet_ref = ref.child("TWEETS")
        TWEET_dict = {str(tweet.id) : {
            "user" : tweet.user.id_str,
            "tweet_text" : tweet.full_text,
            "favorite_count" : tweet.favorite_count,
            "retweet_count" : tweet.retweet_count,
            "search_id" : 1,
            "date_created" : tweet_date
        }}
        print("Inserting tweet into Firebase...")
        tweet_ref.update(TWEET_dict)

        #INSERT INTO USERS
        user_ref = ref.child("USERS")
        USER_dict = {str(tweet.user.id) : {
            "isFollowing" : isFollowing,
            "name" : tweet.user.screen_name,
            "location" : tweet.user.location,
            "verified" : verified,
            "followers_count" : tweet.user.followers_count
        }}
        print("Inserting user into Firebase...")
        user_ref.update(USER_dict)

        #INSERT INTO HASHTAGS
        href = ref.child("HASHTAGS/" + str(tweet.id))
        for hashtag in hashtag_objects:
            HTindex = len(href.get()) if href.get() else 0
            HASHTAG_dict = {str(HTindex) : {
                "hashtag" : hashtag['text']
            }}
            print("Inserting hashtag into Firebase...")
            href.update(HASHTAG_dict)


        #INSERT INTO IMAGES
        img_ref = ref.child("IMAGES/" + str(tweet.id))
        for url in media_urls:
            IMGindex = len(img_ref.get()) if img_ref.get() else 0
            IMAGES_dict = {str(IMGindex) : {
                "image_link" : url['media_url']
            }}
            print("Inserting image into Firebase...")
            img_ref.update(IMAGES_dict)





    #message function
    def message_function(self):
        last_seen_message = self.get_last_seen_message()
        messages = self.api.list_direct_messages(10)
        first = True
        for message in messages:
            message_timestamp = int(message.created_timestamp)
            if message_timestamp <= last_seen_message:
                break
            else:
                if first:
                    self.store_last_seen_message(message_timestamp)
                    first = False
                reply_id = message.message_create['sender_id']
                if reply_id == BOT_ID:
                    continue
                bot_message = """Hola! Si necesitas que difunda un caso de desaparición puedes responder o etiquetarme con mi @ en el tweet que contenga la información o también puedes ingresar a www.botdesparecidx.com y en la sección de reportar puedes llenar un formulario para que difunda tu caso en mis redes! Si tienes otra duda puedes contactar a mi desarrollador."""
                self.api.send_direct_message(reply_id, bot_message)


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
            if mention.user.id in BANNEDID:
                print("BANNED")
                continue
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
                        newuser = self.api.get_status(replyid,              tweet_mode='extended')
                    except tweepy.TweepError as e:
                        print(e)
                        print("Mention error")
                        continue
                    # check if it is following itself
                    if newuser.user.id != BOT_ID:
                        #check if banned
                        if newuser.user.id in BANNEDID:
                            print("BANNED")
                            continue
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
                                    self.postFacebook(newuser)
                                    self.insertData(newuser, 1)
                                    print("Found mention!")
                                    last_seen_id = mention.id
                                    self.store_last_seen_id(
                                        last_seen_id,
                                    )
                                except tweepy.TweepError as e:
                                    print(e)
                                    print("rt error")
                else:
                    #store mention id
                    last_seen_id = mention.id
                    self.store_last_seen_id(
                        last_seen_id
                    )
                    #check if mention is quote of another tweet
                    if mention.is_quote_status:
                        #get quote status
                        try:
                            quotedTweet = self.api.get_status(mention.quoted_status_id, tweet_mode='extended')
                        except:
                            print("quote error")
                            continue
                        #fav mention
                        try:
                            mention.favorite()
                        except tweepy.TweepError as e:
                            print(e)
                            print("fav error")
                        #retweet quoted
                        try:
                            if quotedTweet.user.id in BANNEDID:
                                print("BANNED")
                                continue
                            quotedTweet.retweet()
                            print("Found mention!")
                            self.postFacebook(quotedTweet)
                            self.insertData(quotedTweet, 2)
                        except tweepy.TweepError as e:
                                print(e)
                                print("rt error")

                    else:
                        try:
                            mention.retweet()
                            print("Found mention!")
                            self.postFacebook(mention)
                            self.insertData(mention, 3)

                        except tweepy.TweepError as e:
                            print(e)
                            print("rt error")



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
                    geocode='21.38,-101.33,1200km',
                    lang='es',
                    result_type=result_type,
                    since=DATE_SINCE
                ).items(100)

                # search each tweet
                for tweet in tweets:
                    # 3 tweets per keyword
                    if tweet.user.id in BANNEDID:
                        print("BANNED!")
                        continue
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
                                try:
                                    if self.bot_wit.get_intent(tweetmessage):
                                        print(tweet.full_text)
                                        print(tweet.user.location)
                                        print(tweet.id)
                                        print('Valid tweet! Responding...')
                                        #dump tweet to json and post to fb
                                        self.postFacebook(tweet)
                                        self.insertData(tweet, 4)
                                        #respond
                                        self.api.update_status(
                                            REPLY_STRING.format(
                                                tweet.user.screen_name),
                                            tweet.id
                                        )

                                        print("Checking mentions...")
                                        self.mention_function()
                                        print("Checking messages...")
                                        self.message_function()
                                        foundtweets = True
                                        sleep(1800)
                                    else:
                                        print(tweet.full_text)
                                        self.api.unretweet(tweetID)
                                        print('Invalid tweet! Unretweeting...')
                                except:
                                    print("wit error")

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
        firebase_admin.initialize_app(self.cred, {
            'databaseURL': 'https://pythondbtest-2fbd1-default-rtdb.firebaseio.com/'
        })
        while True:
            print("Checking tweets...")
            self.worker()
            sleep(5)

if __name__ == '__main__':
    Bot().main()
