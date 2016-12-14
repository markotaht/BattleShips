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
        self.users = []
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

        session.tryAddPlayer(username)
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
            return "FAIL:"+sessionName +":INVALIDSESSION", ""

        if session.state == "INIT":
            success = session.tryAddPlayer(username)
            if not success:
                #Name already in use
                return "FAIL:"+ sessionName +":NAMEINUSE", ""

            #Doesn't matter if rejoining. User can re-place his ships
            #TODO: Handle case where user placed ships, game is still in INIT but user rejoined
            print("Allowing %s to join." % username)

            message = "WELCOME:" + sessionName + ":" + str(session.hostName == username) + ":"
            # Also include a list of currently connected players
            for player in session.players.keys():
                if player != username:
                    message += player + ";" + str(session.players[player].isReady) + ";"
            # Remove the extra ; at the end
            message = message[:-1]

            return message, ""
        elif session.state == "PLAY":
            if username in session.players and session.players[username].connected == False:
                print("Allowing %s to rejoin." % username)

                session.updateChannel.basic_publish(exchange=session.prefix + 'updates', routing_key='',
                                                 body="REJOININGPLAYER:%s" % username)

                #THIRD ARGUMENT: board width
                message = "WELCOMEBACK:"+sessionName + ":" + str(session.boardWidth) + ":"

                #FOURTH ARGUMENT: player board
                boardData = ""
                for x in range(0, session.boardWidth):
                    for y in range(0, session.boardWidth):
                        boardData += str(session.players[username].board[x][y])

                print "Board Data: " + boardData

                message += boardData + ":"

                #FIFTH ARGUMENT: Whose turn it is
                message += session.order[session.playerturn] + ":"

                #SIXTH ARGUMENT: Other players data
                # Also include a list of currently connected players
                for player in session.players.keys():
                    if player != username:
                        message += player + ";" + str(session.players[player].connected) + ";"

                        boardData = ""
                        for x in range(0, session.boardWidth):
                            for y in range(0, session.boardWidth):
                                boardData += str(session.players[username].otherBoards[player][x][y])
                        print "Board Data: " + boardData
                        message += boardData + ";"


                # Remove the extra ; at the end
                message = message[:-1]

                return message, ""
            else:
                print "Rejecting %s from rejoining. Already connected without having timed out."
                return "FAIL:" + sessionName + ":NAMEINUSE", ""

            print("Rejecting %s joining. Game already started." % username)
            return "FAIL:"+sessionName + ":GAMESTARTED", ""
        else:
            print("Rejecting %s joining. Game already started." % username)
            return "FAIL:"+sessionName + ":GAMESTARTED, """

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

    def joinServerCallback(self, request):
        print(" [.] joinServer (%s)" %request)
        response = "";
        if(request in self.users):
            return "FAIL:" + self.name +":NAMEINUSE", ""
        else:
            self.users.append(request)
            return "SUCCESS", ""



if __name__ == "__main__":
    server = Server()