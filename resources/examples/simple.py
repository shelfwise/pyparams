from pyparams import *

address: str = PyParam("", scope="url")
port: int = PyParam(10000, scope="url")

client = SomeClient(address, port)
# some code here ...
client.do_something()

