# Yahoo Currency Scraper Server
A server that can receive and answer queries from multiple clients.
It returns live currency data from https://uk.finance.yahoo.com/currencies/.

## Usage:
### Setup
1. Clone the repo.
2. Create a new virtual environment with `python -m venv env`.
3. Activate it with `. ./env/bin/activate`.
4. Install dependencies with `pip install -r requirements.txt`.

### Starting the server
Open a new terminal and navigate to the working directory, then run `python -m yahoo_scraper`.
The server loop should start on Thread-1.

### Connecting a client
Open a new terminal and use `nc localhost 8080` to connect to the server.
There should be a success message followed by some instructions on how to disconnect.
If you then enter a valid request it will return the current exchange rate to 4 decimal places. If you requested an exchange rate that is not present on the page then it will return "FX rate unavailable for XXX:XXX" where XXX:XXX is your request.
Valid requests are in the form `XXX:XXX` and are case sensitive.

#### Example:
```bash
GBP:USD
1.3906
GBP:EUR
1.1480
```


## How it works:
### get_rate() function:
To implement this I made use of requests and bs4.
The inputs to the function have been validated so that they will always be of the form `XXX`.
We then make a get() request to the yahoo finance page (ensuring that we have a timeout set so the program won't hang indefinitely if it doesn't get a response). If the yahoo finance server returned a 200 code we can assume that we got the data that we need so we can proceed.
We create a BeautifulSoup object and then use the function inputs to match the correct row of the "Name" column in the table. With the correct row selected the helpful `.next_sibling` method allows us to move across 1 column to the "Last price" which we can return as text.

Cases where yahoo finance is not operating properly should print a warning and cause the function to return None. 
Cases where the user has requested a non-existant ticker (using a valid format) should return "0.0".

There were a few considerations when writing this function regarding how to get the data. The current method results in a delay of 1-2 seconds (on my internet anyway) as it fetches the data. I considered trying to scrape all the data from the table at regular intervals (every 2 seconds or so) but that is only beneficial if you plan on requesting multiple different exchange rates very quickly as it would prevent a new get() for each rate. Additionally, you would not be providing a current price any more so I decided that individual requests were more reliable.

### Handling multiple clients:
To handle requests from different clients in a timely manner I decided to opt for an asycnhronous multithreaded approach. 
The original server used the `socket` module but this approach quickly became unwieldy for what I was trying to achieve so I rewrote it to make use of the python `socketserver` module. This greatly simplified things as it meant that I only needed to write my own TCPRequestHandler class. This inherits from BaseRequestHandler and overrides the setup(), handle(), and finish() methods.

When the program is run from the command line a ThreadedTCPServer object making use of my request handler class is created and set to `.serve_forever` on Thread_1. The program then loops, waiting for a KeyboardInterrupt to shutdown the server.

Each new client that connects to the server fires the request handlers setup, handle, and finish methods in order. The setup method is just used to give the client some feedback that they have connected succesfully and usage instructions.
The handle method is where we handle client requests. When it receives an input it uses some regex to validate the request and if valid, passes the currencies to the get_rate function. The different possible return methods to the client are handled and the ability for the client to disconnect by entering 'q' or 'quit' is added.
The finish method just returns confirmation to the client that the connection is ended.

If the server is killed using a KeyboardInterrupt then it should kill all current threads since we set `daemon_threads` in the ThreadedTCPServer class. Additionally the `allow_reuse_address` flag is set to prevent an error when trying to restart the server after you have just shut it down. (It tells the kernel to reuse a local socket in the `TIME_WAIT` state without waiting for the timeout)