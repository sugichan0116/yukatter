# -*- coding: utf8 -*-
import request,json
from datetime import timedelta, datetime, timezone
from dateutil import parser
import codecs
import math

system = {
    "paths":{
        "index":"index.html",
        "setting":"setting.json",
        "design":"site.html",
        "card":"card.html"
    },
    "keys":{
        "protocol":"oauth1",
        "conkey":"mCPWWS6PazLgF36jkUnG4oPIT",
        "consec":"deqbZQubFuYWTWznQV2WfNL93sXoOSyZZsnkefJABb1taXwhYP"
    }
}

def systemSetup():
    print("system setup");
    paths = system["paths"]
    # system["export"] = open(paths["index"],"wb") #debug
    f=open(paths["setting"], "rb")
    system["setting"] = json.loads(f.read().decode("utf-8"))

    f=open(paths["design"], "rb")
    system["design"] = f.read().decode("utf-8")

    f=open(paths["card"], "rb")
    system["card"] = f.read().decode("utf-8")

def sendQuery():
    print("send query");
    setting = system["setting"]
    keyword = setting["keyword"]

    date = datetime.now(timezone.utc) - timedelta(days=keyword["DAY"])
    since = timeParse(date) + "_00:00:00_JST"
    until = timeParse(date + timedelta(days=0)) + "_23:59:59_JST"

    print("since:" + since)
    print("until:" + until)

    search = {
        "OR":keyword["OR"],
        "NOT":keyword["NOT"],
        "MIN":keyword["MIN"],
        "TIME":" since:{0} until:{1} ".format(since, until),
        "FILTER":keyword["FILTER"],
    }

    if keyword["DAY"] == 0:
        search["TIME"] = ""

    query = search["OR"] + search["NOT"] + search["MIN"] + search["TIME"] + search["FILTER"]
    count = setting["count"]

    print("query: " + query)

    tweets = []

    max_id = ""
    for i in range(setting["count"]):
        r = request.request(
            "GET",
            "https://api.twitter.com/1.1/search/tweets.json",
            {
                "q":query,
                "count":"100",
                "max_id":max_id
            },
            None,
            **system["keys"]
        )
        print(r)
        content = r["statuses"]
        print(len(content))
        if len(content) == 0:
            break
        max_id = str(content[-1]["id"] - 1)
        print(max_id)
        tweets.extend(content)
    return tweets

def parseAPI(request):
    print("parse request api");
    images = []

    text = "" # for debug log
    print("    length:" + str(len(request)));

    for tweet in request:
        if not tweet.get("retweeted_status",None):
            #debug
            # text += tweet["text"]+"</br>"

            try:
                media_list = tweet["extended_entities"]["media"]
                user = tweet["user"]
                for media in media_list:
                    image = {
                        "url":media["media_url"],
                         "retweet":tweet["retweet_count"],
                        "favorite":tweet["favorite_count"],
                        "text":tweet["text"],
                        "bio":user["description"],
                        "follower":user["followers_count"],
                        "time":tweet["created_at"],
                        "tweet":"https://twitter.com/" + user["name"] + "/status/" + tweet["id_str"],
                        }
                    images.append(image)
            except KeyError:
                continue
    system["log"] = text
    return images

def sortImage(images):
    print("sort image data");
    setting = system["setting"]
    keywords = setting["text"]
    biowords = setting["bio"]
    for image in images:
        keyPoint = pointByWords(image["text"], keywords)
        bioPoint = pointByWords(image["bio"], biowords)
        image["score"] = image["favorite"] + 2 * image["retweet"] + keyPoint + bioPoint
        time = (datetime.now(timezone.utc) - parser.parse(image["time"])).total_seconds()
        image["score"] *= 2 - math.tanh(time / setting["time-pickup"] / 2 * math.log(3))
        image["debug"] = str(keyPoint) + "/" + str(bioPoint) + "/" + str(2 - math.tanh(time / 10000 / 2 * math.log(3)))

    images.sort(
        key=lambda x:x["score"],
         reverse=True
    )

    return images

def writePage(images):
    print("write web page");
    html = ""
    container = ""
    setting = system["setting"]
    text = str(setting["min-score"]) + "/" + str(setting["count"])

    for image in images:
        if image["score"] < setting["min-score"]:
            continue
        # time = datetime.datetime.now() - datetime.datetime.strptime(image["time"], '%a %m %d %H:%M:%S %Z %Y')
        time = datetime.now(timezone.utc) - parser.parse(image["time"])
        container += system["card"].format(time,
            image["url"],
            image["retweet"],
            image["favorite"],
            "{:.32}".format(image["text"]) + "..." + image["debug"],
            image["tweet"],
            int(image["score"])
        )

    html = system["design"].format(str(len(images)), text, container)

    with open(system["paths"]["index"], "wb") as f:
        f.write((html).encode("utf-8"))

#helper
def timeParse(time):
    return time.strftime("%Y-%m-%d")

def matchWord(text, word, point):
    return (point if text.find(word) > 0 else 0)

def pointByWords(text, data):
    sum = 0
    for t in data:
        sum += matchWord(text, t["word"], t["point"])
    return sum

systemSetup()
images = sortImage(parseAPI(sendQuery()))
writePage(images)
