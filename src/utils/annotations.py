import os
import sys
import cv2
import numpy as np
import open3d as o3d
import itertools
import transforms3d.quaternions as tfq
import transforms3d.affines as tfa
from utils.sparse_model import SparseModel

class Annotations:
    def __init__(self, dataset_dir_path, sparse_model_path, dense_model_path, scene_meta_path, visualize=False, drawCuboid=False):
        """
        Constructor for Annotations class.
        Input arguments:
        dataset_dir_path   - path to root dataset directory
        sparse_model_path  - path to sparse model (*.txt)
        dense_model_path   - path to dense model (*.ply)
        scene_meta_path    - path to scenes' meta info (*.npz)
        visualize          - set 'True' to visualize
        drawCuboid         - set 'True' to visualize 3D cuboid
        """
        self.dataset_path = dataset_dir_path
        self.input_array  = np.load(scene_meta_path)
        self.visualize    = visualize
        self.drawCuboid   = drawCuboid

        #read sparse model from input array
        sparse_model = SparseModel().reader(sparse_model_path)
        #read dense model from .PLY file
        dense_model = o3d.io.read_point_cloud(dense_model_path)
        dense_model = dense_model.voxel_down_sample(voxel_size=0.005)

        #read camera intrinsics matrix from camera.txt in root directory
        self.cam_mat = np.eye(3)
        with open(os.path.join(self.dataset_path, 'camera.txt'), 'r') as file:
            camera_intrinsics = file.readlines()[0].split()
            camera_intrinsics = list(map(float, camera_intrinsics))
        self.cam_mat[0,0] = camera_intrinsics[0]
        self.cam_mat[1,1] = camera_intrinsics[1]
        self.cam_mat[0,2] = camera_intrinsics[2]
        self.cam_mat[1,2] = camera_intrinsics[3]

        #get number of scenes and number of keypoints
        self.num_scenes = int(self.input_array['scenes'].shape[0]/7)
        self.num_keypts = sparse_model.shape[0]

        #paths to each of the scene dirs inside root dir
        self.list_of_scene_dirs = [d for d in os.listdir(self.dataset_path)
                                    if os.path.isdir(os.path.join(self.dataset_path, d))]
        self.list_of_scene_dirs.sort()
        self.list_of_scene_dirs = self.list_of_scene_dirs[:self.num_scenes]
        print("List of scenes: ", self.list_of_scene_dirs)
        print("Number of scenes: ", self.num_scenes)
        print("Number of keypoints: ", self.num_keypts)

        #excect images to be 640x480
        self.width = 640
        self.height = 480

        #bounding-box needs to scaled up to avoid excessive cropping
        self.bbox_scale = 1.5
        #define a ratio of labeled samples to produce
        self.ratio = 10

        #this is the object model
        self.object_model = [sparse_model, np.asarray(dense_model.points)]
        #these are the relative scene transformations
        self.scene_tfs = []

    def draw_axis(self, img, R, t, K):

        # How+to+draw+3D+Coordinate+Axes+with+OpenCV+for+face+pose+estimation%3f
        rotV, _ = cv2.Rodrigues(R)
        points = np.float32([[0, .1, 0], [.1, 0, 0], [0, 0, .1], [0, 0, 0]]).reshape(-1, 3)
        axisPoints, _ = cv2.projectPoints(points, rotV, t, K, (0, 0, 0, 0))
        img = cv2.line(img, tuple(axisPoints[3].ravel()), tuple(axisPoints[0].ravel()), (255,0,0), 3)
        img = cv2.line(img, tuple(axisPoints[3].ravel()), tuple(axisPoints[1].ravel()), (0,255,0), 3)
        img = cv2.line(img, tuple(axisPoints[3].ravel()), tuple(axisPoints[2].ravel()), (0,0,255), 3)
        return img

    def visualize_sample(self, cam_t, sample):
        """
        Visualize using opencv draw functions if self.visualize is set True.
        Input arguments:
        sample - labeled sample (RGB image, (keypoint, center pos, scale))
        """

        input_img = sample[0]
        keypts = sample[1][0]
        bbox_cn = sample[1][1]
        bbox_sd = sample[1][2]*200
        mask = sample[1][3]
        cenCuboid = sample[1][4]
        cuboid = sample[1][5]
        depth_img = sample[2]
        # cv2.imshow('depth', depth_img)

        #draw convex hull
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(input_img, contours, 0, (0, 69, 255), -1)

        #draw keypoints
        for point in keypts:
            cv2.circle(input_img, tuple(map(int, point)), 5, (0, 255, 255), -1)

        #draw cuboid center
        for center in cenCuboid:
            cv2.circle(input_img, tuple(map(int, center)), 10, (0, 0, 0), -1)

        # Draw 2D bounding-box
        try:
            x,y,w,h = cv2.boundingRect(contours[0])
            cv2.rectangle(input_img, (x,y), (x+w,y+h), (0, 69, 255), 2)
        except Exception as e:
            print("Unexpected error:", e)
            pass

        # Draw 3D bounding-box
        line_width = 2
        cuboid  = [tuple(map(int, point)) for point in cuboid]
        if self.drawCuboid:
            cv2.line(input_img, cuboid[0], cuboid[1], (255,255,255), line_width)
            cv2.line(input_img, cuboid[0], cuboid[2], (255,255,255), line_width)
            cv2.line(input_img, cuboid[0], cuboid[4], (255,255,255), line_width)
            cv2.line(input_img, cuboid[1], cuboid[3], (255,255,255), line_width)
            cv2.line(input_img, cuboid[1], cuboid[5], (255,255,255), line_width)
            cv2.line(input_img, cuboid[2], cuboid[3], (255,255,255), line_width)
            cv2.line(input_img, cuboid[2], cuboid[6], (255,255,255), line_width)
            cv2.line(input_img, cuboid[3], cuboid[7], (255,255,255), line_width)
            cv2.line(input_img, cuboid[4], cuboid[5], (255,255,255), line_width)
            cv2.line(input_img, cuboid[4], cuboid[6], (255,255,255), line_width)
            cv2.line(input_img, cuboid[5], cuboid[7], (255,255,255), line_width)
            cv2.line(input_img, cuboid[6], cuboid[7], (255,255,255), line_width)

            self.draw_axis(input_img, cam_t[:3, :3], cam_t[:3, 3], self.cam_mat)

        cv2.imshow('window', input_img)
        key = cv2.waitKey(500) & 0xFF
        if key == 27:
            sys.exit(1)

        return

    def project_points(self, input_points, input_pose):
        """
        Function to project the sparse object model onto the RGB image
        according to the provided pose of the object model in camera frame.
        Input arguments:
        input_points - [sparse object model, dense object model]
        input_pose   - pose of object model in camera frame
        Returns:
        (u, v) pos of all object keypoints, bounding box center and scaled side.
        """
        #project 3D sparse-model to 2D image plane
        rvec,_ = cv2.Rodrigues(input_pose[:3, :3])
        tvec = input_pose[:3,3]
        imgpts,_ = cv2.projectPoints(input_points[0], rvec, tvec, self.cam_mat, None)
        keypts = np.transpose(np.asarray(imgpts), (1,0,2))[0]

        #project 3D dense-model to 2D image plane
        imgpts,_ = cv2.projectPoints(input_points[1], rvec, tvec, self.cam_mat, None)
        objpts = np.transpose(np.asarray(imgpts), (1,0,2))[0]
        mask = np.zeros((self.height, self.width), dtype=np.uint8)
        for point in objpts:
            cv2.circle(mask, tuple(map(int, point)), 2, 255, -1)
        kernel = np.ones((5,5),np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(mask, contours, 0, 255, -1)
        x,y,w,h = cv2.boundingRect(contours[0])
        bbox = []
        bbox.append(x)
        bbox.append(y)
        bbox.append(w)
        bbox.append(h)

        #project the 3D bounding-box to 2D image plane
        min_point = np.min(input_points[1], axis=0)
        max_point = np.max(input_points[1], axis=0)
        min_max = [[a,b] for a,b in zip(min_point, max_point)] #[[x_min, x_max], [y_min, y_max], [z_min, z_max]]

        vertices = itertools.product(*min_max)
        vertices = np.asarray(list(vertices))
        cuboid = cv2.projectPoints(vertices, rvec, tvec, self.cam_mat, None)[0]
        cuboid = np.transpose(np.asarray(cuboid), (1,0,2))[0]

        cuboidCenter = (min_point + max_point)/2
        cuboidCenter = cv2.projectPoints(cuboidCenter, rvec, tvec, self.cam_mat, None)[0]
        cuboidCenter = np.transpose(np.asarray(cuboidCenter), (1,0,2))[0]
        # print('proj cuboidCenter', np.asarray(list(cuboidCenter)))

        #estimate a square box using mean and min-max in x- and y-
        bbox_cn = keypts.mean(0)
        xmin, ymin = keypts.min(0)
        xmax, ymax = keypts.max(0)
        if xmin<0: xmin=0
        if ymin<0: ymin=0
        if xmax>=(self.width-1):  xmax=(self.width-1)
        if ymax>=(self.height-1): ymax=(self.height-1)
        bbox_cn = ((xmax+xmin)/2, (ymax+ymin)/2)
        bbox_sd = max((xmax-xmin), (ymax-ymin))*self.bbox_scale

        return keypts, bbox_cn, bbox_sd/200.0, mask, cuboidCenter, cuboid, input_pose, bbox

    def process_input(self):
        """
        Function to extract data from the input array.
        Input array is the output of the optimization step
        which holds the generated sparse model of the object
        and the relative scene transformations.
        """
        #get the relative scene transforamtions from input array
        out_ts  = self.input_array['scenes'][ :(self.num_scenes)*3].reshape((self.num_scenes, 3))
        out_qs  = self.input_array['scenes'][(self.num_scenes)*3 : (self.num_scenes)*7].reshape((self.num_scenes, 4))
        out_tfs = np.asarray([tfa.compose(t, tfq.quat2mat(q), np.ones(3)) for t,q in zip(out_ts, out_qs)])
        self.scene_tfs = out_tfs
        return

    def generate_labels(self):
        """
        Main function to generate labels for RGB images according to provided input array.
        Returns a list of samples where each sample is tuple of the RGB image and the
        associated label, where each label is a tuple of the keypoints, center and scale.
        """
        samples = []
        #iterate through a zip of list of scene dirs and the relative scene tfs
        for data_dir_idx, (cur_scene_dir, sce_t) in enumerate(zip(self.list_of_scene_dirs, self.scene_tfs)):
            #read the names of image frames in this scene
            with open(os.path.join(self.dataset_path, cur_scene_dir, 'associations.txt'), 'r') as file:
                img_name_list = file.readlines()

            #read the camera pose corresponding to each frame
            with open(os.path.join(self.dataset_path, cur_scene_dir, 'camera.poses'), 'r') as file:
                cam_pose_list = [list(map(float, line.split()[1:])) for line in file.readlines()]

            #generate labels only for a fraction of total images in scene
            zipped_list = list(zip(img_name_list, cam_pose_list))[::self.ratio]
            for img_name, cam_pose in zipped_list:
                #read the RGB images using opencv
                img_name = img_name.split()
                rgb_im_path = os.path.join(self.dataset_path, cur_scene_dir, img_name[3])
                depth_im_path = os.path.join(self.dataset_path, cur_scene_dir, img_name[1])

                input_rgb_image = cv2.resize(cv2.imread(rgb_im_path), (self.width, self.height))
                input_depth_image = cv2.resize(cv2.imread(depth_im_path, cv2.IMREAD_ANYDEPTH), (self.width, self.height))
                # print('depth image shape', input_depth_image.shape)
                # cv2.imshow("depth image", input_depth_image)

                #compose 4x4 camera pose matrix
                cam_t = tfa.compose(np.asarray(cam_pose[:3]), tfq.quat2mat(np.asarray([cam_pose[-1]] + cam_pose[3:-1])), np.ones(3))

                #get 2D positions of keypoints, centers and scale of bounding box
                label = self.project_points(self.object_model, np.dot(np.linalg.inv(cam_t), sce_t))

                # append all necessary data into one list
                # if data_dir_idx	not in [5, 6]:
                samples.append((input_rgb_image, label, input_depth_image))

                #visualize if required
                if self.visualize:
                    self.visualize_sample(np.dot(np.linalg.inv(cam_t), sce_t), (input_rgb_image.copy(), label, input_depth_image.copy()))

            print("Created {} labeled samples from dataset {} (with {} raw samples).".format(len(zipped_list), data_dir_idx, len(img_name_list)))

        return samples
