import os
import gzip
from ReplayParser import * ###Import parse function
def readLog(logName):
    
    replayList = []
    rankedIsOn = 0
    try:
        with gzip.open(logName, 'rt') as file:
            logLines = file.readlines()
            for line in logLines:
                if line.count("Ranked mode on") and line.count("LobbyClient sending chat message") == 1: ##Turns on ranked when key phrase is found in local chat logs
                    rankedIsOn = 1
                    print("Ranked is on")
                elif rankedIsOn == 1 and line.count("LobbyClient starting to lobby from IN_MATCH") == 1: ##Turns off ranked when match ends
                    rankedIsOn = 0
                    print("Ranked is off")
                elif rankedIsOn == 1 and line.count("Writing replay") == 1: ##Finds and saves replay paths while ranked is on
                    replayFind = line.split(": ")
                    pathString = replayFind[2]
                    pathString = pathString.rstrip()
                    pathString = pathString.strip('\"')
                    replayList.append(pathString) 
                    print("Found replay, saving path")
            file.close
            return replayList
    except:
        print("SpyParty is running!")

def getResult(replayPath):
    hummus = ReplayParser()
    replay = hummus.parse(replayPath)
    print(replay.venue, replay.spy, replay.sniper, replay.result)

def findLogPath():
    Dir = os.getcwd()
    parenDir = os.path.dirname(Dir)
    return(parenDir + "\\logs")

def findLog(logPath):
    lastEdited = 0
    logFile = ""
    for file in os.scandir(logPath):
        if os.path.getctime(file) > lastEdited:
            lastEdited = os.path.getctime(file)
            logFile = os.path.join(logPath, file)
    return logFile    

