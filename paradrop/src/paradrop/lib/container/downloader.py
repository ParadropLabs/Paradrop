"""
This module downloads a package from a given URL using one of potentially
many different methods.  We currently support the github web API and
simple HTTP(S).  The github method is more developed and returns meta data
about the project (the commit hash and message), but support for other
methods, e.g. download a tar file that was uploaded to a web server,
are not precluded.

Private downloads are supported with the HTTP Authorization header.
For github, we need to use the github API to request a token to access
the owner's private repository.  That part is not implemented here.
"""

import base64
import cStringIO
import json
import os
import re
import shutil
import tarfile
import tempfile

import pycurl


github_re = re.compile("(http|https)://github.com/([\w\-]+)/([\w\-]+)(\.git)?")
general_url_re = re.compile("(http:\/\/|https:\/\/)(\S+)")
hash_re = re.compile("^.*-([0-9a-f]+)$")


class Downloader(object):
    def __init__(self, url, user=None, secret=None, repo_owner=None, repo_name=None):
        self.url = url
        self.user = user
        self.secret = secret
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.checkout = None

        self.commitHash = None
        self.commitMessage = None

        self.workDir = None

    def __enter__(self):
        self.workDir = tempfile.mkdtemp()
        return self

    def __exit__(self, type, value, traceback):
        if self.workDir is not None:
            shutil.rmtree(self.workDir)
            self.workDir = None

    def download(self):
        raise NotImplementedError

    def meta(self):
        raise NotImplementedError

    def fetch(self):
        """
        Download the project.

        Returns the full path to the temporary directory containing the project
        and a dictionary containing meta data.
        """
        runDir = self.download()
        meta = self.meta()
        return runDir, meta

    def extract(self):
        tar = tarfile.open(self.tarFile)

        # Look for a Dockerfile and also check for dangerous paths (.. or /).
        runPath = None
        for member in tar:
            path = member.name
            if path.startswith(".."):
                raise Exception("Archive contains a forbidden path: {}".format(path))
            elif path.startswith("/"):
                raise Exception("Archive contains an absolute path: {}".format(path))
            elif path.endswith("Dockerfile"):
                runPath = path
            elif self.commitHash is None:
                match = hash_re.match(path)
                if match is not None:
                    self.commitHash = match.group(1)

        tar.extractall(path=self.workDir)

        if runPath is None:
            raise Exception("Repository does not contain a Dockerfile")

        relRunDir = os.path.dirname(runPath)
        runDir = os.path.join(self.workDir, relRunDir)
        return runDir


class GithubDownloader(Downloader):
    def __init__(self, url, checkout="master", **kwargs):
        """
        checkout: branch, tag, or commit hash to checkout (default: "master").
        """
        super(GithubDownloader, self).__init__(url, **kwargs)

        if checkout:
            self.checkout = checkout
        else:
            # Interpret None or empty string as the default, "master".
            self.checkout = "master"

    def _create_curl_conn(self, url):
        """
        Create a cURL connection object with useful default settings.
        """
        headers = []
        if self.user is not None and self.secret is not None:
            b64cred = base64.b64encode("{}:{}".format(self.user, self.secret))
            headers.append("Authorization: Basic {}".format(b64cred))

        conn = pycurl.Curl()

        if len(headers) > 0:
            conn.setopt(pycurl.HTTPHEADER, headers)

        conn.setopt(pycurl.URL, url)

        # github often redirects
        conn.setopt(pycurl.FOLLOWLOCATION, 1)

        return conn

    def download(self):
        url = "https://github.com/{}/{}/tarball/{}".format(
                self.repo_owner, self.repo_name, self.checkout)
        conn = self._create_curl_conn(url)

        self.tarFile = os.path.join(self.workDir, "source.tar.gz")
        with open(self.tarFile, "w") as output:
            conn.setopt(pycurl.WRITEFUNCTION, output.write)
            conn.perform()

        http_code = conn.getinfo(pycurl.HTTP_CODE)
        if http_code != 200:
            raise Exception("Error downloading archive: response {}".format(http_code))

        return self.extract()

    def meta(self):
        """
        Return repository meta data as a dictionary.
        """
        result = {}

        if self.commitHash is not None:
            result['CommitHash'] = self.commitHash
        if self.commitMessage is not None:
            result['CommitMessage'] = self.commitMessage

        # If set, self.commitHash may be more specific than self.checkout (e.g.
        # commit hash vs. branch name).  It is better to use the most specific
        # one to query for meta data.
        checkout = self.commitHash
        if checkout is None:
            checkout = self.checkout

        url = "https://api.github.com/repos/{owner}/{repo}/commits/{sha}".format(
                owner=self.repo_owner, repo=self.repo_name, sha=checkout)
        conn = self._create_curl_conn(url)

        response = cStringIO.StringIO()
        conn.setopt(pycurl.WRITEFUNCTION, response.write)
        conn.perform()

        http_code = conn.getinfo(pycurl.HTTP_CODE)
        if http_code == 200:
            data = json.loads(response.getvalue())
            result['Commit'] = data['commit']
            result['CommitMessage'] = data['commit']['message']

        return result


class WebDownloader(Downloader):
    def _create_curl_conn(self, url):
        """
        Create a cURL connection object with useful default settings.
        """
        headers = []
        if self.user is not None and self.secret is not None:
            b64cred = base64.b64encode("{}:{}".format(self.user, self.secret))
            headers.append("Authorization: Basic {}".format(b64cred))

        conn = pycurl.Curl()

        if len(headers) > 0:
            conn.setopt(pycurl.HTTPHEADER, headers)

        conn.setopt(pycurl.URL, url)

        # github often redirects
        conn.setopt(pycurl.FOLLOWLOCATION, 1)

        return conn

    def download(self):
        conn = self._create_curl_conn(self.url)

        self.tarFile = os.path.join(self.workDir, "source.tar")
        with open(self.tarFile, "w") as output:
            conn.setopt(pycurl.WRITEFUNCTION, output.write)
            conn.perform()

        http_code = conn.getinfo(pycurl.HTTP_CODE)
        if http_code != 200:
            raise Exception("Error downloading archive: response {}".format(http_code))

        return self.extract()

    def meta(self):
        """
        Return repository meta data as a dictionary.
        """
        result = {}

        return result


def downloader(url, user=None, secret=None, **kwargs):
    """
    Return an appropriate Downloader for the given URL.

    This should be used in a "with ... as ..." statement to perform cleanup on
    all exit cases.

    Example:
    with downloader("https://github.com/...") as dl:
        path, meta = dl.fetch()
        # do some work on the repo here
    """
    # If the URL looks like a github.com reop, then use github-specific
    # download method.  Otherwise, use basic web download method.
    match = github_re.match(url)
    if match is not None:
        if user is None:
            user = match.group(2)
        repo_owner = match.group(2)
        repo_name = match.group(3)
        return GithubDownloader(url, user=user, secret=secret,
                repo_owner=repo_owner, repo_name=repo_name, **kwargs)

    else:
        return WebDownloader(url, user=user, secret=secret, **kwargs)
