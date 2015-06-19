#coding: utf-8
'''
Created on 2014-5-15

@author: Administrator
'''


import smtplib
mail_from = "xj@svvt.net"
mail_pwd = "dhtyn8204"
mail_host = "smtp.exmail.qq.com"
mail_to = ["xiajiok@qq.com"]
s = smtplib.SMTP()
s.connect(mail_host)
s.login(mail_from,mail_pwd)
#s.sendmail(mail_user, mail_to, "test msg")
s.sendmail(mail_from, mail_to, 'From: from@yeah.net/r/nTo: to@21cn.com/r/nSubject: this is a email from python demo/r/n/r/nJust for test~_~')
s.close()



from email.mime.text import MIMEText
import time
 
#正文
mail_body='hello, this is the mail content'
#定义正文
msg=MIMEText(mail_body)
#定义标题
msg['Subject']='this is the title'
#定义发信人
msg['From']=mail_from
msg['To']=';'.join(mail_to)
#定义发送时间（不定义的可能有的邮件客户端会不显示发送时间）
msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')
 
smtp=smtplib.SMTP()
smtp.connect(mail_host)
#用户名密码
smtp.login(mail_from,mail_pwd)
smtp.sendmail(mail_from,mail_to,msg.as_string())
smtp.quit()
 
print 'ok'


from email.mime.multipart import MIMEMultipart

# me == my email address
# you == recipient's email address
me = "my@email.com"
you = "your@email.com"

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = "Link"
msg['From'] = me
msg['To'] = you

# Create the body of the message (a plain-text and an HTML version).
text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org"
html = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
       How are you?<br>
       Here is the <a href="http://www.python.org">link</a> you wanted.
    </p>
  </body>
</html>
"""

# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)
msg.attach(part2)

# Send the message via local SMTP server.
s = smtplib.SMTP(mail_host)
s.login(mail_from,mail_pwd)
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(mail_from, mail_to, msg.as_string())
s.quit()





