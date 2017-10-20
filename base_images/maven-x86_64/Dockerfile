FROM maven:3.5-jdk-8-alpine

# The default directory (/root/.m2) is not writable by paradrop user.
ENV MAVEN_CONFIG /opt/paradrop/.m2

# Make maven output a little less verbose.
ENV MAVEN_OPTS "-Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer.Slf4jMavenTransferListener=warn"

ADD init-app.sh /usr/local/bin/

# Set up an unprivileged user so that we can drop out of root.
# Make /opt/paradrop/app for installing the app files.
RUN adduser -S -u 999 paradrop && \
    mkdir -p /home/paradrop && \
    chown paradrop /home/paradrop && \
    mkdir -p /opt/paradrop/app && \
    mkdir -p /opt/paradrop/.m2 && \
    chown -R paradrop /opt/paradrop && \
    chmod a+s /opt/paradrop

# setcap is not present in this image. This may cause problems
# if the chute tries to bind to ports 1-1024.
#
#    setcap 'cap_net_bind_service=+ep' /usr/bin/java

# Defang setuid/setgid binaries.
RUN find / -perm +6000 -type f -exec chmod a-s {} \; || true

WORKDIR /opt/paradrop/app

# Copy paradrop.yaml and pom.xml, the latter only if it exists. Then
# call init-app.sh to install dependencies. These layers will be cached as long
# as the requirements do not change.
ONBUILD COPY paradrop.yaml pom.xm[l] /opt/paradrop/app/
ONBUILD RUN init-app.sh

# Now copy the rest of the files and build.
ONBUILD COPY . /opt/paradrop/app/
ONBUILD RUN mvn --batch-mode package
ONBUILD RUN chown paradrop -R /opt/paradrop

ONBUILD USER paradrop
