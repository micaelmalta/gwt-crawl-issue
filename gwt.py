#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from gdata import GDataEntryFromString
import urllib
from gdata.webmastertools.data import CrawlIssueEntry, CrawlIssuesFeed, \
    CrawlIssueUrl
from gdata.webmastertools import CrawlIssueFeedFromString
import math
import atom
from gdata.data import LinkFinder
import urllib2
from urllib2 import HTTPError, URLError
import socket
import re
import csv

"""Module for downloading CSV files from Google Webmaster Tools.

Module handles authentication with the Google servers by using the gdata
module provided by Google.  This script requires the gdata package be
installed in order to run.

  Downloader: Handles download implementation.
"""

import json
import gdata.webmastertools.service

class HeadRequest(urllib2.Request):
    def get_method(self):
        return 'HEAD'

def getheadersonly(url, redirections=True):
    opener = urllib2.OpenerDirector()
    opener.add_handler(urllib2.HTTPHandler())
    opener.add_handler(urllib2.HTTPDefaultErrorHandler())
    if redirections:
        # HTTPErrorProcessor makes HTTPRedirectHandler work
        opener.add_handler(urllib2.HTTPErrorProcessor())
        opener.add_handler(urllib2.HTTPRedirectHandler())
    try:
        res = opener.open(HeadRequest(url))
    except urllib2.HTTPError, res:
        pass
    res.close()
    return dict(code=res.code, headers=res.info(), finalurl=res.geturl())


class Gwt(object):
    """Handles client authentication and requests for Webmaster data.

    Contains the logic needed to authenticate with Google servers and
    download CSV files from Webmaster Tools.
    """
    HOST = 'www.google.com'
    APP_NAME = 'Google-WMTdownloadscript-0.1'
    LIST_PATH = '/webmasters/tools/downloads-list?hl=%s&siteUrl=%s'
    ISSUE_PATH = '/webmasters/tools/feeds/%s/crawlissues/?start-index=%s&max-results=%s'
    FILE_NAME_HEADER = 'content-disposition'
    TEXT_BEFORE_NAME = 'attachment; filename='
    MAX_PER_PAGE = 100
    CRAWL_ERRORS = {}
    URL_COUNTER = 0
    TOTAL_RESULTS = 0

    def __init__(self, site):
        self._client = gdata.webmastertools.service.GWebmasterToolsService()
        self._logged_in = False
        self._language = 'fr'
        self.site = site

    def IsLoggedIn(self):
        """Check if client has logged into their Google account yet."""
        return self._logged_in

    def LogIn(self, email, password, captcha_answer=None):
        """Attempts to log into the specified Google account.

        Args:
          email: User's Google email address.
          password: Password for Google account.
          captcha_answer: Optional answer to the captcha challenge.

        Raises:
          CaptchaRequired: If the login service requires a captcha response.
          BadAuthentication: If email/password is incorrect.
        """
        if self._client.captcha_token and captcha_answer:
            self._client.ClientLogin(email, password, source=self.APP_NAME,
                                   captcha_token=self._client.captcha_token,
                                   captcha_response=captcha_answer)
        else:
            self._client.ClientLogin(email, password, source=self.APP_NAME)

        self._logged_in = True

    def getCounter(self):
        return self.URL_COUNTER

    def getTotalResults(self):
        return self.TOTAL_RESULTS

    def GetCrawlIssues(self):
        self.csv = csv.writer(open("crawl-1.csv", "wb"))
        self.csv.writerow(["URI", "DETAIL", "ISSUE TYPE", "DATE"])

        if not self.IsLoggedIn():
            raise ValueError('Client not logged in.')

        self._GetCrawlIssues()

    def _GetCrawlFeed(self, page=1):
        uri = self._GetFullUrl(self.ISSUE_PATH % (urllib.quote_plus(self.site), int(page), self.MAX_PER_PAGE))
        try:
            feed = self._client.GetFeed(uri, converter=CrawlIssueFeedFromString)
            return feed
        except RequestError:
            return None

    def _GetCrawlIssues(self):
        feed = self._GetCrawlFeed()
        if not feed:
            return

        total_results = int(feed.total_results.text)

        self.TOTAL_RESULTS = total_results
        print "Il y a %d resultats" % total_results
        self._GetEntries(feed.entry)

        nb_page = int(math.ceil(total_results / self.MAX_PER_PAGE))

        for x in xrange(2, nb_page):
            startIndex = self.MAX_PER_PAGE * (x - 1) + 1;

            result = self._GetCrawlFeed(startIndex)
            if result:
                self._GetEntries(result.entry)


    def _GetEntries(self, entries):

        for entry in entries:
            self.csv.writerow([entry.url.text, entry.detail.text, entry.issuetype.text, entry.datedetected.text])
            if self._exluded_entry(entry):
#                print "Exclude %s : %s - %s" % (entry.url.text,
#                                         entry.detail.text,
#                                         entry.issuetype.text)
                continue

            self.CrawlUri(entry.url.text)

    def _exluded_entry(self, entry):
        """ Exclude some patern """
        return re.search('robots.txt', entry.detail.text)

    def CrawlUri(self, uri):
        """
        Check if uri response is valid

        Mark as solved if valid
        """
        req = getheadersonly(uri)
        http_code = req['code']
        if http_code in [200, 301, 302, 304, 410]:
            self.mark_as_resolved(uri)
            return True
        else:
            if http_code not in self.CRAWL_ERRORS:
                self.CRAWL_ERRORS[http_code] = []
            self.CRAWL_ERRORS[http_code].append(uri)
            return False


    def SetLanguage(self, language_code):
        self._language = language_code

    def _GetFullUrl(self, path):
        """Construct an absolute URL using path segment.

        Args:
          path: The path segment of a URL.

        Returns:
          A URL giving the absolute path to a resource.
        """
        return 'https://' + self.HOST + path

    def GetResult(self, data):
        return data

    def mark_as_resolved(self, uri):
        uri = uri.replace(self.site, '')
        print "RESOLVE %s" % uri
        self.URL_COUNTER += 1

        payload = '7|0|19|https://www.google.com/webmasters/tools/gwt/|E0A63C90F20A97A3B90B99019E19DC12|com.google.crawl.wmconsole.fe.feature.gwt.crawlerrors.shared.CrawlErrorsActionService|markUrlsAsFixed|com.google.crawl.wmconsole.fe.feature.gwt.base.shared.FeatureContext/1637625730|java.util.List|/webmasters/tools|java.lang.Boolean/476441737|com.google.crawl.wmconsole.fe.feature.gwt.config.FeatureKey/4151209095|0|fr|%s|com.google.crawl.wmconsole.fe.base.PermissionLevel/2603202488|java.util.LinkedList/3953877921|com.google.crawl.wmconsole.fe.feature.gwt.crawlerrors.shared.UrlErrorSummaryShared/3005870204|java.lang.Integer/3438268394|java.lang.Long/4227064769|11/10/13|%s|1|2|3|4|2|5|6|5|7|8|0|0|9|1|10|11|12|12|13|5|14|1|15|16|1|17|E4cn2BF3A|17|E4cn2BF3A|18|16|878|16|410|17|3T|19|-7|' % (self.site, uri)

        #payload = json.dumps(payload)

        headers = {
            'x-gwt-module-base': 'https://www.google.com/webmasters/tools/gwt/',
            'x-gwt-permutation': '2F81ADD09C4710CEB4FE78DA35FDC1A8',
            'Content-Type': 'text/x-gwt-rpc',
        }


        res_stream = self._client.Post(
            payload,
            self._GetFullUrl('/webmasters/tools/gwt/CRAWLERRORS_EDIT?hl=fr&siteUrl=%s' % self.site),
            extra_headers=headers,
            converter=self.GetResult,
        )

        #print res_stream
