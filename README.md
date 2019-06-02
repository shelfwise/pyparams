<img src="resources/img/header.png" width="800">

# pyparams
Library for python file parametrization.


# Simple python example:

* Define parametrized file by annotating selected parameters with `PyParam`

* A content of `client.py` file
```python
from pyparams import *

address: str = PyParam("", scope="url")
port: int = PyParam(10000, scope="url")

client = SomeClient(address, port)
# some code here ...
client.do_something()
```

* Parse file to create `config.yml`:
```bash
pyparams path/to/client.py
cat config.yml
url:
    address:
        dtype: str
        value: ''
    port:
        dtype: int
        value: 10000
```

* Set config and create compiled version of the `client.py` code.
```bash
pyparams path/to/client.py -o compiled_client.py
```
this will create `compiled_client.py` file:
```python
from pyparams import Module
from pyparams import *
address: str = ''
port: int = 10000
client = SomeClient(address, port)
client.do_something()
...
```

