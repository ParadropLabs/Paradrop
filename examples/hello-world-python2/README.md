Hello world chute written with Python v2
===================================================
This simple chute demonstrate the basic structure required to build a chute with Python


Building
--------

On host
```
docker build -f development/Dockerfile -t paradrop/hello-world-python2 .
docker run -t -i -p 8080:80 -v $PWD:/opt/paradrop paradrop/hello-world-python2 /bin/bash
```

In the container, install the pip and test it.
```
cd /opt/paradrop/development
pip install --editable .
```

Deployment
-----------
On host
```
./install.sh
cd deployment
pdtools device --address=<router_ip> chutes install
```
