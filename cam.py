import cv2
import os
import sys
import copy
import time
import datetime
import serial
import threading
from collections import deque
import subprocess
import glob
import atexit
from playsound import playsound

list = deque()
secondsDesired = 30
frameLimit = 60 * secondsDesired
cameraIndex = int(glob.glob('/dev/video*')[0][-1:])  # fetch the latest camera

threadLock = threading.Lock()


class captureThread(threading.Thread):
    stop = False
    startingTime = 0
    framesSeen = 0

    def __init__(self, threadID, name, counter):

        threading.Thread.__init__(self)
        self.shutdown_flag = threading.Event()
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        print "Starting " + self.name
        self.captureLoop()
        print "Exiting " + self.name

    def captureLoop(self):
        self.startingTime = time.time()
        #cv2.startWindowThread()             # uncomment these lines if you want to see a preview of the webcam feed.
        #window = cv2.namedWindow("preview") # if you do uncomment these lines, the program cannot be executed as a service anymore
        vc = cv2.VideoCapture(cameraIndex)
        lastAcceptedTime = 0
        print vc
        try:
            if vc.isOpened():  # try to get the first frame
                cameraWorking, frame = vc.read()
            else:
                cameraWorking = False
            self.width = len(frame[0])
            self.height = len(frame)

        except Exception as e:
            vc.release()
            print "Exception! {0} ".format(e)
            t2.stop = True
            return

        self.framesSeen = 1

        print self.width, self.height

        while not self.shutdown_flag.is_set():
            lockAquired = threadLock.acquire(False)
            if lockAquired:
                cameraWorking, frame = vc.read()
                if not cameraWorking:
                    break
                list.append(frame)
                if len(list) > frameLimit:
                    list.popleft()
                self.framesSeen = self.framesSeen + 1
                #cv2.imshow("preview", frame) # uncomment this line, and line 42 and 43, if you want the preview of the webcam feed to be updated
                k = cv2.waitKey(1)
                if k % 256 == 27:
                    vc.release()
                    t2.stop = True
                    break
                threadLock.release()

    def saveCaptured(self):
        threadLock.acquire()
        suggestedPressTime = time.time()

        endingTime = time.time()
        # generate the actual image here

        print "Time elapsed:", (endingTime - self.startingTime)
        timeElapsed = endingTime - self.startingTime
        realFps = self.framesSeen / timeElapsed
        print "Real fps:", realFps

        framesDesired = int(realFps * secondsDesired)
        startingIndex = max(0, len(list) - framesDesired)

        videoCore = str(datetime.datetime.now())
        videoCore = videoCore.replace(" ", "_")
        videoName = videoCore + ".avi"
        print "Video name", videoName
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(videoName, fourcc, realFps,
                                 (self.width, self.height))
        for i in range(startingIndex, len(list)):
            writer.write(list[i])

        del writer

        print "Video name:", videoName
        print "Video core:", videoCore

        cmd = "./uploadvideo.bash '" + videoName + "' '" + videoCore + "'"
        os.system(cmd)
        playsound('upload_complete.wav')
        list.clear()
        threadLock.release()


class inputThread(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.shutdown_flag = threading.Event()
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):
        print "Starting " + self.name
        self.inputLoop()
        print "Exiting " + self.name

    def inputLoop(self):
        while not self.shutdown_flag.is_set():
            try:
                ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  # make sure the arduino is running the same baud rate
                input_line = ser.readline()
                ser.flushInput()
                if input_line.strip() == 'a':
                    playsound('button_press.wav')
                    print "Capturing"
                    t1.saveCaptured()
            except Exception as e:
                print "Exception! {0} ".format(e)
                t1.stop = True
                break


def reverseFrame(frame):
    frame = frame[::-1]
    for i in range(0, len(frame)):
        frame[i] = frame[i][::-1]
    return frame


if __name__ == "__main__":
    t1 = captureThread(1, "Capture Thread", 1)
    t2 = inputThread(2, "Input Thread", 2)

    t1.start()
    time.sleep(5)
    t2.start()

    while True:
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:  # kill the threads if the user stops the program
            print "Keyboard interrupt"
            t1.shutdown_flag.set()
            t2.shutdown_flag.set()
            t1.join()
            t2.join()
            break
    print "Exiting Main Thread"