"""
This module is responsible for configuration haproxy.
"""
import os
import subprocess

from paradrop.base import settings
from paradrop.core.chute.chute_storage import ChuteStorage
from paradrop.core.container.chutecontainer import ChuteContainer


def generateConfigSections():
    sections = []

    sections.append({
        "header": "global",
        "lines": [
            "daemon",
            "maxconn 256",
        ]
    })

    sections.append({
        "header": "defaults",
        "lines": [
            "mode http",
            "timeout connect 5000ms",
            "timeout client 50000ms",
            "timeout server 50000ms"
        ]
    })

    sections.append({
        "header": "backend portal",
        "lines": [
            "server pd_portal 127.0.0.1:8080 maxconn 256"
        ]
    })

    # Custom variables:
    # - req.querymarker: will be set to the literal "?" if the original request
    # contains a query string.  We will use this to construct a redirect with a
    # query string only if needed.
    # - req.subpath: will be set to the remainder of the path, if anything,
    # after removing /chutes/<chutename>, e.g. "/chutes/hello-world/index.html"
    # becomes "/index.html".  This does not include the query string.
    frontend = {
        "header": "frontend http-in",
        "lines": [
            "bind *:80",
            "default_backend portal",
            "http-request set-var(req.querymarker) str(?) if { query -m found }",
            "http-request set-var(req.subpath) path,regsub(^/chutes/[^/]+,)"
        ]
    }
    sections.append(frontend)

    chuteStore = ChuteStorage()
    chutes = chuteStore.getChuteList()
    for chute in chutes:
        port, service = chute.get_web_port_and_service()
        if port is None or service is None:
            continue

        container = ChuteContainer(service.get_container_name())
        if not container.isRunning():
            continue

        # Generate a rule that matches HTTP host header to chute name.
        frontend['lines'].append("acl host_{} hdr(host) -i {}.chute.paradrop.org".format(
            chute.name, chute.name))
        frontend['lines'].append("use_backend {} if host_{}".format(
            chute.name, chute.name))

        # Generate rules that matches the beginning of the URL.
        # We need to be careful and either have an exact match
        # or make sure there is a slash or question mark after the chute name
        # to avoid mix-ups, e.g. "sticky-board" and "sticky-board-new".
        frontend['lines'].append("acl path_{} url /chutes/{}".format(
            chute.name, chute.name))
        frontend['lines'].append("acl path_{} url_beg /chutes/{}/".format(
            chute.name, chute.name))
        frontend['lines'].append("acl path_{} url_beg /chutes/{}?".format(
            chute.name, chute.name))

        # Try to find a host binding for the web port to redirect:
        # http://<host addr>/chutes/<chute>/<path> ->
        # http://<host addr>:<chute port>/<path>
        #
        # We need to do a lookup because the host port might be dynamically
        # assigned by Docker.
        #
        # Use HTTP code 302 for the redirect, which will not be cached by the
        # web browser.  The port portion of the URL can change whenever the
        # chute restarts, so we don't want web browsers to cache it.  Browsers
        # will cache a 301 (Moved Permanently) response.
        portconf = container.getPortConfiguration(port, "tcp")
        if len(portconf) > 0:
            # TODO: Are there other elements in the list?
            binding = portconf[0]
            frontend['lines'].append("http-request replace-value Host (.*):(.*) \\1")
            frontend['lines'].append("http-request redirect location http://%[req.hdr(host)]:{}%[var(req.subpath)]%[var(req.querymarker)]%[query] code 302 if path_{}".format(
                binding['HostPort'], chute.name))

        # Add a server at the chute's IP address.
        sections.append({
            "header": "backend {}".format(chute.name),
            "lines": [
                "server {} {}:{} maxconn 256".format(chute.name,
                    container.getIP(), port)
            ]
        })

    return sections


def writeConfigFile(output):
    sections = generateConfigSections()
    for section in sections:
        output.write(section['header'] + "\n")
        for line in section['lines']:
            output.write("    " + line + "\n")
        output.write("\n")


def reconfigureProxy(update):
    """
    Reconfigure haproxy with forwarding and redirect rules.
    """
    confFile = os.path.join(settings.RUNTIME_HOME_DIR, "haproxy.conf")
    pidFile = os.path.join(settings.TMP_DIR, "haproxy.pid")

    with open(confFile, "w") as output:
        writeConfigFile(output)

    cmd = ["haproxy", "-f", confFile, "-p", pidFile]

    if os.path.exists(pidFile):
        with open(pidFile, "r") as source:
            pid = source.read().strip()
            cmd.extend(["-sf", pid])

    subprocess.call(cmd)
