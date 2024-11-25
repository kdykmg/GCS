import cv2
import os

path=os.path.dirname(__file__)
path=path+''
os.chdir(path)

img = cv2.imread('key_imgs/arm_release.png')
color= img[10,10,:]
print(color)
img[:,:,:]=color
cv2.imshow('',img)
cv2.waitKey(0)