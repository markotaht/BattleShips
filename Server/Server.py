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


    def initListeners(self):
        # Listening for people creating a new session
        self.createSessionListener = MethodType(createRPCListener(self, 'rpc_createSession', self.createSessionCallback), self, Server)
        self.createSession = threading.Thread(target=self.createSessionListener)
        self.createSession.start()

        #Listening for people joining a session
        self.joinSessionListener = MethodType(createRPCListener(self,'rpc_joinSession',self.joinSessionCallback),self,Server)
        self.joinSession = threading.Thread(target=self.joinSessionListener)
        self.joinSession.start()

        #Listening for people asking for available rooms
        self.getSessionsListener = MethodType(createRPCListener(self,'rpc_getSessions',self.getSessionsCallback), self, Server)
        self.getSessions = threading.Thread(target=self.getSessionsListener)
        self.getSessions.start()

    # Called when user is attempting to create a new session
    def createSessionCallback(self, request):
        print(" [.] createSession(%s)" % request)
        try:
            sessionName, boardSize, username = request.split(":")
        except ValueError:
            return "FAIL", ""

        session = Session(self.name, sessionName, username, int(boardSize))
        self.sessions[sessionName] = session

        session.addPlayer(username)
        response = "CREATED:" + sessionName

        # First argument is sent to only the sender. The second one is broadcasted globally.
        return response, ""


    #Called when user is attempting to join a session
    def joinSessionCallback(self, request):
        print(" [.] joinSession(%s)" % request)
        sessionName,username = request.split(":")

        try:
            session = self.sessions[sessionName]
        except KeyError:
            # First argument is sent to only the sender. The second one is broadcasted globally.
            print("Invalid sessionName provided by %s" % username)
            return "FAIL:"+sessionName, ""

        if session.state == "INIT":
            session.addPlayer(username)
            #Doesn't matter if rejoining. User can re-place his ships
            #TODO: Handle case where user placed ships, game is still in INIT but user rejoined
            print("Allowing %s to join." % username)

            message = "WELCOME:" + sessionName + ":" + str(session.hostName == username) + ":"
            # Also include a list of currently connected players
            for player in session.players.keys():
                message += player + ";" + str(session.players[player].isReady) + ";"
            # Remove the extra ; at the end
            message = message[:-1]

            return message, ""
        else:
            if username in session.players:
                print("Allowing %s to rejoin." % username)

                message = "WELCOMEBACK:"+sessionName + ":" + str(session.hostName == username) + ":"
                # Also include a list of currently connected players
                for player in session.players.keys():
                    message += player + ";" + str(session.players[player].isReady) + ";"
                # Remove the extra ; at the end
                message = message[:-1]

                return message, ""
            else:
                print("Rejecting %s joining. Game already started." % username)
                return "FAIL:"+sessionName, ""

    #Called when user is asking for available rooms on the server
    def getSessionsCallback(self, request):
        print(" [.] getSessions(%s)" % request)
        response = "";
        keyCount = len(self.sessions.keys())
        for i in range(0, keyCount):
            session = self.sessions[self.sessions.keys()[i]]
            response += self.sessions.keys()[i] + ":"  + str(session.boardWidth) + ":" + str(len(session.players)) + ":" + session.state
            if i != keyCount - 1:
                response += ":"

        # First argument is sent to only the sender. The second one is broadcasted globally.
        return response, ""


if __name__ == "__main__":
    server = Server()