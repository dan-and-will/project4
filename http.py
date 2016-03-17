
import socket

GET = 'GET'
POST = 'POST'

class http:

    def __init__(self, hostname):
        self.hostname = hostname
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((hostname, 80))
        self.cookies = {}

    def update_or_create_cookie(self, cookie):
        # csrftoken=ae23898253d0594d1997071e8466c71e; expires=Thu, 16-Mar-2017 19:45:57 GMT; Max-Age=31449600; Path=/
        cook = cookie.split('; ')[0].split('=')
        self.cookies[cook[0]] = cook[1]

    def format_cookies(self):
        return "; ".join(["{k}={v}".format(k=k,v=v) for k,v in self.cookies.iteritems()])

    def make_request(self, method, path, data=''):
        h = """{method} {path} HTTP/1.1
Host: {host}
Connection: keep-alive
Content-Length: {length}
Cookie: {cookies}

{data}
""".format(method=method, path=path, host=self.hostname, data=data, cookies=self.format_cookies(), length=len(data))
        if method == 'POST':
            print repr(h)
            print "\n\n\n\n"
        return h

    def parse_response(self, resp):
        headers, data = resp.split("\r\n\r\n", 1)

        lines = headers.splitlines()
        status = int(lines[0].split(' ')[1])
        headers_dict = {}
        for l in lines:
            if ':' in l:
                l = l.split(': ', 1)
                # headers_dict[l[0]] = l[1]
                if l[0] == 'Location':
                    data = l[1]
                if l[0] == 'Set-Cookie':
                    self.update_or_create_cookie(l[1])
        return status, headers_dict, data

    def post(self, path, data):
        self.sock.send(self.make_request(POST, path, data=data))
        resp = self.sock.recv(2048)
        print resp

    def get(self, path):
        self.sock.send(self.make_request(GET, path))
        resp = self.sock.recv(2048)
        (status, headers, data) = self.parse_response(resp)
        if status == 200:
            return data
        elif status == 302:
            new_path = '/' + data.split('/',3)[-1]
            return self.get(new_path)
        elif status == 500:
            return self.get(path)
