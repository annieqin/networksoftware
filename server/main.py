# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from tornado.web import Application, StaticFileHandler
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.autoreload
from tornado.options import define, options
from ws import taskHandler, sendTaskHandler, taskDispatcher
from web import responseTimeHandler, tracerouteHandler, indexHandler
import motor
import pymongo
import uuid
import simplejson as json

define("port", default=9000, help="run on the given port", type=int)


class Application(tornado.web.Application):
	def __init__(self, db):
		self.taskDispatcher = taskDispatcher(self)
		handlers = [(r'/', indexHandler),
					(r'/taskHandler', taskHandler),
		            (r'/sendTask', sendTaskHandler),
		            (r'/responsetime', responseTimeHandler),
		            (r'/traceroute', tracerouteHandler),
		            (r'/ip_tree.json()', tornado.web.StaticFileHandler, {'path': 'ip_tree.json'})]
		settings = {'template_path': 'templates', 'static_path': 'static', 'db': db}
		tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
	mongo_client = motor.MotorClient("localhost", 27017)
	mongo_db = mongo_client["networksoftware"]
	
	tornado.options.parse_command_line()
	app = Application(mongo_db)
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()
