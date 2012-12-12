#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2009 Im, Hyo Jun
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
#
# I am holding the CELF Korea Technical Jamboree event on Oct 30th, 2009.
# This is a web application that handles user registration for the event. (http://celf-kor-jamboree.appspot.com)
#
# This application displays very simple registration form.
# Users enter their name, company and e-mail address, and then press the 'register' button.
# Then, the information provided by user is stored in the Google data store (i.e. database)
#
# If a user accesses the following url, he can get the list of all the users who registered for the event.(Only administrators can view the result)
# http://celf-kor-jamboree.appspot.com/list


import cgi
import datetime
import wsgiref.handlers
from string import *

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

messages = {'no name':u'이름을 입력해 주세요. Please enter your name.',
		'no email':u'E-mail 주소를 입력해 주세요. Please enter your e-mail address.',
		'no company':u'소속 회사를 입력해 주세요. Please enter your company.',
		'invalid email':u'올바른 e-mail 주소를 입력해 주세요. Please enter the valid e-mail address',
		'already registered':u' e-mail 주소는 이미 등록되어 있습니다. The e-mail address is already registered.',
		'thanks':u'님, 등록해 주셔서 감사합니다. Thank you for your registration. <br> ',
		'see you':u' 11월 6일에 뵙겠습니다. See you on November 6th. <br> 등록은 완료되었으며 별도의 등록 완료 메일은 발송되지 않으니 참고하시기 바랍니다. <br>Please be noted that no confirmation mail will be sent to your e-mail address.',
		'not administrator':u'관리자만 조회가 가능합니다. Only administrators can access this page.',
		'title':u'5th CELF Korea Tech Jamboree Registration',
		'name':u'이름(Name)',
		'email':u'E-mail',
		'company':u'회사(Company)'}
		
# character set used to validate the e-mail address
rfc822_specials = '()<>@,;:\\"[]'

# Check the validity of the e-mail address
def isAddressValid(addr):
    # First we validate the name portion (name@domain)
    c = 0
    while c < len(addr):
        if addr[c] == '"' and (not c or addr[c - 1] == '.' or addr[c - 1] == '"'):
            c = c + 1
            while c < len(addr):
                if addr[c] == '"': break
                if addr[c] == '\\' and addr[c + 1] == ' ':
                    c = c + 2
                    continue
                if ord(addr[c]) < 32 or ord(addr[c]) >= 127: return 0
                c = c + 1
            else: return 0
            if addr[c] == '@': break
            if addr[c] != '.': return 0
            c = c + 1
            continue
        if addr[c] == '@': break
        if ord(addr[c]) <= 32 or ord(addr[c]) >= 127: return 0
        if addr[c] in rfc822_specials: return 0
        c = c + 1
    if not c or addr[c - 1] == '.': return 0

    # Next we validate the domain portion (name@domain)
    domain = c = c + 1
    if domain >= len(addr): return 0
    count = 0
    while c < len(addr):
        if addr[c] == '.':
            if c == domain or addr[c - 1] == '.': return 0
            count = count + 1
        if ord(addr[c]) <= 32 or ord(addr[c]) >= 127: return 0
        if addr[c] in rfc822_specials: return 0
        c = c + 1

    return count >= 1
    

# DB model class which stores the attendees of Korea Technical Jamboree event    
class Attendee(db.Model):
	email = db.StringProperty()
	name = db.StringProperty()
	company = db.StringProperty()
	date = db.DateTimeProperty(auto_now_add=True)


def showHTMLTitle(myself):
	myself.response.out.write(u"""
	<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> 
	<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=EUC-KR" /> 
		<title>""" + messages['title'] + u"""</title> 
		<meta name="Keywords" content="" /> 
		<meta name="Description" content="" />
		<link rel="stylesheet" type="text/css" href="stylesheets/common.css" />
	</head>
	<body>
	<div id="header">
		<h1> """ + messages['title'] + u"""</h1>
	</div>
	<div class = "container clearfix">
		<div class="main">
			<h2> <a href = "http://tree.celinuxforum.org/CelfPubWiki/KoreaTechJamboree"> """ + messages['title'] + u""" </a></h2>""")
			
def showHTMLFooter(myself):
	myself.response.out.write(u"""
		</div>
	</div>
	
	<div id="footer">
		<p class="title">CE Linux Forum</p> 
		<p class="copyright">Linux&reg; is a registered trademark owned by Linus Torvalds</p>
	</div>
	
	</body>
	</html>""")
	

# Show the registration form
# At the top of the registration form, the myMsg message will be displayed.
def showForm(myself, myMsg, name = '', email = '', company = ''):
	showHTMLTitle(myself)
	if (myMsg):
		myself.response.out.write(myMsg + u"<br>")
	
	myself.response.out.write(u"""
	  <form action="/register" method="post">
	  <center>
	    <table>
	    <tr><td>""" + messages['name'] + u""": </td><td><input type="text" name="name" value = """)
	myself.response.out.write(u'"' + name + u'"')
	myself.response.out.write(u""" /></td>
	    <tr><td>""" + messages['email'] + u""": </td><td><input type="text" name="email" value = """)
	myself.response.out.write(u'"' + email + u'"')
	myself.response.out.write(u""" /></td>
	    <tr><td>""" + messages['company'] + u""": </td><td><input type="text" name="company" value = """)
	myself.response.out.write(u'"' + company + u'"')
	myself.response.out.write(u""" /></td>
	    </table>
	    </center>
	    <br><input type="submit" value="Register">
	  </form>""")
	showHTMLFooter(myself)



class MainPage(webapp.RequestHandler):
	def get(self):
		showForm(self, u'')


# List up all the attendees of the event
class ListAttendees(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		
		if user:
			showHTMLTitle(self)
			if users.is_current_user_admin():
				self.response.out.write(u'<center><div id="list"><table rules="cols">')
				self.response.out.write(u'<caption>List of attendees</caption>')
				self.response.out.write(u'<colgroup><col id="name" /><col id="email" /><col id="company" /></colgroup>')
				self.response.out.write(u'<thread><tr><th scope="col">이름</th><th scope="col">E-mail</th><th scope="col">회사</th></tr></thead><tbody>')
				query = db.GqlQuery("SELECT * FROM Attendee")
				for result in query:
					self.response.out.write(u"<tr><td>" + result.name + u"</td><td>" + result.email + u"</td><td>" + result.company + u"</td></tr>")
				self.response.out.write(u"</tbody></table></div></center>")
			else:
				self.response.out.write(messages['not administrator'] + u" <br>")
			showHTMLFooter(self)
		else:
			self.redirect(users.create_login_url(self.request.uri))


# This class is invoked when user press the submit button.
# Register the user information to the DB
class Register(webapp.RequestHandler):
	def post(self):
		email = self.request.get('email')
		name = self.request.get('name')
		company = self.request.get('company')
	
		if name == '':
			showForm(self, messages['no name'], name, email, company)
		elif email == '':
			showForm(self, messages['no email'], name, email, company)
		elif company == '':
			showForm(self, messages['no company'], name, email, company)
		elif (isAddressValid(email)):
			query = db.GqlQuery("SELECT * FROM Attendee WHERE email = :1", email)
			result = query.fetch(1)
			if len(result) > 0:
				showHTMLTitle(self)
				self.response.out.write(email + u" " + messages['already registered'])
				showHTMLFooter(self)
			else:
				attendee = Attendee()
				attendee.email = email
				attendee.name = name
				attendee.company = company
				attendee.put()
				showHTMLTitle(self)
				self.response.out.write(name + messages['thanks'] + messages['see you'])
				showHTMLFooter(self)
		else:
			showForm(self, messages['invalid email'], name, email, company)
   			


application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/main', MainPage),
  ('/register', Register),
  ('/list', ListAttendees)
])


def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
