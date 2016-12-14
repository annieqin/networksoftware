# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from tornado.websocket import WebSocketHandler
from tornado.httputil import HTTPServerRequest
from tornado.web import RequestHandler
from tornado import gen
import json
import uuid
import pymongo
import motor
import re

global result
result = []

# mongo_client = motor.MotorClient('localhost', 27017)
# mongo_db = mongo_client['networksoftware']

class taskHandler(WebSocketHandler):
	"""receive tasks and send to client end 
	"""
	def on_close(self):
		print("Connection Closed")
		super(taskHandler, self).on_close()

	def on_message(self, message):
		"""call callback method(registered by sendTaskHandler) in taskDispatcher when received message from client
		"""
		data = json.loads(message)
		result.append(data)  # we usually put them into database
		mongo_db = self.settings["db"]
		mongo_db.meterResult.insert(data)		
		if data["taskid"]:
			print "data before---"
			print data
			data.pop("_id", None)
			print "data after---"
			print data
			self.application.taskDispatcher.callbackResult(json.dumps(data))

	def open(self, *args, **kwargs):
		"""register seedMessage method to taskDispatcher when opened
		"""
		print("connect...")				
		# sendMsg = dict(optype="traceroute",destination="sina.com",taskid=str(uuid.uuid1()))
		# msg = json.dumps(sendMsg)
		# self.write_message(msg)
		self.application.taskDispatcher.register(self.seedMessage)

	####TODO:use regex to check weather msg in correct format
	def seedMessage(self,msg):
		"""send task to client
		"""
		msg["taskid"] = str(uuid.uuid1())
		if re.compile(r"^\w+\.\w+$").search(msg["destination"]) or re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$").search(msg["destination"]):
			self.write_message(json.dumps(msg))


####TODO:write like taskHandler,try to receive meter task from webpage and then write back to webpage
class sendTaskHandler(WebSocketHandler):
	"""receive tasks from web page and dispatch to taskHandler
	"""
	def check_origin(self, origin):
		return True

	def on_message(self, message):
		"""call seedMessage method(registered in taskHandler) in taskDispatcher to send task to client
		"""
		task = json.loads(message)
		self.application.taskDispatcher.dispatch(task)

	def on_close(self):
		super(sendTaskHandler, self).on_close()

	def open(self, *args, **kwargs):
		"""register callback method to taskDispatcher when opend
		"""
		print("open connection from web")
		self.application.taskDispatcher.register2(self.callback)
		super(sendTaskHandler, self).open(*args, **kwargs)

	def callback(self,msg):
		"""send result to web page
		"""
		self.write_message(msg)



class taskDispatcher():
	"""dispatch tasks from sendTaskHandler to taskHandler
	"""
	def __init__(self,app):
		self.app = app
		self.sendMessage = None
		self.callback = None

	#传送命令
	def dispatch(self,task):
		sendMessage = self.sendMessage
		if sendMessage:
			sendMessage(task)

	def register(self,sendMessage):
		self.sendMessage = sendMessage

	#返回结果
	####TODO:write like dispatcher() ,try to wirte callback function
	def callbackResult(self,Message):
		callback = self.callback
		if callback:
			callback(Message)


	def register2(self,callback):
		self.callback = callback







