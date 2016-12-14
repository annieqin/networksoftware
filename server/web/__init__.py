# -*- coding: utf-8 -*-
from tornado.web import RequestHandler
from tornado import gen
import json


class indexHandler(RequestHandler):
	def get(self):
		self.render("websocketFrontPage.html")
	post = get

class responseTimeHandler(RequestHandler):
	"""Load the data of response time from database and show in the form of charts at the front end  
	"""
	@gen.coroutine
	def get(self):
		"""process GET request, response with responsetime.html
		"""
		# min_res = []
		avg_res = []
		x_ticks = []
		results = yield self.do_find()
		for index, item in enumerate(results):
			# min_time = item["result"].get("min", "")
			avg_time = item["result"].get("avg", "")
			hostname = item["result"].get("hostname", "")
			# min_res.append([index+1,float(min_time)])
			if avg_time and hostname:
				avg_res.append([index+1,float(avg_time)])
				x_ticks.append([index+1,str(hostname)])
		data = [avg_res]
		res = {"data": data, "xticks": x_ticks}
		self.render("responsetime.html", **res)

	@gen.coroutine
	def do_find(self):
		"""load data from mongodb
		"""
		mongo_db = self.settings["db"]
		cursor = mongo_db.meterResult.find({
			"result.loss_rate": {
				"$exists": True
			}
		})
		res = yield cursor.to_list(None)
		raise gen.Return(res)

class tracerouteHandler(RequestHandler):
	"""Load the data of traceroute from database and show in the form of graph at the front end
	"""
	@gen.coroutine
	def get(self):
		results = yield self.do_find()
		res = []
		for index, item in enumerate(results):
			route = item["result"]["route"]
			res.append({"route": route,
						"destination": item["result"]["destination"],
						})
		ip_tree = yield self.gen_tree(res)
		with open("ip_tree.json", "w") as f:
			f.write(json.dumps(ip_tree))
		self.render("traceroute.html")		

	@gen.coroutine
	def do_find(self):
		"""load data from mongdb
		"""
		mongo_db = self.settings["db"]
		cursor = mongo_db.meterResult.find({
			"result.route": {
				"$exists": True
			}
		})
		res = yield cursor.to_list(None)
		raise gen.Return(res)

	# @gen.coroutine
	# def gen_tree(self, data):
	# 	ip_tree = ipTree()
	# 	for route in data:
	# 		for index, ip in enumerate(route["route"]):
	# 			node = ip_tree.get_node(ip)
	# 			if node:
	# 				continue
	# 			else:
	# 				if index == 0:
	# 					parent_node = ip_tree.root
	# 				else: 
	# 					parent_node = ip_tree.get_node(route["route"][index-1])	
	# 				parent_node.children[ip] = ipNode(ip)
	# 	raise gen.Return(ip_tree)

	@gen.coroutine
	def gen_tree(self, data):
		"""generate a tree according to the ip node
		"""
		ip_tree = ipTree()
		for route in data:
			ips = route["route"]
			for index, ip in enumerate(ips):
				path = " ".join(ips[:index+1])			
				node = ip_tree.get_node(path)
				if node:
					continue
				else:
					parent_path = " ".join(ips[:index])
					parent_node = ip_tree.get_node(parent_path)
					parent_node.children[path] = ipNode(ip, path)
		json_tree = ip_tree.root.to_json_node()
		raise gen.Return(json_tree)


class ipTree(object):
	def __init__(self):
		self.root = ipNode("127.0.0.1", "")

	# def get_node(self, ip):
	# 	node = self.root
	# 	queue = []
	# 	queue.append(node)
	# 	while queue:
	# 		node = queue.pop(0)
	# 		if node.children:
	# 			if ip in node.children:
	# 				return node.children[ip]
	# 			else:
	# 				for ip in node.children:
	# 					queue.append(node.children[ip])
	# 	return None

	def get_node(self, path):
		"""search node according to its path
		"""
		if not path:
			return self.root
		parent_node = self.get_node(" ".join(path.split(" ")[:-1]))
		return parent_node.children.get(path, "")


class ipNode(object):
	def __init__(self, name, path, children=None):
		self.name = name
		self.path = path
		self.children = {} if children is None else children

	def to_json_node(self):
		"""convert an ipTree into a tree conforming to json format
		"""
		res = {"name": self.name, "children": []}
		for node in self.children.values():		
			res["children"].append(node.to_json_node())
		return res