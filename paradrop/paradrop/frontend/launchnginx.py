import dockerapi
"""
This is simply an example call showing how one might use the dockerapi.launchApp function

Use this url as location of Dockerfile and src and extract zip to working dir.

https://github.com/nphyatt/docker-test/archive/master.zip

"""

cId = dockerapi.launchApp(path='/home/owner/paradrop/docker-test/', name='nick/test', restart_policy={"MaximumRetryCount": 0, "Name": "always"}, port_bindings={ 80: 9000 })
