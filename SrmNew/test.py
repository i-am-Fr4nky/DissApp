# from SrmNew.srm import SRM
from SrmNew.srm2 import SRM
import cv2
import datetime

imgPath = '/home/ange/Dropbox/Изображения/c3po.jpg'
img = cv2.imread(imgPath, 3)

# cv2.imshow("Test", img)
# cv2.waitKey()



#
#
# # pixel array in img



print('print srm at {0}'.format(datetime.datetime.now().time()))

srm = SRM(img)
segmented = srm.run()

print('end srm at {0}'.format(datetime.datetime.now().time()))

print('end')
cv2.imshow("Origin", img)
cv2.imshow("Result", segmented)
cv2.waitKey()

cv2.imwrite('/home/ange/Desktop/cv_experiments/Python/c3po.png', segmented)


