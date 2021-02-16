import threading
import socketserver
from re import fullmatch

import requests
from bs4 import BeautifulSoup

from yahoo_scraper.utils import measure_perf, send_string

HOST = "localhost"
PORT = 8080


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def setup(self):
        send_string(self.request,
                    "Connected!\nEnter 'q' to disconnect.\n")

    def handle(self):
        while True:
            data = self.request.recv(4096).decode().strip()

            # # Debug information for verifying threads.
            # cur_thread = threading.current_thread()
            # send_string(self.request, f"{cur_thread.name} was sent {data}")

            # Validating input values in the form XXX:XXX (case sensitive)
            if fullmatch(r'^[A-Z]{3}:[A-Z]{3}$', data):
                fromCcy, toCcy = data.split(':')
                fx_rate = get_rate(fromCcy, toCcy)
                if fx_rate == '0.0':
                    message = f"FX rate unavailable for {fromCcy}:{toCcy}"
                elif fx_rate is not None:
                    message = fx_rate
                else:
                    message = "Unable to connect to Yahoo Finance"
                send_string(self.request, message)

            elif data == 'q' or data == 'quit':
                send_string(self.request, "Disconnecting...")
                break

            else:
                send_string(self.request, "Invalid request")

    def finish(self):
        send_string(self.request, "Disconnected")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


@measure_perf
def get_rate(fromCcy, toCcy):
    """Return current exchange rate from Yahoo Finance."""

    r = requests.get('https://uk.finance.yahoo.com/currencies/', timeout=5)

    if r.status_code == requests.codes.ok:
        soup = BeautifulSoup(r.content, features='html.parser')
        found = soup.find("td", string=f"{fromCcy}/{toCcy}")
        if found:
            return found.next_sibling.text

    else:
        print("Error connecting to Yahoo Finance")
        return None

    # Unable to find requested rate
    return "0.0"


def main():
    with ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler) as server:
        try:
            server_thread = threading.Thread(target=server.serve_forever)
            # Exit the server thread when the main thread terminates
            server_thread.daemon = True
            print("Starting Server...")
            server_thread.start()
            print("Server loop running in thread:", server_thread.name)

            while True:
                pass

        except KeyboardInterrupt:
            print("\nRequested Shutdown")

        finally:
            print("Shutting down server")
            server.shutdown()


if __name__ == "__main__":
    main()
