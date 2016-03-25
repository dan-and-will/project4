
import socket

GET = 'GET'
POST = 'POST'

class http:

    def __init__(self, hostname):
        self.hostname = hostname
        self.connect()
        self.cookies = {}
        self.l=[]

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.hostname, 80))
        self.sock.settimeout(10)


    def update_or_create_cookie(self, cookie):
        # csrftoken=ae23898253d0594d1997071e8466c71e; expires=Thu, 16-Mar-2017 19:45:57 GMT; Max-Age=31449600; Path=/
        cook = cookie.split('; ')[0].split('=')
        self.cookies[cook[0]] = cook[1]

    def format_cookies(self):
        return "; ".join(["{k}={v}".format(k=k,v=v) for k,v in self.cookies.iteritems()])

    def create_request(self, method, path, data=''):
        h = """{method} {path} HTTP/1.1
Host: {host}
Connection: keep-alive
Content-Length: {length}
Cookie: {cookies}

{data}""".format(method=method, path=path, host=self.hostname, data=data, cookies=self.format_cookies(), length=len(data))
        return h

    def get_chunked_data(self, chunk):
        length_hex, data = chunk.split("\r\n", 1)
        length = int(length_hex, 16)
        read_extra = length - len(data)
        while read_extra > 0:
            try:
                data += self.sock.recv(read_extra)
            except:
                print repr(data)
                print length, len(data), read_extra
                raise
            read_extra = length - len(data)
        while not data.endswith("0\r\n\r\n"):
            chunk = self.sock.recv(16)
            # print repr(chunk)
            # print length, len(data)
            data += chunk
        # raise Exception("WILL")
        return data

    def get_response(self):
        resp = self.sock.recv(1024)
        try:
            headers, data = resp.split("\r\n\r\n", 1)
        except:
            print self.l[-1]
            print "\n\n\nIT BLEW UP\n", repr(resp)
            raise
        self.l.append(resp)
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
                    # print "\n\nREAD EXTRA: {a} {b} {c}".format(a=read_extra,b=length, c=len(data))
                    data += self.sock.recv(read_extra)
                    read_extra = length - len(data)
                    # print "READ EXTRA: {a} {b} {c}".format(a=read_extra,b=length, c=len(data))
            if l[0] == 'Transfer-Encoding':
                if l[1] == 'chunked' and status != 500:
                    # print 'CHUNKED'
                    try:
                        data = self.get_chunked_data(data)
                    except:
                        print headers
                        raise
            if l[0] == 'Connection':
                if l[1] == 'close':
                    self.connect()
                    return 500, '', ''
        return status, redir_loc, data

    def post(self, path, data):
        self.sock.send(self.create_request(POST, path, data=data))
        # resp = self.sock.recv(4096)
        # (status, data) = self.parse_response(resp)
        status, redir_loc, _ = self.get_response()
        return status, redir_loc

    def get(self, path):
        self.sock.send(self.create_request(GET, path))
        # resp = self.sock.recv(4096)
        # try:
        #     (status, data) = self.parse_response(resp)
        # except:
        #     print resp
        #     raisey
        status, redir_loc, data = self.get_response()
        if status == 200:
            return data
        elif status == 302:
            return self.get(redir_loc)
        elif status == 500:
            # print "500\n"
            return self.get(path)
