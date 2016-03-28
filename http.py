
import socket

GET = 'GET'
POST = 'POST'

class E404(Exception):
    """custom exception for 404s
    """
    pass

class http:

    def __init__(self, hostname):
        """set up a http connection
        """
        self.hostname = hostname
        self.connect()
        self.cookies = {}

    def connect(self):
        """ititialize a tcp socket connested to the host
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.hostname, 80))
        self.sock.settimeout(10)


    def update_or_create_cookie(self, cookie):
        """handle cookies
        """
        cook = cookie.split('; ')[0].split('=')
        self.cookies[cook[0]] = cook[1]

    def format_cookies(self):
        """return cookies in format for http header
        """
        return "; ".join(["{k}={v}".format(k=k,v=v) for k,v in self.cookies.iteritems()])

    def create_request(self, method, path, data=''):
        """create an http request
        """
        return """{method} {path} HTTP/1.1
Host: {host}
Connection: keep-alive
Content-Length: {length}
Cookie: {cookies}

{data}""".format(method=method, path=path, host=self.hostname, data=data, cookies=self.format_cookies(), length=len(data))

    def get_chunked_data(self, chunk):
        """'handle' chunked http responses
        """
        length_hex, data = chunk.split("\r\n", 1)
        length = int(length_hex, 16)
        read_extra = length - len(data)
        while read_extra > 0:
            data += self.sock.recv(read_extra)
            read_extra = length - len(data)
        while not data.endswith("0\r\n\r\n"):
            data += self.sock.recv(512)
        return data

    def get_response(self):
        """get http response and handle some headers and response codes
        """
        resp = self.sock.recv(1024)
        headers, data = resp.split("\r\n\r\n", 1)
        read_extra = 0
        lines = headers.splitlines()
        status = int(lines[0].split(' ')[1])
        redir_loc = ''
        for l in lines[1:]:
            l = l.split(': ', 1)
            if l[0] == 'Location':
                redir_loc = '/' + l[1].split('/',3)[-1]
            if l[0] == 'Set-Cookie':
                self.update_or_create_cookie(l[1])
            if l[0] == 'Content-Length':
                length = int(l[1])
                read_extra = length - len(data)
                while read_extra:
                    data += self.sock.recv(read_extra)
                    read_extra = length - len(data)
            if l[0] == 'Transfer-Encoding':
                if l[1] == 'chunked' and status != 500:
                    data = self.get_chunked_data(data)
            if l[0] == 'Connection':
                if l[1] == 'close':
                    self.connect()
                    return 500, '', '' # fool get mehtod in to retrying request
        return status, redir_loc, data

    def post(self, path, data):
        """send http post request
        """
        self.sock.send(self.create_request(POST, path, data=data))
        status, redir_loc, _ = self.get_response()
        return status, redir_loc

    def get(self, path):
        """send http get request
        """
        self.sock.send(self.create_request(GET, path))
        status, redir_loc, data = self.get_response()
        if status == 200:
            return data
        elif status == 302:
            return self.get(redir_loc)
        elif status == 500:
            return self.get(path)
        elif status == 404:
            raise E404
