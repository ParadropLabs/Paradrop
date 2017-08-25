Hello world chute written with node.js
===================================================
This simple chute demonstrate the basic structure required to build a chute with node.js.


Building
--------

On host
```
docker build -f development/Dockerfile -t paradrop/hello-world-node .
docker run -t -i -p 8080:80 -v $PWD:/opt/paradrop paradrop/hello-world-node /bin/bash
```

In the container
```
cd /opt/paradrop/development
npm install
npm start
```

Deployment
-----------
On host
```
./install.sh
cd deployment
pdtools device --address=<router_ip> chutes install
```
