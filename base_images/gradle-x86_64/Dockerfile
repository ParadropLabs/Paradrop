FROM gradle:4.2-jdk8-alpine

ADD init-app.sh /usr/local/bin/

# Set up an unprivileged user so that we can drop out of root.
# Make /opt/paradrop/app for installing the app files.
USER root
RUN adduser -S -u 999 paradrop && \
    mkdir -p /home/paradrop && \
    chown paradrop /home/paradrop && \
    mkdir -p /opt/paradrop/app && \
    chown -R paradrop /opt/paradrop && \
    chmod a+s /opt/paradrop

# setcap is not present in this image. This may cause problems
# if the chute tries to bind to ports 1-1024.
#
#    setcap 'cap_net_bind_service=+ep' /usr/bin/java

# Defang setuid/setgid binaries.
RUN find / -perm +6000 -type f -exec chmod a-s {} \; || true

WORKDIR /opt/paradrop/app

ONBUILD COPY . /opt/paradrop/app/
ONBUILD RUN chown -R paradrop /opt/paradrop

ONBUILD USER paradrop
ONBUILD RUN /usr/local/bin/init-app.sh
