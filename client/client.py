from socket import *
import sys
import os
import pickle

try:
    address = gethostbyname(sys.argv[1])
except:
    print("Unable to resolve host!")
    sys.exit()

port = int(sys.argv[2])

# open control connection  and connect to server's welcome socket
controlConnection = socket(AF_INET, SOCK_STREAM)
controlConnection.connect((address, port))

def sendString(socket, string):
    bytesSent = 0
    while bytesSent != len(string):
        bytesSent += socket.send(string[bytesSent:])


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

    return fileSize


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

    return fileSize # Number of bytes received


def receiveListDirectory(controlSocket, dataSocket):
    receiveFile(controlSocket, dataSocket, "ls.p")

    file_object = open('ls.p', 'r')
    directory = pickle.load(file_object)
    file_object.close()
    os.remove("ls.p")

    print directory


validCommands = ["get", "put", "ls", "quit"]

running = True
while running:
    # take user input and check if valid
    userInput = raw_input("ftp>")    
    command = userInput.split()
    while command[0] not in validCommands:
        print("Invalid command")
        userInput = raw_input("ftp>")    
        command = userInput.split()

    userInputLength = str(len(userInput))
    while len(userInputLength) < 5:
        userInputLength = "0" + userInputLength

    # send command to server
    sendString(controlConnection, userInputLength)
    sendString(controlConnection, userInput)


    if command[0] in validCommands[0:3] and len(command) <= 2:
        # Generate ephmeral port for data channel
        welcomeConnection = socket(AF_INET, SOCK_STREAM)
        welcomeConnection.bind(('', 0))
        welcomeConnection.listen(1)
        dataPort = str(welcomeConnection.getsockname()[1])
        # Send port info to server
        sendString(controlConnection, dataPort)
        # accept connection from server
        dataConnection, address = welcomeConnection.accept()
        # receive or upload data
        if command[0] == "get" and len(command) == 2:
            fileExists = receiveString(controlConnection, 1)
            if fileExists == '1':
                fileSize = receiveFile(controlConnection, dataConnection, command[1])
                print ("received " + command[1] + " " + str(fileSize) + " bytes downloaded")
            else:
                print("Failure: File doesn't exist")
        elif command[0] == "put" and len(command) == 2:
            if os.path.exists(command[1]):
                sendString(controlConnection, '1')
                fileSize = sendFile(controlConnection, dataConnection, command[1])
                print ("uploaded " + command[1] + " " + str(fileSize) + " bytes uploaded")
            else:
                print("Failure: file doesn't exist")
                sendString(controlConnection, '0')

        elif command[0] == "ls" and len(command) == 1:
            receiveListDirectory(controlConnection, dataConnection)
        else:
            print("Failure: invald arguments")

        # close data connection
        dataConnection.close()
    elif command[0] == "quit":
        running = False

# close control connection
controlConnection.close()
