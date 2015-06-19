#coding: utf-8
import requests
url = "http://hbds.hzlib.net:7080/huibendasai/toupiaoAction"
vote = 13968

for i in xrange(1, 56000):
	user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36"
	headers = {"Referer":"http://hbds.hzlib.net:7080/huibendasai/index", "user_agent":user_agent}
	data = {"hiddenID":"34h1", "toupiaoSubmit":u"投票(%d)" % vote}
	r = requests.post(url,data=data,headers=headers)
	print r.status_code, r.content
	vote += 1
	print vote, "ok"
