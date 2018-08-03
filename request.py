# -*- coding: utf-8 -*-

import time, random, platform, hmac, hashlib, base64, json, traceback, datetime

version=platform.python_version_tuple()
if int(version[0]) == 2:
	input = raw_input
	toutf8 = lambda x: x and x.encode("utf-8")
	tostr = lambda x: x and x.decode("utf-8")
	from urllib2 import urlopen, Request, HTTPError,URLError
	from urllib import quote, urlencode
	from urlparse import parse_qs
else:
	input = input
	toutf8 = lambda x: x and bytes(str(x), "utf-8")
	tostr = lambda x: x and x.decode("utf-8")
	from urllib.request import urlopen, Request
	from urllib.parse import quote, urlencode, parse_qs
	from urllib.error import HTTPError,URLError



class response:
	def __init__(self, r):
		self.code = r[0]
		self.body = r[1]

	def getjson(self):
		return json.loads(self.body.decode('utf-8'))

	def getquery(self):
		return {k: v for k, v in [i.split("=") for i in self.body.split("&")]}


def avoid_exception(func):
	import functools
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		while True:
			try:
				return func(*args, **kwargs)
			except Exception as e:
				traceback.print_exc()
				time.sleep(5)
	return wrapper
def timeconverter(obj):
	if isinstance(obj,int):
		return datetime.datetime.fromtimestamp(obj)
	else:
		return int(time.mktime(obj.timetuple()))
def info(*args,**kwargs):
	min,sec=kwargs.get("min",0),kwargs.get("sec",0)
	if args:
		print("\t".join(args))
	if min or sec:
		print("sleep {0} min {1} sec".format(min,sec))
		time.sleep(min*60+sec)

def httpfunc(r):
	req=Request(url=r["url"], data=r["data"], headers=r["header"])
	req.get_method=lambda:r["method"]
	h = urlopen(req)
	return h.getcode(), tostr(h.read())


def request(method, url, param, header,**kwargs):
	method=method.upper()
	protocol=kwargs.get("protocol",None)
	if not protocol:
		if method == "GET":
			r={
				"method":method,
				"url":url + "?" + urlencode(param) if param else url,
				"data":None,
				"header":header or {}
			}
		else:
			r={
				"method":method,
				"url":url,
				"data":toutf8(urlencode(param)) if isinstance(param,dict) else param,
				"header":header or {}
			}
	if protocol=="oauth1":
		kwargs["type"]=kwargs.get("type","json")
		acckey, accsec = kwargs.get("acckey",""),kwargs.get("accsec","")
		conkey, consec = kwargs.get("conkey",""),kwargs.get("consec","")
		baseparam = {
			"oauth_token": acckey,
			"oauth_consumer_key": conkey,
			"oauth_signature_method": "HMAC-SHA1",
			"oauth_timestamp": str(int(time.time())),
			"oauth_nonce": str(random.getrandbits(64)),
			"oauth_version": "1.0"
		}
		signature = dict(baseparam)
		signature.update(param)
		signature = '&'.join('{0}={1}'.format(quote(key, ''), quote(signature[key], '~')) for key in sorted(signature))
		signature = ("{0}&{1}".format(consec, accsec), '{0}&{1}&{2}'.format(method, quote(url, ''), quote(signature, '')))
		signature = base64.b64encode(hmac.new(toutf8(signature[0]), toutf8(signature[1]), hashlib.sha1).digest())
		header = dict(baseparam)
		header.update({"oauth_signature": signature})
		header = ",".join("{0}={1}".format(quote(k, ''), quote(header[k], '~')) for k in sorted(header))
		header = {"Authorization": 'OAuth {0}'.format(header)}
		if method == "GET":
			r={
				"method":method,
				"url":url + "?" + urlencode(param) if param else url,
				"data":None,
				"header":header
			}
		else:
			r={
				"method":method,
				"url":url,
				"data":toutf8(urlencode(param)),
				"header":header
			}
	if protocol=="coincheck":
		kwargs["type"]=kwargs.get("type","json")
		conkey, consec = kwargs.get("conkey",""),kwargs.get("consec","")
		url = "https://coincheck.com/api" + url
		nonce = str(int(time.time() * 1000000000))
		param=urlencode(param) if param else str()
		signature = hmac.new(toutf8(consec), toutf8(nonce + url + param), hashlib.sha256).hexdigest()
		header = {"ACCESS-KEY": conkey, "ACCESS-NONCE": nonce, "ACCESS-SIGNATURE": signature}
		if method == "GET":
			r={
				"method":method,
				"url":url + "?" + param if param else url,
				"data":None,
				"header":header
			}
		else:
			r={
				"method":method,
				"url":url,
				"data":toutf8(param),
				"header":header
			}
	if kwargs.get("open",True):
		r=httpfunc(r)
		t=kwargs.get("type",None)
		if not t:
			pass
		if t=="query":
			r={k: v for k, v in [i.split("=") for i in r[1].split("&")]}
		if t=="json":
			r=json.loads(r[1])
	return r


def request_oauth10(consumer_key, consumer_secret, access_token, access_token_secret, method, url, param):
	method = method.upper()
	access_token, access_token_secret = access_token or "", access_token_secret or ""
	param = {k: v for k, v in [pair.split("=") for pair in param.split("&")]} if isinstance(param, str) else param
	param = {k: v for k, v in (parse_qs(param) if isinstance(param, str) else param).items()}
	baseparam = {
		"oauth_token": access_token,
		"oauth_consumer_key": consumer_key,
		"oauth_signature_method": "HMAC-SHA1",
		"oauth_timestamp": str(int(time.time())),
		"oauth_nonce": str(random.getrandbits(64)),
		"oauth_version": "1.0"
	}
	signature = dict(baseparam)
	signature.update(param)
	signature = '&'.join('{0}={1}'.format(quote(key, ''), quote(signature[key], '~')) for key in sorted(signature))
	signature = ("{0}&{1}".format(consumer_secret, access_token_secret), '{0}&{1}&{2}'.format(method, quote(url, ''), quote(signature, '')))
	signature = base64.b64encode(hmac.new(toutf8(signature[0]), toutf8(signature[1]), hashlib.sha1).digest())
	header = dict(baseparam)
	header.update({"oauth_signature": signature})
	header = ",".join("{0}={1}".format(quote(k, ''), quote(header[k], '~')) for k in sorted(header))
	header = {"Authorization": 'OAuth {0}'.format(header)}
	if method == "GET":
		return request(method, url, param, None, header)
	if method == "POST":
		return request(method, url, None, urlencode(param), header)


def twitter_post_test(consumer_key, consumer_secret, callback):
	r = request_oauth10(consumer_key, consumer_secret, None, None, "POST", "https://api.twitter.com/oauth/request_token", callback or {"oauth_callback": callback})
	print("open {0}?{1}".format("https://api.twitter.com/oauth/authorize", r.body))
	r = r.getquery()
	r["oauth_verifier"] = input("varifier:")
	r = request_oauth10(consumer_key, consumer_secret, None, None, "GET", "https://api.twitter.com/oauth/access_token", r).getquery()
	tk, ts = r["oauth_token"], r["oauth_token_secret"]
	r = request_oauth10(consumer_key, consumer_secret, tk, ts, "POST", "https://api.twitter.com/1.1/statuses/update.json", {"status": "そろそろ大阪へ向かおう"})
	print(r.getjson())
