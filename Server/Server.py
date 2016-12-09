import threading, random
from collections import defaultdict
from Session import Session
from commons import createRPCListener
from types import MethodType

class Server():
    def __init__(self):
        self.name = 'Hardcoded localhost server'
        self.prefix = self.name
        self.sessions = {}
        self.users = defaultdict(str)
        self.connections = []
        self.initListeners()

        #Create a session for faster debugging
        self.createSessionCallback("Test Session:8:MockUser")
        self.createSessionCallback("Test Session2:12:MockUser")


    def initListeners(self):
        #Listening for people joining a session
        self.joinSessionListener = MethodType(createRPCListener(self,'rpc_joinSession',self.joinSessionCallback),self,Server)
        self.joinSession = threading.Thread(target=self.joinSessionListener)
        self.joinSession.start()

        #Listening for people creating a new session
        self.createSessionListener = MethodType(createRPCListener(self, 'rpc_createSession', self.createSessionCallback), self, Server)
        self.createSession = threading.Thread(target=self.createSessionListener)
        self.createSession.start()

        #Listening for people asking for available rooms
        self.getSessionsListener = MethodType(createRPCListener(self,'rpc_getSessions',self.getSessionsCallback), self, Server)
        self.getSessions = threading.Thread(target=self.getSessionsListener)
        self.getSessions.start()

    #Called when user is attempting to join a session
    def joinSessionCallback(self,request):
        print(" [.] joinSession(%s)" % request)
        n,user = request.split(":")

        try:
            self.sessions[n].addPlayer(user)
        except KeyError:
            return "FAIL:"+n, ""

        #First argument is sent to only the sender. The second one is broadcasted globally.
        return "JOINED:"+n, ""

    # Called when user is attempting to create a new session
    def createSessionCallback(self, request):
        print(" [.] createSession(%s)" % request)
        try:
            sessionName, boardSize, user = request.split(":")
        except ValueError:
            return "FAIL", ""

        session = Session(self.name, sessionName, int(boardSize))
        self.sessions[sessionName] = session
        session.addPlayer(user)
        response = "CREATED:" + sessionName

        # First argument is sent to only the sender. The second one is broadcasted globally.
        return response, ""

    #Called when user is asking for available rooms on the server
    def getSessionsCallback(self, request):
        print(" [.] getSessions(%s)" % request)
        response = "";
        keyCount = len(self.sessions.keys())
        for i in range(0, keyCount):
            session = self.sessions[self.sessions.keys()[i]]
            response += self.sessions.keys()[i] + ":"  + str(session.boardWidth) + ":" + str(len(session.players))
            if i != keyCount - 1:
                response += ":"

        # First argument is sent to only the sender. The second one is broadcasted globally.
        return response, ""



server = Server()