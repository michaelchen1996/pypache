import socket
import threading
import time
import configparser
import re
import os
import importlib
import uuid

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
zjh=000000000000&mm=11111111'''

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
    def __init__(self, header=None, version='', data=b''):
        self.header = header
        if header is None:
            self.header = {}
        self.version = version
        self.data = data


class HTTPRequest(HTTP):
    def __init__(self, method=None, path=None):
        HTTP.__init__(self)
        self.method = method
        self.path = path
        self.parameters = {}

    def getCookie(self):
        if 'Cookie' in self.header:
            return self.header['Cookie']
        return None


class HTTPResponse(HTTP):
    def __init__(self):
        HTTP.__init__(self)
        self.code = ''
        self.status = ''
        self.version = ''
        self.data = b''

    def dump2bytes(self):
        data = self.version + ' ' + self.code + ' ' + self.status + '\r\n'
        for key in self.header:
            value = self.header[key]
            data += key + ': ' + value + '\r\n'
        # 设置默认值
        # if 'Content-Type' not in self.header:
        #     data += 'Content-Type: text/html\r\n'
        data += '\r\n'
        r_data = data.encode('utf-8')
        r_data += self.data
        return r_data

    def setCode(self, code):
        code = str(code)
        print(code)
        self.code = code
        self.status = responses[int(code)][0]
        info = responses[int(self.code)][1]
        self.data = ('<html><body><h1>%s %s</h1><p>%s</p></body></html>' % (self.code, self.status, info)).encode(
            'utf-8')

    def setCookie(self, cookie):
        self.header['Set-Cookie'] = cookie

    def setContentType(self, content_type):
        self.header['Content-Type'] = content_type

    def setDate(self, date):
        self.header['Date'] = date


class HTTPWebServer(object):
    def __init__(self, config_filename='config.ini'):
        # Prepare to read .ini file
        config = configparser.ConfigParser()
        config.read(config_filename)
        # read the parameters from .ini file
        self.max_connect_num = config.getint('server', 'max_connect')
        self.connect_num = 0
        self.app_root = config.get('server', 'root')
        self.port = config.getint('server', 'port')
        self.recv_buf_size = config.getint('server', 'recv_buf_size')
        self.default_pages = config.get('server', 'default').split('\n')
        self.lock = threading.Lock()
        self.api_content = open("WebServerAPI.py").read()
        # run
        self.__run()

    def __run(self):
        if not os.path.exists(self.app_root):
            os.makedirs(self.app_root)
        # Establish TCP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', self.port))
        self.sock.listen(self.max_connect_num)
        while True:
            if self.connect_num < self.max_connect_num:
                threading.Thread(target=HTTPWebServer.__connection_task, args=((self,) + self.sock.accept())).start()

    def __connection_task(self, connection, addr):
        self.lock.acquire()
        self.connect_num += 1
        self.lock.release()
        receive_data = b''
        while True:
            receive_data += connection.recv(self.recv_buf_size)
            success, http_request = self.__parse_request(receive_data)
            if success:
                break
        # response content
        http_response = self.__make_response(http_request)
        connection.sendall(http_response.dump2bytes())
        connection.close()

        self.lock.acquire()
        self.connect_num -= 1
        self.lock.release()

    # parse the http request from client
    def __parse_request(self, r_data):
        # get the parameter
        def get_parameter(src_str):
            for triple in re.findall(r'(^|&)([a-zA-Z0-9]+)=([^&]*)', src_str):
                http_request.parameters[triple[1]] = triple[2]

        http_request = HTTPRequest()
        ret = re.match(r'([A-Z]*) ([\S]*) ([\S]*)\r\n', r_data.decode('utf-8'))
        if not ret:
            return False, None
        http_request.method = ret.group(1)
        uri = ret.group(2).split('?')
        http_request.path = uri[0]
        if len(uri) > 1:
            get_parameter(uri[1])
        http_request.version = ret.group(3)
        parsing_pos = len(ret.group(0))
        # compile the pattern
        regular = re.compile(r'([\S]*): ([\S ]*)\r\n')
        ret = regular.match(r_data.decode('utf-8'), pos=parsing_pos)
        while ret:
            http_request.header[ret.group(1)] = ret.group(2)
            parsing_pos += len(ret.group(0))
            ret = regular.match(r_data.decode('utf-8'), pos=parsing_pos)
        # match the end of header
        regular_end = re.compile(r'\r\n')
        if regular_end.match(r_data.decode('utf-8'), pos=parsing_pos):
            parsing_pos += 2
        else:
            return False, None
        print(http_request.header)
        http_request.data = r_data[parsing_pos:]
        if 'Content-Length' in http_request.header \
                and len(http_request.data) < int(http_request.header.get('Content-Length')):
            return False, None

        get_parameter(http_request.data.decode('utf-8'))
        print(http_request.parameters)
        return True, http_request

    def __make_response(self, http_request: HTTPRequest):
        http_response = HTTPResponse()
        http_response.version = http_request.version
        path = self.app_root + http_request.path
        if os.path.isdir(path):
            for default_page in self.default_pages:
                if path[-1] == '/':
                    path += default_page
                else:
                    path += '/' + default_page
                if os.path.isfile(path):
                    break
        if os.path.isfile(path):
            try:
                f = open(path, 'br')
                last_time = http_request.header.get('Last-Modified')
                # Last-Modified: Fri, 23 Oct 2009 08:06:04 GMT
                if last_time and time.mktime(time.strptime(last_time, "%a, %d %b %Y %H:%M:%S GMT")) > os.stat(
                        path).st_mtime:
                    http_response.setCode('304')
                else:
                    http_response.setCode('200')
                    if path.split('.')[-1] == 'py':
                        # 动态页面
                        # 准备data
                        data = {'params': http_request.parameters, 'cookie': http_request.getCookie(),
                                'reqType': http_request.method}
                        out = ""
                        # 生成命名管道名
                        pipe_name = str(uuid.uuid4())
                        # 创建管道
                        if not os.path.exists(pipe_name):
                            os.mkfifo(pipe_name)

                        pid = os.fork()
                        if pid != 0:
                            # in parent
                            pipe = open(pipe_name, 'r')
                            rt = pipe.readline()
                            reg_command = re.compile(r'command:([\S]*)')
                            reg_out = re.compile(r'out:([\S]*)')
                            reg_end = re.compile(r'end:')

                            # 下面这部分写得有点反人类，但是我还没有找到更好方法:)
                            # call by command in eval
                            def setCookie(cookie):
                                http_response.setCookie(cookie)

                            def setContentType(content_type):
                                http_response.setContentType(content_type)

                            def setCode(code):
                                http_response.setCode(code)

                            while rt:
                                ret_command = reg_command.match(rt)
                                if ret_command:
                                    eval(ret_command.group(1))
                                    rt = pipe.readline()
                                    continue
                                ret_out = reg_out.match(rt)
                                if ret_out:
                                    out += ret_out.group(1)
                                    rt = pipe.readline()
                                    continue
                                ret_end = reg_end.match(rt)
                                if reg_end:
                                    ret_end.group(1)
                                    break
                            # 关闭和删除命名管道
                            pipe.close()
                            os.remove(pipe_name)
                        else:
                            # in child
                            os.execlp('python3', 'python3', path, '--pipe_name', pipe_name, '--data', str(data))
                            pass
                        http_response.data = out.encode('utf-8')

                    else:
                        # 静态页面
                        http_response.data = f.read()
                        postfix = path.split('.')[-1].lower()
                        if postfix in ['txt', 'html', 'htm']:
                            http_response.setContentType('text/html')
                        elif postfix in ['jpg', 'jpeg']:
                            http_response.setContentType('image/jpeg')
                        elif postfix == 'png':
                            http_response.setContentType('image/png')
                        elif postfix == 'gif':
                            http_response.setContentType('image/gif')
                        elif postfix == 'svg':
                            http_response.setContentType('image/svg+xml')
                        elif postfix == 'css':
                            http_response.setContentType('text/css')
                        elif postfix == 'js':
                            http_response.setContentType('application/javascript')
                        elif postfix == 'json':
                            http_response.setContentType('application/json')
                f.close()
            except IOError:
                print(str(IOError) + path)
                http_response.setCode('403')
        else:
            http_response.setCode('404')
        return http_response


if __name__ == '__main__':
    server = HTTPWebServer(config_filename="config.ini")
