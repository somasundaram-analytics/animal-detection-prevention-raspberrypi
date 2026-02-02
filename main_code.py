import cv2
import numpy as np
import os
import time
import serial
import smtp
import pygame
import RPi.GPIO as GPIO
import lcd

relay = 36

duration =20
GPIO.setmode(GPIO.BOARD)

GPIO.setup(relay,GPIO.OUT)
GPIO.output(relay,False)

animals = { "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}

ser=serial.Serial(port='/dev/ttyS0',baudrate=9600,timeout=1)


def sms(animal):

    print("Sending Message")
    lcd.display("Sending ", "Message...")
    time.sleep(1)        
    ser.write(b'AT\r\n')
    time.sleep(1)
    ser.write(b"AT+CMGF=1\r")
    time.sleep(3)
    ser.write(b'AT+CMGS="+917893755859"\r')
    h=f"-= ALERT =- \n{animal} detected in the field"
    time.sleep(3)
    ser.reset_output_buffer()
    time.sleep(1)
    ser.write(str.encode(h+chr(26)))
    time.sleep(2)
    print("message sent")
    lcd.display("Message ", "Sent")    
    time.sleep(10)



def camera():
    net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3-tiny.cfg")
    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    cap = cv2.VideoCapture(0)

    font = cv2.FONT_HERSHEY_PLAIN
    frame_id = 0

    while True:
        ret, frame = cap.read()
        frame_id += 1
        height, width, channels = frame.shape
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.2:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    color = colors[class_id]
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(frame, classes[class_id], (x, y + 30), font, 2, (255, 255, 255), 2)
                    object_name = classes[class_id]
                    print(object_name)
                    lcd.display(f"{object_name} detected"," in feield")
                    
                    if object_name in animals:
                         play_audio("honey_bee.mp3",5)
                         print("animal detected")
                         img_name = "detected_animal.jpg"
                         cv2.imwrite(img_name, frame)
                         #smtp.send_email(img_name,object_name)
                         GPIO.output(relay,True)
                         sms(object_name)
                         time.sleep(0.2)

                    else:
                        GPIO.output(relay,False)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


    

    
def play_audio(file_name, duration):
    pygame.mixer.init()
    pygame.mixer.music.load(file_name)
    pygame.mixer.music.play()

    start_time = time.time()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

        # check if 5 seconds have passed
        if time.time() - start_time >= duration:
            break
while True:
    
    print("Intializing Camera")
    time.sleep(1)
    camera()

