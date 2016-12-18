import socket
import threading
import time
import configparser
import re
import os

sample_response = b'''HTTP/1.1 200 OK\r
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

sample_request = b'''POST /loginAction.do HTTP/1.1\r
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

responses = {
    100: ('Continue', 'Request received, please continue'),
    101: ('Switching Protocols',
          'Switching to new protocol; obey Upgrade header'),

    200: ('OK', 'Request fulfilled, document follows'),
    201: ('Created', 'Document created, URL follows'),
    202: ('Accepted',
          'Request accepted, processing continues off-line'),
    203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
    204: ('No Content', 'Request fulfilled, nothing follows'),
    205: ('Reset Content', 'Clear input form for further input.'),
    206: ('Partial Content', 'Partial content follows.'),

    300: ('Multiple Choices',
          'Object has several resources -- see URI list'),
    301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
    302: ('Found', 'Object moved temporarily -- see URI list'),
    303: ('See Other', 'Object moved -- see Method and URL list'),
    304: ('Not Modified',
          'Document has not changed since given time'),
    305: ('Use Proxy',
          'You must use proxy specified in Location to access this '
          'resource.'),
    307: ('Temporary Redirect',
          'Object moved temporarily -- see URI list'),

    400: ('Bad Request',
          'Bad request syntax or unsupported method'),
    401: ('Unauthorized',
          'No permission -- see authorization schemes'),
    402: ('Payment Required',
          'No payment -- see charging schemes'),
    403: ('Forbidden',
          'Request forbidden -- authorization will not help'),
    404: ('Not Found', 'Nothing matches the given URI'),
    405: ('Method Not Allowed',
          'Specified method is invalid for this resource.'),
    406: ('Not Acceptable', 'URI not available in preferred format.'),
    407: ('Proxy Authentication Required', 'You must authenticate with '
                                           'this proxy before proceeding.'),
    408: ('Request Timeout', 'Request timed out; try again later.'),
    409: ('Conflict', 'Request conflict.'),
    410: ('Gone',
          'URI no longer exists and has been permanently removed.'),
    411: ('Length Required', 'Client must specify Content-Length.'),
    412: ('Precondition Failed', 'Precondition in headers is false.'),
    413: ('Request Entity Too Large', 'Entity is too large.'),
    414: ('Request-URI Too Long', 'URI is too long.'),
    415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
    416: ('Requested Range Not Satisfiable',
          'Cannot satisfy request range.'),
    417: ('Expectation Failed',
          'Expect condition could not be satisfied.'),

    500: ('Internal Server Error', 'Server got itself in trouble'),
    501: ('Not Implemented',
          'Server does not support this operation'),
    502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
    503: ('Service Unavailable',
          'The server cannot process the request due to a high load'),
    504: ('Gateway Timeout',
          'The gateway server did not receive a timely response'),
    505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
}


class HTTP(object):
    def __init__(self):
        self.header = {}
        self.version = ''
        self.data = b''

    def getData(self):
        return self.data

    def setData(self, data):
        self.data = data

    def getVersion(self):
        return self.version

    def setVersion(self, version):
        self.version = version


class HTTPRequest(HTTP):
    def __init__(self):
        HTTP.__init__(self)
        self.method = ''
        self.path = ''
        self.is_first = True
        self.is_header = True

    def recv(self, r_data):
        self.data += r_data
        if self.is_first:
            ret = re.match(r'([A-Z]*) ([\S]*) ([\S]*)\r\n', self.data.decode('utf-8'))
            if not ret:
                return False
            self.method = ret.group(1)
            self.path = ret.group(2)
            self.version = ret.group(3)
            self.data = self.data[len(ret.group(0)):]
            self.is_first = False
        while self.is_header:
            ret = re.match(r'([\S]*): ([\S ]*)\r\n', self.data.decode('utf-8'))
            if ret:
                self.header.update(((ret.group(1), ret.group(2)),))
                self.data = self.data[len(ret.group(0)):]
            elif re.match(r'\A\r\n', self.data.decode('utf-8')):
                self.data = self.data[2:]
                self.is_header = False
            else:
                return False
        if 'Content-Length' in self.header and len(self.data) < int(self.header.get('Content-Length')):
            return False
        else:
            return True


class HTTPResponse(HTTP):
    def __init__(self):
        HTTP.__init__(self)
        self.code = ''
        self.status = ''

    def dump2bytes(self):
        data = self.version + ' ' + self.code + ' ' + self.status + '\r\n'
        for key, value in self.header:
            data += key + ': ' + value + '\r\n'
        data += '\r\n'
        r_data = data.encode('utf-8')
        r_data += self.data
        return r_data

    def setCode(self, code):
        print(code)
        self.code = code
        self.status = responses[int(code)][0]
        info = responses[int(self.code)][1]
        self.data = ('<html><body><h1>%s %s</h1><p>%s</p></body></html>' % (self.code, self.status, info)).encode(
            'utf-8')

    def make_response(self, http_request):
        time.sleep(5)
        self.version = http_request.getVersion()
        # get param and path
        # error in path and param
        path = config.get('server', 'root') + http_request.path
        is_file = False
        # find file
        try:
            f = open(path, 'r')
            is_file = True
        except IOError:
            for i in config.get('server', 'default').split('\n'):
                default_path = path
                if path[-1] == '/':
                    default_path += i
                else:
                    default_path += '/' + i
                try:
                    f = open(default_path, 'r')
                    is_file = True
                except IOError:
                    pass
                if is_file:
                    break
            if not is_file:
                print(path)
                if os.path.exists(path):
                    self.setCode('403')
                else:
                    self.setCode('404')
        if is_file:
            last_time = http_request.header.get('Last-Modified')
            # Last-Modified: Fri, 23 Oct 2009 08:06:04 GMT
            if last_time and time.mktime(time.strptime(last_time, "%a, %d %b %Y %H:%M:%S GMT")) > os.stat(
                    path).st_mtime:
                self.setCode('304')
            else:
                self.setCode('200')
                self.data = f.read().encode('utf-8')
            f.close()


def task(connection, address):
    # multi-thread test
    global connect_num

    lock.acquire()
    connect_num += 1
    lock.release()

    # time.sleep(5)
    http_request = HTTPRequest()
    while True:
        d = connection.recv(config.getint('server', 'recv_buf_size'))
        if http_request.recv(d):
            break
            # response content
    http_response = HTTPResponse()
    http_response.make_response(http_request)
    connection.sendall(http_response.dump2bytes())
    connection.close()

    lock.acquire()
    connect_num -= 1
    lock.release()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.ini")

    if not os.path.exists(config.get('server', 'root')):
        os.makedirs(config.get('server', 'root'))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((config.get('server', 'host'), config.getint('server', 'port')))
    sock.listen(config.getint('server', 'max_connect'))
    connect_num = 0
    lock = threading.Lock()

    while True:
        if connect_num < config.getint('server', 'max_connect'):
            t = threading.Thread(target=task, args=sock.accept())
            t.start()
