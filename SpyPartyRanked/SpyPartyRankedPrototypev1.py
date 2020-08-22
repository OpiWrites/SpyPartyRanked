from ReplayParser import * ###Import parse function
def readLog(logName):
    print("Entered method")
    replayList = []
    rankedIsOn = 0
    file = open(logName, 'r')
    logLines = file.readlines()
    for line in logLines:
        if line.count("you choose") == 1: ##Turns on ranked when key phrase is found
            rankedIsOn = 1
            print("Ranked is on")
        if rankedIsOn == 1 and line.count("LobbyClient starting to lobby from IN_MATCH") == 1: ##Turns off ranked when match ends
            rankedIsOn = 0
            print("Ranked is off")
        if rankedIsOn == 1 and line.count("Writing replay") == 1: ##Finds and saves replay paths while ranked is on
            replayFind = line.split(": ") ##Make this regex later
            pathString = replayFind[2]
            pathString = pathString.rstrip()
            pathString = pathString.strip('\"')
            replayList.append(pathString) 
            print("Found replay, saving path")
    return replayList

def getResult(replayPath):
    hummus = ReplayParser()
    replay = hummus.parse(replayPath)
    spyName = replay.spy
    sniperName = replay.sniper
    result = replay.result
    venue = replay.venue
    print(venue, spyName, sniperName, result)

replayList = readLog("C:/Users/Aidan/AppData/Local/SpyParty/logs/SpyPartyTestFile.log")
for replayPath in replayList:
    getResult(replayPath)
