This python api enables easy interaction with the Etherpad Lite API.
Etherpad Lite is a collaborative editor provided by the Etherpad Foundation.
http://etherpad.org

#1 Disclaimer

This is just a Proof of Concept of a CLI tracking of etherpadlite.

## API mode

The API mode `-A` will work only with the etherpad-lite fork over here: 

    [https://github.com/guyzmo/etherpad-lite](https://github.com/guyzmo/etherpad-lite)

I have extended the API of etherpad in order to be able to have more
informations from the server, so it can display a local copy of the text
in the terminal, updated in real time

## Socket.io mode

In order for the socket.io mode to work, you need to add `websocket` in
settings.json configuration file for Etherpad-Lite, as follows:

    "socketTransportProtocols" : ["xhr-polling", "jsonp-polling", "htmlfile", "websocket"],

#2 Install or develop


to install:

    python setup.py install

to build:

    pip install zc.buildout
    buildout

#3 Run

* gives the help screen

    ```bin/pyepad --help```

* to connect to beta.etherpad.org:

    ```bin/pyepad test -H beta.etherpad.org```

* to connect to a local instance

    ```bin/pyepad mypad -H localhost -P 9001```

* to connect using API

    ```bin/pyepad mypad -A -k `cat /path/to/etherpad-lite/APIKEY.txt` -H localhost -P 9001```

#3 License

Apache License

#4 Credit

Thanks to devjones, from who I have forked the project
This python client was inspired by TomNomNom's php client which can be found at: https://github.com/TomNomNom/etherpad-lite-client
