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

"""Example script for how to download a CSV file and upload it to Google docs.  

Download a Top Search Queries CSV file and then upload the file to Google docs
as a spreadheet.  The email, password, and website values used here must be
replaced with real values.  See wiki document on its use.
"""

# Import the downloader
from gwt import Gwt
# Import gdata objects for uploading files to Google Docs
import gdata.docs
import gdata.docs.service
import sys

# Email address and password used to sign-in to Webmaster Tools and Google Docs
email = 'xxx'
password = 'xxx'
# Specify the website and the type of data to download
website = sys.argv[1]

# Instantiate the downloader object
gwt = Gwt(website)

# Authenticate with your Webmaster Tools sign-in info
gwt.LogIn(email, password)

# Initiate the Crawl
gwt.GetCrawlIssues()

counter = gwt.getCounter()
total = gwt.getTotalResults()
print "%d URL ont ete marque comme corrige sur %d" % (counter, total)

#gwt.CrawlUri('http://pro.01net.com/jeux-video/jeux-gratuits-en-ligne/aventure/104913/steppenwolf-44/screenshot/')
