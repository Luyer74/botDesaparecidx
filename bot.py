import os
import time
import json
import wget
import shutil
import tweepy  # https://github.com/tweepy/tweepy
import facebook
import credentials

from time import sleep
from bot_wit import BotWit
from MySQLdb import _mysql
from datetime import datetime



ID_MEXICO = credentials.ID_MEXICO
BOT_ID = credentials.BOT_ID
BANNEDID = []
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

        # TODO What is it for ?
        # Maybe change the file created to a method, the same procedure is been repeated
        # define the filename with utc timestamp as prefix
        self.dateString = datetime.utcnow().strftime('%Y-%m-%d - %H-%M-%S')
        self.output = open(
            'bdatweets_%s.json' % self.dateString,
            'a'
        )

        #wit
        self.bot_wit = BotWit(credentials.BOT_WIT_KEY)
        #fb
        self.graph = facebook.GraphAPI(credentials.FACEBOOK_KEY)
        #database
        self.connectToDB()
        #twitter credentials
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


    def get_last_seen_message(self):
        with open(LAST_SEEN_MESSAGE, "r") as file:
            return int(file.read().strip())


    def store_last_seen_message(self, last_seen_message):
        with open(LAST_SEEN_MESSAGE, "w") as file:
            file.write(str(last_seen_message))


    # TODO automize process
    def dumpTweet(self, tweet):
        self.counter += 1
        json.dump(tweet._json, self.output)
        self.output.write('\n')
        if self.counter >= 50:
            self.output.close()
            fileString = 'bdatweets_%s.json' % self.dateString
            print("Dumping tweet into " + fileString)
            shutil.move(fileString, 'tweetJSONS')
            # This process can be moved to a method
            self.dateString = datetime.utcnow().strftime('%Y-%m-%d - %H-%M-%S')
            self.output = open(
                'bdatweets_%s.json' % self.dateString,
                'a'
            )
            self.counter = 0


    def postFacebook(self, tweet):
        tweet_text = tweet.full_text
        tweet_user = tweet.user.screen_name
        ent = tweet.entities
        urls = tweet.entities['urls']
        if 'media' in ent:
            #get image url
            images = tweet.entities['media']
            img_url = images[0]['media_url']
            path = 'img.jpg'
            #remove previous image
            if os.path.isfile(path):
                os.remove(path)
            #post
            post_message = tweet_user + " pide tu ayuda para difundir lo siguiente:\n \"" + tweet_text + "\""
            gotImage = False
            while not gotImage:
                try:
                    wget.download(img_url, path)
                    gotImage = True
                except:
                    print("Error downloading image! Trying again...")
                    # TODO is it neccesary this long ?
                    sleep(60)
            print("\nPosting to facebook...")
            # TODO better send the path to the method
            # and let the method to open and close
            # the image with a 'with' statement
            self.graph.put_photo(
                image=open(path, 'rb'),
                message=post_message
            )
        elif urls:
            link_tweet = urls[0]['expanded_url']
            post_message = tweet_user + " pide tu ayuda para difundir lo siguiente:\n \"" + tweet_text + "\" "
            print("\nPosting to facebook...")
            self.graph.put_object(
                parent_object="me",
                connection_name="feed",
                message=post_message,
                link=link_tweet
            )


    def connectToDB(self):
        # TODO Implement hanging case, attemps
        connected = False
        while not connected:
            try:
                print("Connecting to database...")
                self.db=_mysql.connect(
                    host=credentials.DB_HOST,
                    user=credentials.DB_USER,
                    passwd=credentials.DB_PASS,
                    db=credentials.DB_NAME
                )
                connected = True
            except:
                print("Failed connection, trying again...")
                sleep(10)


    def insertData(self, tweet, search_id):
        #user info
        userID = tweet.user.id_str

        # TODO What is this variable ?
        user_verified = tweet.user.verified

        if user_verified:
            verified = 'True'
        else:
            verified = 'False'
        followers_count = tweet.user.followers_count
        user_location = tweet.user.location
        user_name = tweet.user.screen_name
        #tweet info
        tweet_id = tweet.id
        tweet_dateF = tweet.created_at
        favorite_count = tweet.favorite_count
        retweet_count = tweet.retweet_count

        try:
            tweet_text = tweet.full_text
        except AttributeError:
            tweet_text = tweet.text
        #hashtags
        try:
            hashtag_objects = tweet.entities.hashtags
        except AttributeError:
            hashtag_objects = []
        #check media if it exists
        try:
            media_urls = tweet.entities.media
        except AttributeError:
            media_urls = []
            print("No media found")

        #check if user is following
        try:
            friendship = self.api.show_friendship(
                source_id=BOT_ID,
                target_id=userID
            )
            if friendship[1].following:
                isFollowing = 'True'
            else:
                isFollowing = 'False'
        except:
            isFollowing = 'False'

        #change date format
        tweet_date = tweet_dateF.strftime("%Y-%m-%d, %H%M%S")
        tweet_date = tweet_date[:10]

        #insert into users
        inserted = False
        # Move this string to a global string
        user_string = "INSERT INTO USERS (user_id, isFollowing, name, location, verified, followers_count) VALUES ("
        # Change it to a f"{}" string format
        user_string = user_string + userID + ", " + isFollowing + ", \'" + user_name + "\', \'" + user_location + "\', " + str(verified) + ", " + str(followers_count) + ")"
        print("running query:" + user_string)
        #EXAMPLE QUERY
        #db.query("""INSERT INTO USERS (user_id, isFollowing, numUses, name, location, verified, followers_count) VALUES (123, true, 7, 'bres', 'mexico', false, 300)""")

        #run query
        while not inserted:
            try:
                self.db.query(user_string)
                inserted = True
                print("Inserted user into DB!")
            except _mysql.IntegrityError as e:
                print(e)
                print("error inserting user")
                inserted = True
            except _mysql.OperationalError as e:
                print(e)
                print("disconected")
                self.connectToDB()
            except:
                print("UNKNOWN ERROR")
                raise
                inserted = True

        #insert into tweets
        inserted = False
        # Move this string to a global string
        tweet_string = "INSERT INTO TWEETS (tweet_id, user, tweet_text, favorite_count, retweet_count, search_id, date_created) VALUES("
        # Change it to a f"{}" string format
        tweet_string = tweet_string + str(tweet_id) + ", " + userID + ", \'" + tweet_text + "\'," + str(favorite_count) + ", " + str(retweet_count) + ", " + str(search_id) + ", \'" + tweet_date + "\')"

        print("running query:" + tweet_string)
        #run query
        while not inserted:
            try:
                self.db.query(tweet_string)
                print("Inserted tweet into DB!")
                inserted = True
            except _mysql.IntegrityError as e:
                # Why the 'inserted' variable is on when
                # an integrity error happened ?
                print("error inserting tweet")
                print(e)
                inserted = True
            except _mysql.OperationalError as e:
                print(e)
                print("disconected")
                self.connectToDB()
            except:
                print("UNKNOWN ERROR")
                raise
                inserted = True


        #insert into hashtags
        for hashtag in hashtag_objects:
            inserted = False
            HT = hashtag['text']
            hashtag_string = "INSERT INTO HASHTAGS (tweet_id, hashtag) VALUES("
            hashtag_string = hashtag_string + str(tweet_id) + ", \'" + HT + "\')"

            print("running query:" + hashtag_string)
            #run query
            while not inserted:
                try:
                    self.db.query(hashtag_string)
                    inserted = True
                    print("Inserted HT into DB!")
                except _mysql.IntegrityError as e:
                    # Why the 'inserted' variable is on when
                    # an integrity error happened ?
                    print("error inserting hashtag")
                    print(e)
                    inserted = True
                except _mysql.OperationalError as e:
                    print(e)
                    print("disconected")
                    self.connectToDB()
                except:
                    print("UNKNOWN ERROR")
                    raise
                    inserted = True

        #insert into tweet_links
        for url in media_urls:
            inserted = False
            link = url['media_url']
            # Move this string to a global string
            # Change it to a f"{}" string format
            media_string = "INSERT INTO TWEET_IMAGES (tweet_id, image_link) VALUES("
            media_string = media_string + str(tweet_id) + ", \'" + link + "\')"

            print("running query:" + media_string)
            #run query
            while not inserted:
                try:
                    self.db.query(media_string)
                    print("Inserted image into DB!")
                    inserted = True
                except _mysql.IntegrityError as e:
                    # Why the 'inserted' variable is on when
                    # an integrity error happened ?
                    print("error inserting image")
                    print(e)
                    inserted = True
                except _mysql.OperationalError as e:
                    print(e)
                    print("disconected")
                    self.connectToDB()
                except:
                    print("UNKNOWN ERROR")
                    raise
                    inserted = True


    #message function
    def message_function(self):
        last_seen_message = self.get_last_seen_message()
        messages = self.api.list_direct_messages(10)
        first = True
        for message in messages:
            message_timestamp = int(message.created_timestamp)
            if message_timestamp < last_seen_message:
                break
            
            if first:
                self.store_last_seen_message(message_timestamp)
                first = False
            reply_id = message.message_create['sender_id']
            if reply_id == BOT_ID:
                continue
            bot_message = (
                "Hola! Si necesitas que difunda un caso de desaparición "
                "puedes responder o etiquetarme con mi @ en el tweet que "
                "contenga la información o también puedes ingresar a www.botdesparecidx.com "
                "y en la sección de reportar puedes llenar un formulario para que difunda "
                "tu caso en mis redes! Si tienes otra duda puedes contactar "
                "a mi desarrollador."
            )
            self.api.send_direct_message(reply_id, bot_message)


    # mention function
    def mention_function(self):
        last_seen_id = self.get_last_seen_id()
        print(f"Last seen id = {last_seen_id}")
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
                        newuser = self.api.get_status(replyid, tweet_mode='extended')
                    except tweepy.TweepError as e:
                        # If there's an exception where the newuser is not
                        # initialized, the variable will not exist
                        # and the code will fail :(
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
                                    self.postFacebook(newuser)
                                    self.dumpTweet(newuser)
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
                            quotedTweet = self.api.get_status(
                                mention.quoted_status_id,
                                tweet_mode='extended'
                            )
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
                            quotedTweet.retweet()
                            print("Found mention!")
                            self.postFacebook(quotedTweet)
                            self.dumpTweet(quotedTweet)
                            self.insertData(quotedTweet, 2)
                        except tweepy.TweepError as e:
                                print(e)
                                print("rt error")

                    else:
                        try:
                            mention.retweet()
                            print("Found mention!")
                            self.postFacebook(mention)
                            self.dumpTweet(mention)
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
                    geocode='21.38,-101.33,1500km', # What is this location ?
                    lang='es',
                    result_type=result_type,
                    since=DATE_SINCE
                ).items(100)

                # search each tweet
                for tweet in tweets:
                    # 3 tweets per keyword
                    if tweet.user.id == BANNEDID:
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
                                        self.dumpTweet(tweet)
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
                                        sleep(1800) # Why this long ?
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
            sleep(1800) # Why this long ?


    def main(self):
        while True:
            print("Checking tweets...")
            self.worker()
            sleep(5)


if __name__ == '__main__':
    Bot().main()