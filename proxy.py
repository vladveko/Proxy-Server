import socket 
import threading
import signal
import sys

def parse_url(url):
    # Find position of ://
    pos = url.find("://")

    # If there is ://, get the rest of url
    if pos != -1:
        url = url[(pos+3):]

    # Get the port position, if any
    port_pos = url.find(":")

    server_pos = url.find("/")
    if server_pos == -1:
        server_pos = len(url)
    #     webserver = url[:server_pos]
    # else:
    #     webserver = url[server_pos+1:]


    if port_pos == -1:
        # Default port
        port = 80
        webserver = url[:server_pos]

    else:
        # Specific port
        port = int(url[port_pos+1:server_pos])
        webserver = url[:port_pos]

    return (webserver, port)

def alter_request(request):
    # Parse the request into lines and get first line
    line = request.split("\n")[0]
    # Parse the first line into words
    words = line.split(" ")

    # If it's not GET request, quit
    if words[0] != "GET":
        return request

    # If it is, then alter GET request
    
    # Get url
    url = words[1]
    # Find position of ://
    pos = url.find("://")

    # If there is ://, get the rest of url
    if pos != -1:
        abs_path = url[(pos+3):]

    # Find position of /
    pos = abs_path.find("/")
    if pos != -1:
        # Get absolute path
        abs_path = abs_path[pos:]

    return request.replace(url, abs_path, 1)

def getresponsecode(response):
    status_line = response.decode('utf-8', 'ignore').split("\n")[0]
    
    if status_line.find("HTTP") == -1:
        return 0

    return status_line.split(" ")[1]


class Server:

    def __init__(self, host, port):
        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown) 

        # TCP socket for incoming connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set re-use socket
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to a host and a port
        self.server_socket.bind((host,port))
        
        # Now, listening for new connections  
        self.server_socket.listen(10)

    def listenForConn(self):

        while True:
            # Establish the connection
            (client_socket, client_addr) = self.server_socket.accept() 

            # Create new thread
            thread = threading.Thread(target=self.proxy, args=(client_socket, client_addr))
            thread.setDaemon(True)
            thread.start()
        self.shutdown()

    def proxy(self, conn, addr):
        
        # Get request from browser
        request = conn.recv(8192)
        #print(request.decode('utf-8'))

        # Parse the first line 
        line = request.decode('utf-8', 'ignore').split('\n')[0]
        # And get url 
        url = line.split(' ')[1]
        if not url:
            sys.exit(0)
        #print(url)

        # Parse url to get webserver and port
        (webserver, port) = parse_url(url)

        request = alter_request(request.decode('utf-8')).encode('utf-8')
        try:
            # Send recieved request to the server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(7)
            s.connect((webserver, port))
            s.sendall(request)

            # Now wait for response
            stop = False
            while not stop:
                # Recievig response
                response = s.recv(8192)

                # If there is response
                if response:
                    #print(response.decode('utf-8', 'ignore'))

                    # then parse responce to get code

                    code = getresponsecode(response)

                    if code:
                        print(f"Url: {url} Code: {code}")

                    # Send recieved responce to the client
                    conn.send(response)
                else:
                    stop = True

            # Close all resourses
            s.close()
            conn.close()        

        except socket.error as error_msg:
            # If any error occurred, print error message
            print("Error: ", addr, error_msg)
            
            # Close all resources
            if s:
                s.close()

            if conn:
                conn.close()

    def shutdown(self):
        self.server_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    print("The proxy-server is running.")

    server = Server("127.0.0.1", 12345)

    server.listenForConn()