# poolcamera

## What
An IoT project including a NUC, Python scripting, a webcam, an Arduino and 3D printing.
You press the button, and magically a video of the last 30 seconds is uploaded to YouTube for your viewing pleasures.


## To install
$ virtualenv venv
$ pip install -r requirements.txt

## Setting up the hardware
There's a bunch of hardware in this project, so let's get down to business

### Button, Arduino and 3D print

- Get an arduino mini
- Upload the arduino code in this repo to it
- Get a dome button, for example from here: https://www.sparkfun.com/products/9181
- 3D print (We used a lulzbot) the button attachment
- Use the bottom of the button to screw it onto the attachment
- Use your electrical engineering skills to attach the arduino to the button
- Use a zip-tie to stabilize the arduino to the 3D printed attachment
- With a USB cable, plug arduino to NUC or other machine running the python script
- Mount the attachment to wall of choice

### NUC and Webcam

- Get a NUC or other small machine you'd like to run Python on
- Get a webcam or other USB camera, plug it into the NUC

## To run
$ source venv/bin/activate
$ python cam.py

Youtube-Upload script for API v3: https://github.com/tokland/youtube-upload
We're using a modified version to skip the command line calling. 
Source is included under youtube-upload/

## Configuring

https://console.developers.google.com

To configure OAuth:

1) Manually upload a video with: 'youtube-upload [OPTIONS] <file>'
2) Authenticate using the link given by the script
3) Copy paste the authentication code back to the script

This needs to be only done once, the upload should work automatically after that.
