import cv2
import numpy
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
secondsDesired = 30 # amount of seconds to upload 
frameLimit = 60 * secondsDesired # cannot exceed more than 60 FPS for 30 seconds
videoDevices = glob.glob('/dev/video*')
print "Pool Camera -- Available video devices: ", videoDevices
cameraIndex = int(videoDevices[0][-1:])  # fetch the latest camera, whatever last number it has in the device
print "Pool Camera -- Using video device index ", cameraIndex

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
        print "Capture Thread -- Starting " + self.name
        self.captureLoop()
        print "Capture Thread -- Exiting " + self.name

    def captureLoop(self):
        self.startingTime = time.time()
        #cv2.startWindowThread()             # uncomment these lines if you want to see a preview of the webcam feed.
        #window = cv2.namedWindow("preview") # if you do uncomment these lines, the program cannot be executed as a service anymore
        try:
            vc = cv2.VideoCapture(cameraIndex)

        except Exception as e:
            print "Capture Thread -- Exception! {0} ".format(e)
            print "Capture Thread -- Failed to start video capture."
            t2.stop = True
            return
        #print vc
        try:
            if vc.isOpened():  # try to get the first frame
                cameraWorking, frame = vc.read()
            else:
                cameraWorking = False
                frame = numpy.zeros((1, 1, 3), numpy.uint8)
            self.width = len(frame[0])
            self.height = len(frame)

        except Exception as e:
            vc.release()
            print "Capture Thread -- Exception! {0} ".format(e)
            t2.stop = True
            return

        self.framesSeen = 1

        print "Capture Thread -- Width: ", self.width, " Height: ", self.height

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
                if k % 256 == 27: # escape character to cancel running threads
                    vc.release()
                    t2.stop = True
                    break
                threadLock.release()

    def saveCaptured(self):
        threadLock.acquire()

        endingTime = time.time()
        # generate the actual image here

        print "Save Captured -- Time elapsed:", (endingTime - self.startingTime)
        timeElapsed = endingTime - self.startingTime
        realFps = self.framesSeen / timeElapsed
        print "Save Captured -- Real fps:", realFps

        framesDesired = int(realFps * secondsDesired)
        startingIndex = max(0, len(list) - framesDesired)

        videoCore = str(datetime.datetime.now())
        videoCore = videoCore.replace(" ", "_")
        videoName = videoCore + ".avi"
        print "Save Captured -- Video name: ", videoName
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(videoName, fourcc, realFps,
                                 (self.width, self.height))
        for i in range(startingIndex, len(list)):
            writer.write(list[i])

        del writer

        print "Save Captured -- Video name: ", videoName
        print "Save Captured -- Video core: ", videoCore

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
        print "InputThread -- Starting " + self.name
        self.inputLoop()
        print "InputThread -- Exiting " + self.name

    def inputLoop(self):
        while not self.shutdown_flag.is_set():
            try:
                baudRate = 9600 # make sure the arduino is running the same baud rate
                arduinoDeviceLocation = '/dev/ttyACM0' # make sure your arduino is at this device
                ser = serial.Serial(arduinoDeviceLocation, baudRate, timeout=1)  # timeout after 1 second
                input_line = ser.readline()
                ser.flushInput()
                if input_line.strip() == 'a': # make sure the arduino is sending the same character
                    playsound('button_press.wav')
                    print "InputThread -- Capturing"
                    t1.saveCaptured()
            except Exception as e:
                print "InputThread -- Exception! {0} ".format(e)
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
            print "Pool Camera -- Keyboard interrupt"
            t1.shutdown_flag.set()
            t2.shutdown_flag.set()
            t1.join()
            t2.join()
            break
    print "Pool Camera -- Exiting Main Thread"
