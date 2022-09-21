from socket import *
import sys
import os
import pickle

serverPort = int(sys.argv[1])
connectionsAllowed = 1

# create welcome socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(connectionsAllowed)
print("The server is ready to receive")


def sendString(socket, string):
    bytesSent = 0
    while bytesSent != len(string):
        bytesSent += socket.send(string[bytesSent:])
    return bytesSent


def receiveString(socket, length):
    string = ""
    buffer = ""
    while len(string) != length:
        buffer = socket.recv(length)
        if not buffer:
            break
        string += buffer
    return string


def sendFile(controlSocket, dataSocket, filename):
    # read file information
    fileSize = os.path.getsize(filename)
    fileObj = open(filename, 'r')
    fileData = fileObj.read(fileSize)

    # send server file size
    fileSizeStr = str(fileSize)
    while len(fileSizeStr) < 10:
        fileSizeStr = "0" + fileSizeStr
    numSent = 0
    while numSent < 10:
        numSent += controlSocket.send(fileSizeStr[numSent:])
    
    # send server file data
    numSent = 0
    while numSent < fileSize:

        numSent += dataSocket.send(fileData[numSent:])
        if not fileData[numSent:]: break #if empty, break out.

    fileObj.close()


def receiveFile(controlSocket, dataSocket, filename):
    fileSize = ""
    fileData = ""
    # receive file size from server
    while len(fileSize) < 10:
        buffer = controlSocket.recv(10)
        if not buffer:
            break
        fileSize += buffer
    fileSize = int(fileSize)

    # receive file data from server
    while len(fileData) < fileSize:
        buffer = dataSocket.recv(fileSize)
        if not buffer:
            break
        fileData += buffer

    # write data to file
    fileObj = open(filename, 'w')
    fileObj.write(fileData)
    fileObj.close()


def listDirectory(controlSocket, dataSocket):
    directory = os.listdir(os.curdir)

    file_object = open('ls.p', 'w')
    pickle.dump(directory, file_object)
    file_object.close()

    sendFile(controlSocket, dataSocket, "ls.p")
    os.remove("ls.p")


while True:
    # accept connection from client (control connection)
    controlConnection, address = serverSocket.accept()
    print("Got connection from: ", address)
    while True:
        # receive command from client
        commandLength = int(receiveString(controlConnection, 5))
        clientInput = receiveString(controlConnection, commandLength)
        command = clientInput.split()
        if command[0] == "quit":
            break

        # receive port info from client for data connection
        dataPort = int(receiveString(controlConnection, 5))
        # create new socket and connect to client (data connection)
        dataConnection = socket(AF_INET, SOCK_STREAM)
        dataConnection.connect((address[0], dataPort))
        # respond to command
        if command[0] == "get" and len(command) == 2:
            if os.path.exists(command[1]):
                sendString(controlConnection, '1')
                sendFile(controlConnection, dataConnection, command[1])
                print ("get successful, uploaded: " + command[1])
            else:
                print("Failure: file doesn't exist")
                sendString(controlConnection, '0')
        elif command[0] == "put" and len(command) == 2:
            fileExists = receiveString(controlConnection, 1)
            if fileExists == '1':
                receiveFile(controlConnection, dataConnection, command[1])
                print ("put successful, received: " + command[1])
            else:
                print("Failure: File doesn't exist")
        elif command[0] == "ls" and len(command) == 1:
            listDirectory(controlConnection, dataConnection)
            print "ls successful"
        else:
            print("Failure: invalid arguments")

        # close data connection
        dataConnection.close()
    # close control connection
    controlConnection.close()



