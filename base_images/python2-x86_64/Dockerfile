FROM python:2.7

ADD init-app.sh /usr/local/bin/

# Install some useful tools and libraries.
RUN apt-get update && \
    apt-get install -y \
        iptables

# Set up an unprivileged user so that we can drop out of root.
# Make /home/paradrop so that pip can drop some files in there.
# Make /opt/paradrop/app for installing the app files.
# Add cap_net_bind_service to python so that it can bind to ports 1-1024.
RUN useradd --system --uid 999 paradrop && \
    mkdir -p /home/paradrop && \
    chown paradrop /home/paradrop && \
    mkdir -p /opt/paradrop/app && \
    chown paradrop /opt/paradrop/app && \
    chmod a+s /opt/paradrop/app && \
    setcap 'cap_net_bind_service=+ep' /usr/local/bin/python2.7

# Defang setuid/setgid binaries.
RUN find / -perm +6000 -type f -exec chmod a-s {} \; || true

WORKDIR /opt/paradrop/app

# Copy paradrop.yaml and requirements.txt, the latter only if it exists.  Then
# call init-app.sh to install dependencies. These layers will be cached as long
# as the requirements do not change.
ONBUILD COPY paradrop.yaml requirements.tx[t] /opt/paradrop/app/
ONBUILD RUN init-app.sh

# Now copy the rest of the files.
ONBUILD COPY . /opt/paradrop/app/
ONBUILD RUN chown paradrop:paradrop -R /opt/paradrop/app

ONBUILD USER paradrop
