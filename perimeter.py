#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''UZB-78 Perimetr  --- dead man switch protocol implementation.

### Basics

In the current form, the program checks a trigger (file or URL) and if
the trigger hasn't been touched for a specified time, sends out a
e-mail message. The same happens of the remote trigger is unavaliable
for a specified amount of time. If the trigger is activated, the script
replaces itself with a empty no-op one or tries to remove itself if the
replacement is impossible.

### Features

 * local or remote trigger 
 * separate time threshold for remote trigger being unavaliable
 * auto-erases itself after the triggering
 * utf-8 support for messages

### Triggers

For a local trigger, `touch(1)` something in your `.bashrc`.

For a remote trigger, to use with perimeter deployed on another host,
link it somewhere under /var/www so it can be accessed over HTTP.

I'm in the process of creating a web service for remote triggers to be
updated from desktop machines. It will be avaliable Real Soon Now.

### Deployment 

It should be deployed on a Linux/Unix system, probably using
`cron(8)`. Before you do that, customize the following settings:

 * `RECIPIENTS` -- a tuple of recipient email addresses

 * `SMTP_HOST` -- SMTP relay name; no auth supported so it has to accept
                  mail from the host you will be sending from

 * `MAIL_FROM` -- sender email address

 * `SUBJECT` and `MESSAGE` -- subject and body of the email message to be
                              sent. Both will be properly encoded from UTF.

 * `THRESHOLD` -- (in seconds) how long the trigger has to be untouched
                  for the program to act

 * `CONNECT` -- (in seconds) how long the remote trigger has to be
                unaccessible for the program to act

 * `TEST_PATH` -- path for the local filesystem trigger. Default is `~/.login_timestamp`

 * `TEST_URL` -- domain name of the remote trigger

 * `TEST_URL_PATH` -- URL path of the remote trigger

For the remote trigger URL being `http://example.com/remote/trigger`,
the values would be:

```
TEST_URL = 'example.com'
TEST_PATH = '/remote/trigger'
```

Only HTTP is supported as of now. The parameters are split due to how
httplib HEAD queries work.

You may also want to change:

 * `STATE` -- path to Perimetr's internal state file used with remote trigger

`OVERLAY` is an empty python file that is written over the script file after 
triggering, so the cron won't send out missing file emails and bring attention
to the script. In case of overwriting being impossible, the script tries to 
remove itself.

### Usage

`perimeter.py -r`

checks for remote trigger

`perimeter.py`

checks for local trigger

### Licence

    UZB-78 Perimetr --- dead man switch protocol implementation.

    Copyright (C) 2016 Ph10x

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

__version__ = '2.0'

import os, sys, time, smtplib, httplib, socket

from getopt import GetoptError, gnu_getopt as go
from email.MIMEText import MIMEText
from email.Header import Header
from time import gmtime, strftime
from email.Header import Header

#### CONFIGURATION SECTION

RECIPIENTS = ('recipient@example.com',)
SMTP_HOST = 'localhost'
MAIL_FROM = 'daemon@localhost'
TEST_PATH = os.path.join(os.path.expandvars('$HOME'), '.login_timestamp')
TEST_URL = 'example.com'
TEST_URL_PATH = '/timestamp'

# 432000 - 5 days

THRESHOLD = int (432000)
CONNECT = int (432000)
SUBJECT = u'Bavarian fire drill!'
MESSAGE = u'''This is a test message. This is a drill. There's no need to be alarmed.
Please disregard.
'''

#### END OF CONFIGURATION SECTION

# DO NOT TOUCH ANYTHING BELOW THIS LINE!

STATE = '/var/tmp/.perimeterd.state'
OVERLAY = '''#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Perimeter response deployed.

pass
'''

####

def sendmail(recipient, remote=False):

  if __debug__:
    print 'Payload deploy initiated.'

  message = MIMEText(MESSAGE,'plain', 'UTF-8')
  message['From'] = 'UVB-76 <%s>' % MAIL_FROM
  message['To'] = recipient
  message['Priority'] = 'urgent'
  message['X-Mailer'] = 'Perimetr %s' % __version__
  message['Message-ID'] = '<%s-perimeter@UVB-76>' % strftime("%S%M%H%d%m%Y", gmtime())
  message['Date'] = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
  message['Subject'] = Header(SUBJECT, 'utf-8')
        
  if False:
    pass # testing stub, please disregard
  else:
    smtp = smtplib.SMTP(host=SMTP_HOST)
    smtp.connect()
    smtp.sendmail(MAIL_FROM, recipient, message.as_string())
    smtp.close()

def remote():
  'remote trigger testing'

  def read_state():
    result = (-1, -1)
    if os.path.exists(STATE):
      try:
        state = file(STATE,'r').read()
        if ':' in state:
          try:
            result = [ int(i) for i in state.split(':') ]
          except ValueError:
            pass
      except:
        pass
        
    return result
        
  def write_state(connect, seen):
    result = file(STATE,'w').write('%s:%s' % (int(connect), int(seen)))
  
  now = time.time()  
  connect, seen = read_state()  

  try:
    connection = httplib.HTTPConnection(TEST_URL)
    connection.request('HEAD', TEST_URL_PATH)
    response = connection.getresponse()

  except socket.error as error:
    then = -1
    if __debug__:
      print '*** ERROR: HTTP Connection lost:', error    

  else:
    if __debug__:
      print 'HTTP Connection established.'
    then = seen
    if response.status == 200:
      # checking remote timestamp date
      headers = response.getheaders()
      date = [ item for item in headers if item[0] == 'last-modified' ][0]
      if len(date):
        then = int(time.mktime(time.strptime(date[1], "%a, %d %b %Y %H:%M:%S %Z")))

  finally:
    connection.close()

  if seen > 0:
    if now-then > THRESHOLD:
      launch(True)
      return True
    else: 
      write_state(now, then)      

  elif connect > 0:
    if now-connect > CONNECT:
      launch(True)
      return True

  write_state(now, now)  

def local():
  'local trigger testing'

  now = time.time()
  last = os.stat(TEST_PATH)[7]

  if int(now-last) > THRESHOLD:
    launch()
    return True

def launch():
  'payload launch - sending the message'

  for recipient in RECIPIENTS:
    sendmail(recipient)

if __name__ == '__main__': 

  # command line parsing
  try:
    if 'r' in [ o[0].strip('-') 
                for o in go(sys.argv[1:], 'r', ['remote'])[0] if len(o) ]:
      result = remote()
    else:
      result = local()
  except GetoptError:
    result = local()

  if result:
    try:
      file(os.path.abspath(__file__), 'wb').write(OVERLAY) 
    except IOError:
      os.remove(os.path.abspath(__file__))
    # this should never happen
    if __debug__:
      print 'The time is now. Done. Simply done. Not much to say afterwards.'

### The world ends here.
