# PySMTP - SMTP Cient written in Python 3.4
<dl>
<b>usage: pysmtp.py [-h] [-nl] host </b>
<dt />host<dd />The host name of the SMTP server to which you are connecting
<dt />-nl, --not-login<dd />Disable authorization
<dt />-h, --help<dd />show help message
</dl>
<h3>Info:</h3>
+ Have the ability to work through the SSL connection
+ Mass mailing
+ The ability to attach files of various formats
+ It is possible to attach all the files within the specified folder (just enter the path to it)
+ [v1.2] The ability to disable authorization
+ [v1.3] Random generation of boundaries
+ [v1.4] New interface + Russian localization
+ [v1.5] Use ESMTP
+ [v1.6] The ability to specify the name of the sender

<h3>Manual:</h3>
<pre>
<b>From:</b> [name] email
<b>Password:</b> password      # not used with flag -hl
<b>To:</b> email               # separated with a space
<b>Subject:</b> subject

[Text messages]         # double Enter for transition
...                     # next item

<b>+</b>[filename]             # double Enter for
<b>+</b>...                    # sending messages
</pre>
