import os
import random

import webapp2
import jinja2

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import db
from django.utils import simplejson

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)
def generate_random(len):
	word = ''
	for i in range(len):
		word += random.choice('0123456789')
	return word

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

class Connection(db.Model):
	teletoken = db.StringProperty()
	robitoken = db.StringProperty()
	robitkey = db.StringProperty()
	telekey = db.StringProperty()

class BaseHandler(webapp2.RequestHandler):
	def render(self, template, **kw):
		self.response.out.write(render_str(template, **kw))

	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

class MainPage(BaseHandler):
	def get(self):
		user = users.get_current_user()
		if not user:
			self.redirect(users.create_login_url(self.request.uri))
			return
		telerandom = generate_random(10)
		robitrandom = generate_random(10)
		self.render('main.html',
					user=user,
					telerandom = telerandom,
					robitrandom = robitrandom)

class RobitPage(BaseHandler):
	def get(self, robitkey):
		user = users.get_current_user()
		robitoken = channel.create_channel(user.user_id()+robitkey)

		q = Connection.all()
		q.filter('robitkey =', robitkey)
		for connection in q:
			connection.robitoken = robitoken
			connection.put()
			self.render('robit.html',
						token=robitoken,
						me=user.user_id(),
						telekey = connection.telekey,
						robitkey = robitkey)
			return

		telekey = generate_random(10)

		c = Connection(
			robitoken = robitoken,
			robitkey = robitkey,
			telekey = telekey,)
		c.put()

		self.render('robit.html',
					token=robitoken,
					me= user.user_id(),
					telekey = telekey,
					robitkey = robitkey)
	def post(self, robitkey):
		json_string = simplejson.loads(self.request.body)
		user = users.get_current_user()
		q = Connection.all()
		q.filter('robitkey =', robitkey)
		for conn in q:
			channel.send_message(user.user_id() + conn.telekey, "this is a message")
		self.response.out.write(simplejson.dumps(json_string["telekey"]))

class TelePage(BaseHandler):
	def get(self, telekey):
		user = users.get_current_user()
		teletoken = channel.create_channel(user.user_id() + telekey)

		q = Connection.all()
		q.filter('telekey =', telekey)
		for connection in q:
			connection.teletoken = teletoken
			connection.put()
			self.render('teleoperator.html',
						token=teletoken,
						me="this query worked fine",
						robitkey = connection.robitkey,
						telekey = telekey)
			return

		robitkey = generate_random(10)

		c = Connection(
			telekey = telekey,
			teletoken = teletoken,
			robitkey = robitkey)
		c.put()
		self.render('teleoperator.html', token=teletoken, me=user.user_id())
	def post(self, telekey):
		json_string = simplejson.loads(self.request.body)
		user = users.get_current_user()
		q = Connection.all()
		q.filter('telekey =', telekey)
		for conn in q:
			channel.send_message(user.user_id() + conn.robitkey, "this is a message")
		self.response.out.write(simplejson.dumps(json_string["robitkey"]))

class testbutton(BaseHandler):
	def post(self, robitkey):
		json_string = simplejson.loads(self.request.body)
		user = users.get_current_user()
		q = Connection.all()
		q.filter('robitkey =', robitkey)
		print robitkey
		for conn in q:
			channel.send_message(user.user_id() + conn.telekey, "this is a message")
		self.response.out.write(simplejson.dumps(json_string["telekey"]))


app = webapp2.WSGIApplication([
								('/', MainPage),
								(r'/robit/([^/]+)', RobitPage),
								(r'/tele/([^/]+)', TelePage),
								(r'/testbutton/([^/]+)', testbutton)
								],
								debug=True)
