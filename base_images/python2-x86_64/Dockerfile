FROM python:2.7

ADD init-app.sh /usr/local/bin/

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

ONBUILD COPY . /opt/paradrop/app/
ONBUILD RUN chown paradrop:paradrop -R /opt/paradrop/app

# Run init-app.sh as root to install python packages.
ONBUILD RUN init-app.sh
ONBUILD USER paradrop
