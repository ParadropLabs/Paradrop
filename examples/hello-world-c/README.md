Hello world chute written with C language
===================================================
This simple chute demonstrate the basic structure required to build a chute with a programming language that compiling is required.


Building
--------

On host
```
docker build -f development/Dockerfile -t paradrop/hello-world-c .
docker run -t -i -p 8080:80 -v $PWD:/opt/paradrop paradrop/hello-world-c /bin/bash
```

In the container
```
cd /opt/paradrop/development
make
```

Then test the binary to make sure it works

Deployment
-----------
On host
```
cd deployment
pdtools device --address=<router_ip> chutes install
```
