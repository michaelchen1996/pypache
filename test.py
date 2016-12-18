import configparser
import re

c = configparser.ConfigParser()
c.read("config.ini")
# print(c['server']['default'])
c['server']['default']
# print(c)

default_page = b'''HTTP/1.1 200 OK\r
Accept-Ranges: bytes\r
Cache-Control: max-age=0\r
Content-Length: 12\r
Content-Type: text/html; charset=utf-8\r
Date: Mon, 05 Dec 2016 01:30:46 GMT\r\
Etag: "12345"\r
Expires: Mon, 05 Dec 2016 01:30:46 GMT\r
Last-Modified: Fri, 23 Oct 2009 08:06:04 GMT\r
Server: pypache/1.0\r
\r
hello world!'''

request_page = b'''POST /loginAction.do HTTP/1.1\r
Host: 202.115.47.141\r
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r
Accept-Encoding: gzip, deflate\r
Accept-Language: zh-cn\r
Content-Type: application/x-www-form-urlencoded\r
Origin: http://202.115.47.141\r
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Safari/602.1.50\r
Connection: keep-alive\r
Upgrade-Insecure-Requests: 1\r
Referer: http://202.115.47.141/login.jsp\r
Content-Length: 32\r
Cookie: JSESSIONID=dca7OgNETQ70QhB18noJv\r
\r
zjh=2014141463007&mm=michael2jwc'''
# print(str)


# print(re.match(r'\O', request_page.decode("utf-8")).group(0))
# print(request_page[:2]==b'PO')
dict = {}
dict.update((('a', 1),))
# print(dict)
import time

t = 'Fri, 23 Oct 2009 08:06:04 GMT'
temp = time.strptime(t, "%a, %d %b %Y %H:%M:%S GMT")
print(time.mktime(time.strptime(t, "%a, %d %b %Y %H:%M:%S GMT")))
print(time.time())
