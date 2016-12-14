import re
import subprocess
import time
from collections import defaultdict

class CmdTask:
	def __init__(self,task,callback):
		self.attempTimes = 3  #retry 3 time
		self.task = task
		self.callback = callback
		self.startTime = None
		self.endTime = None

	def getTimeNow(self):
		localtime = time.asctime(time.localtime(time.time()))
		return localtime

	def run(self,timeout=30,callback=None):
		self.timeout = timeout
		if self.task["optype"] == "ping":
			cmd = "ping"+" -c5 -s56 "+self.task["destination"]
			result = self.execute(cmd,timeout)
		elif self.task["optype"] == "traceroute":
			cmd = "traceroute"+" -n -m15 "+self.task["destination"]
			result = self.execute(cmd, 300)
			# result = self.executeTraceroute(cmd)	
		result["optype"] = self.task["optype"]
		result["taskid"] = self.task["taskid"]
		if self.callback:
			self.callback(result)

	def execute(self,cmd,timeout):
		"""execute the task
		"""
		self.startTime = self.getTimeNow()
		print(cmd)
		cmdlist = cmd.split(" ")
		while self.attempTimes>0:
			pipe = subprocess.Popen(cmdlist,stderr=subprocess.PIPE,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
			i = 0
			while i< timeout:
				try:
					if pipe.poll() == None:
						time.sleep(1)
						i += 1
					else:
						stdoutputdata,stderrdata = pipe.communicate()
						# if stderrdata:
						# 	self.attempTimes -= 1
						# else:
						self.attempTimes = 0
						if cmdlist[0] == "ping":
							result = self.parsePing(stdoutputdata)
						elif cmdlist[0] == "traceroute":
							result = self.parseTraceroute(stdoutputdata)
						self.endTime = self.getTimeNow()
						return self._success(result)
						break
				except TimeoutAlarm,e:
					return self._fail("timeout error")
		else:
			return self._fail("fail to execute task")

	# def executeTraceroute(self, cmd):
	# 	self.startTime = self.getTimeNow()
	# 	cmdlist = cmd.split(" ")
	# 	pipe = subprocess.Popen(cmdlist,stderr=subprocess.PIPE,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
	# 	timeout = 300
	# 	i = 0
	# 	while i<timeout:
	# 		try:
	# 			if pipe.poll() == None:
	# 				time.sleep(1)
	# 				i += 1
	# 			else:
	# 				stdoutputdata,stderrdata = pipe.communicate()
					
	# 				result = self.parseTraceroute(stdoutputdata)
	# 				self.endTime = self.getTimeNow()
	# 				return self._success(result)
	# 		except:
	# 			return self._fail("fail to execute task")
	# 	return self._fail("timeout error")

	def parsePing(self,stdoutputdata):
		"""Parse the ping result
		"""
		print(stdoutputdata)
		res = {}
		# hostname = re.search("\b(([a-zA-Z0-9]\w{0,61}?[a-zA-Z0-9]|[a-zA-Z0-9])\.){0,1}?([a-zA-Z0-9]\w{0,61}?[a-zA-Z0-9]|[a-zA-Z0-9])\.(com|edu|gov|int|mil|net|org|biz|info|name|museum|coop|aero|[a-z][a-z])(\.[a-z][a-z]){0,1}\b", stdoutputdata, re.M|re.I)
		hostname = re.split(" ", re.split(r"---", stdoutputdata)[1])[1]
		print hostname
		res["hostname"] = hostname
		re_loss_rate = re.search("\d{1,3}\.\d{1,2}\%", stdoutputdata)
		if re_loss_rate:
			print re_loss_rate.group(0)
			res["loss_rate"] = re_loss_rate.group(0)

		re_min_avg = re.search("\d{1,3}\.\d{1,3}/\d{1,3}\.\d{1,3}", stdoutputdata)
		if re_min_avg:
			print re_min_avg.group(0)
			min_avg = re_min_avg.group(0).split("/")
			res["min"] = min_avg[0]
			res["avg"] = min_avg[1]
		return res

	def parseTraceroute(self, stdoutputdata):
		"""Parse the traceroute result
		"""
		itemlist = stdoutputdata.split("\n")
		res = defaultdict(list)
		for item in itemlist:
			re_ip = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', item)
			if re_ip:
				ip = re_ip.group(0)
				res["route"].append(ip)
		res["route"].append(self.task["destination"])
		res["destination"] = self.task["destination"]
		return res

	def _success(self,result):
			return self._setTime(dict(status="success",result=result))

	def _fail(self,reason):
			return self._setTime(dict(status="fail",result=reason))

	def _setTime(self, result):
		if isinstance(result, dict):
			result['startTime'] = self.startTime
			if self.endTime:
				result['endTime'] = self.endTime
			else:
				result['endTime'] = self.getTimeNow()
		return result

class TimeoutAlarm(Exception):
	pass

def executeTask(task,callback):
	taskHandler = CmdTask(task,callback)
	taskHandler.run()




