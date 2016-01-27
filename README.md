# UZB-78 Perimetr 
##dead man switch protocol implementation

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
`cron(8)`. No dependencies except Python with standard library.
Before you deploy, customize the following settings:

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
