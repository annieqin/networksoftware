from threading import Thread

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS
from twisted.internet import reactor, threads
from twisted.internet.protocol import ReconnectingClientFactory, Factory
from twisted.python import log
import json
from tasks import executeTask

global factory
factory = None

WS_ADDRESS = "ws://127.0.0.1:9000/taskHandler"


class MyWebSocketClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
	protocolInstance = None

	def buildProtocol(self, addr):
		proto = Factory.buildProtocol(self, addr)
		self.protocolInstance = proto
		return proto

	def clientConnectionFailed(self, connector, reason):
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

	def clientConnectionLost(self, connector, unused_reason):
		ReconnectingClientFactory.clientConnectionLost(self, connector, unused_reason)

	def send(self, message):
		if self.protocolInstance:
			if isinstance(message, dict):
				self.protocolInstance.sendMessage(json.dumps(message, ensure_ascii=False))
			elif isinstance(message, str) or isinstance(message, unicode):
				self.protocolInstance.sendMessage(message)


class ProbeWebsocketClientProtocol(WebSocketClientProtocol):
	def onConnect(self, response):
		print("client ws connected")
		super(ProbeWebsocketClientProtocol, self).onConnect(response)

	def onMessage(self, payload, isBinary):
		print(payload)
		task = json.loads(payload)
		if "optype" in task:
			d = threads.deferToThread(executeTask, task, self.callback)
			d.addErrback(log.err)

	def onClose(self, wasClean, code, reason):
		print("Connection Closed")
		super(ProbeWebsocketClientProtocol, self).onClose(wasClean, code, reason)

	def callback(self, result):
		self.sendMessage(json.dumps(result))
		return


####TODO:connect to websocket server,your can refer twisted example to  complete the function(the server address is WS_ADDRESS)
#### the example: https://github.com/crossbario/autobahn-python/tree/master/examples/twisted/websocket/echo
def connectServer(serverAddr):
	factory = WebSocketClientFactory(serverAddr)

	factory.protocol = ProbeWebsocketClientProtocol
	reactor.connectTCP("127.0.0.1", 9000, factory)
	reactor.run()


if __name__ == "__main__":
	print("client start")
	connectServer(WS_ADDRESS)
