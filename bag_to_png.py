""" usage """

"""
Python2.7 bag_to_png.py --out pngfiles2 --rgb /camera/color/image_raw  --dep /camera/aligned_depth_to_color/image_raw --bag rosbagfiles/2020-10-20-13-29-58.bag


"""
import argparse
import os
import sys
import cv2
import matplotlib.pyplot as plt
import numpy as np
from cv_bridge import CvBridge, CvBridgeError
sys.path.append("/usr/lib/python2.7/dist-packages/")
import rospy
import rosbag
from sensor_msgs.msg import Image

cv_bridge = CvBridge()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help = "name of output directory (will be created if not exist)")
    parser.add_argument("--rgb", required=True, help = "name of ROS topic for RGB images")
    parser.add_argument("--dep", required=True, help = "name of ROS topic for Depth images")
    parser.add_argument("--bag", required=True, help = "path to bag file")
    args = vars(parser.parse_args())

    out_dir   = args["out"]
    rgb_topic = args["rgb"]
    dep_topic = args["dep"]
    bag_file  = args["bag"]

    out_rgb_dir = os.path.join(out_dir, "rgb")
    out_dep_dir = os.path.join(out_dir, "depth")
    if not os.path.isdir(out_rgb_dir):
        os.makedirs(out_rgb_dir)
    if not os.path.isdir(out_dep_dir):
        os.makedirs(out_dep_dir)

    if not os.path.exists(bag_file):
        print("couldn't find bag file. check path")
        sys.exit(-1)

    bag = rosbag.Bag(bag_file)
    topics = bag.get_type_and_topic_info()[1].keys()

    #cv2.namedWindow(rgb_topic)
    #cv2.namedWindow(dep_topic)
    rgb_file = open(os.path.join(out_dir, 'rgb.txt'), 'w')
    dep_file = open(os.path.join(out_dir, 'depth.txt'), 'w')
    for topic, msg, t in bag.read_messages(topics=[rgb_topic, dep_topic]):
        fn = format(((rospy.rostime.Time.to_nsec(t)/1e9) - 1580300000), '.6f')
        try:
            if topic==rgb_topic:
                cvimg = cv_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                out_fn = os.path.join(out_rgb_dir, fn + '.png')
                rgb_file.write(fn + ' ' + 'rgb/' + fn + '.png' + '\n')
                #print "RGB: ", fn, cvimg.max(), type(cvimg), cvimg.dtype
            elif topic==dep_topic:
                cvimg = cv_bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
                #cvimg = cvimg.copy()*1000.0                # uncomment this only for astra
                #cvimg = cvimg.astype(np.uint16)            # uncomment this only for astra
                out_fn = os.path.join(out_dep_dir, fn + '.png')
                dep_file.write(fn + ' ' + 'depth/' + fn + '.png' + '\n')
                #print "Depth: ", fn, cvimg.min(), cvimg.max(), type(cvimg), cvimg.dtype, cvimg.shape

            #cv2.imshow(topic, cvimg)
            cv2.imwrite(out_fn, cvimg)
            #cv2.waitKey(10)
        except CvBridgeError, e: print e
    rgb_file.close()
    dep_file.close()
    bag.close()