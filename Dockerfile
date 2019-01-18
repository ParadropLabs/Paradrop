#
# Build Stage
#
FROM python:2.7-alpine as build

# Install requirements for building dependencies.  This is mainly for compiled
# C code required by some of the Python packages.
RUN apk add --no-cache curl-dev gcc libffi-dev linux-headers musl-dev

WORKDIR /usr/src/paradrop
COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt
COPY . .
RUN pip install /usr/src/paradrop/paradrop/daemon

#
# Run Stage
#
FROM python:2.7-alpine

# Install runtime dependencies. These include commands that Paradrop uses such
# as iptables as well as shared libraries.
RUN apk --no-cache add ca-certificates dnsmasq haproxy hostapd iptables ip6tables libcurl pulseaudio-dev

# Copy all of the Python packages that were installed in the build stage.
COPY --from=build /usr/local/lib/python2.7/site-packages /usr/local/lib/python2.7/site-packages

# Copy the static files for the admin panel because the Python package does not
# install them.
COPY --from=build /usr/src/paradrop/paradrop/localweb/www /usr/local/lib/python2.7/site-packages/paradrop/static

EXPOSE 80
CMD [ "python", "-m", "paradrop.main" ]
