CREATE TABLE USERS (
    user_id BIGINT,
    isFollowing BOOLEAN,
	name VARCHAR(280),
	location VARCHAR(280),
    verified BOOLEAN,
    followers_count BIGINT,
    PRIMARY KEY(user_id)
);

CREATE TABLE TWEETS (
    tweet_id BIGINT,
    user BIGINT,
	tweet_text TEXT,
    favorite_count BIGINT,
	retweet_count BIGINT,
    search_id INT,
    date_created DATE,
    PRIMARY KEY(tweet_id),
    FOREIGN KEY(user) references USERS(user_id)
);

CREATE TABLE HASHTAGS (
    tweet_id BIGINT,
    hashtag VARCHAR(280),
    PRIMARY KEY(tweet_id, hashtag),
    FOREIGN KEY(tweet_id) references TWEETS(tweet_id)
);

CREATE TABLE TWEET_IMAGES (
	tweet_id BIGINT,
	image_link VARCHAR(280),
	PRIMARY KEY(tweet_id, image_link),
	FOREIGN KEY(tweet_id) references TWEETS(tweet_id)
);

CREATE TABLE PAGE_FORMS (
    nombre VARCHAR(280),
    sexo VARCHAR(280),
    edad INT,
    visto TEXT,
    fechaDes DATE,
    fechaFor DATE,
    rasgos TEXT,
    image_name VARCHAR(280),
    comentarios TEXT,
    email VARCHAR(280),
    PRIMARY KEY(email, nombre)
);
