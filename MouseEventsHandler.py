from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from enum import Enum
from pynput.mouse import Button, Controller
import time
import json
import threading


class ClickButton(Enum):
    LEFT_BUTTON = 0
    RIGHT_BUTTON = 1

    def __int__(self):
        return self.value


class EventType(Enum):
    CLICK = 0
    MOVE = 1
    DRAG = 2

    def __int__(self):
        return self.value


class ClickEvent:
    def __init__(self):
        self.xPos = 0
        self.yPos = 0
        self.eventType = EventType.CLICK
        self.button = ClickButton.LEFT_BUTTON
        self.label = ""


class MouseEventsHandler:
    def __init__(self, predelay=2000, interval=100, loops=100):
        self.__predelay = predelay
        self.__interval = interval
        self.__loops = loops
        self.eventsList = []
        self.mouse = Controller()
        self.isToStop = False

    def generalInfo(self):
        print("Number of loops = " + str(self.__loops))
        print("Interval time (ms) = " + str(self.__interval))
        print("Number of events per loop = " + str(len(self.eventsList)))

    def setPreDelay(self, predelay):
        self.__predelay = predelay

    def setInterval(self, interval):
        self.__interval = interval

    def setLoops(self, loops):
        self.__loops = loops

    def stop(self, isToStop):
        self.isToStop = isToStop

    def addEvent(self):
        newEvent = ClickEvent()
        if len(self.eventsList) > 0:
            newEvent.xPos = self.eventsList[-1].xPos
            newEvent.yPos = self.eventsList[-1].yPos
            newEvent.button = self.eventsList[-1].button
        self.eventsList.append(newEvent)

    def removeEvent(self, event):
        if event in self.eventsList:
            self.eventsList.remove(event)

    def clearEvents(self):
        del self.eventsList[:]

    def clickEvent(self, position, button):
        self.mouse.position = position
        if button == ClickButton.LEFT_BUTTON:
            self.mouse.press(Button.left)
            time.sleep(0.001)
            self.mouse.release(Button.left)
        else:
            self.mouse.press(Button.right)
            time.sleep(0.001)
            self.mouse.release(Button.right)

    def moveEvent(self, position):
        self.mouse.position = position

    def dragEvent(self, position):
        self.mouse.press(Button.left)
        time.sleep(0.05)
        self.mouse.position = position
        self.mouse.release(Button.left)

    def runAutoClicker(self):
        time.sleep(self.__predelay/1000.0)
        for loopNumber in range(self.__loops):
            if self.isToStop:
                break
            else:
                for event in self.eventsList:
                    position = (event.xPos, event.yPos)
                    if event.eventType == EventType.CLICK:
                        self.clickEvent(position, event.button)
                    elif event.eventType == EventType.MOVE:
                        self.moveEvent(position)
                    else:
                        self.dragEvent(position)
                    time.sleep(self.__interval/1000.0)
                    if self.isToStop:
                        break
        self.isToStop = False

    def saveEvents(self, path):
        eventsData = {}
        eventsData['events'] = []
        for event in self.eventsList:

            eventsData['events'].append({
                'x': event.xPos,
                'y': event.yPos,
                'event-type': event.eventType.value,
                'button': event.button.value,
                'notes': event.label
            })
        print(path)
        with open(path, 'w') as outfile:
            json.dump(eventsData, outfile)

    def openEvents(self, path):
        self.clearEvents()
        with open(path) as file:
            eventsData = json.load(file)
            for event in eventsData['events']:
                newEvt = ClickEvent()
                newEvt.xPos = event['x']
                newEvt.yPos = event['y']
                newEvt.eventType = EventType(event['event-type'])
                newEvt.button = ClickButton(event['button'])
                newEvt.label = event['notes']
                self.eventsList.append(newEvt)