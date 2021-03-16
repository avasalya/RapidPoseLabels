import os
import yaml
import cv2
import numpy as np


class DatasetWriter:

    def __init__(self, output_dir):
        """
        Constructor for Writer class.
        Input arguments:
        output_dir - path to output directory
        """
        self.output_dir = output_dir
        #create sub-directories if they dont exist
        for dir_name in ["bboxes", "center", "scale", "keypoint", "rgb", "mask", "depth", "labels"]:
            if not os.path.isdir(os.path.join(self.output_dir, dir_name)):
                os.makedirs(os.path.join(self.output_dir, dir_name))

        self.gtyml = os.path.join(self.output_dir, 'gt.yml')
        # erase old file
        open(self.gtyml, 'w').close()

    def write_to_disk(self, sample, index):
        """
        Function to write the generated sample (keypoint, center, scale, mask and the RGB image)
        in a format as expected by the ObjectKeypointTrainer training module
        (https://github.com/rohanpsingh/ObjectKeypointTrainer#preparing-the-dataset).
        Bounding-boxes are saved in the format as expected by darknet-yolov3
        (https://github.com/AlexeyAB/darknet#how-to-train-to-detect-your-custom-objects).
        Input arguments:
        sample - labeled sample (RGB image, (keypoint, center pos, scale, mask))
        index  - counter for naming images
        """
        rgb_image   = sample[0]
        kpt_label   = sample[1][0]
        cen_label   = sample[1][1]
        sca_label   = sample[1][2]
        mask_label  = sample[1][3]
        cent_cuboid = sample[1][4]
        proj_cuboid = sample[1][5]
        pred_pose   = sample[1][6]
        bbox        = sample[1][7]
        yoloBox     = sample[1][8]
        depth_image = sample[2]

        # print('writer depth_image shape', depth_image.shape)

        ymlLabel = []
        txtLabel = []
        yolotxtLabel = []

        height = rgb_image.shape[0] #480
        width  = rgb_image.shape[1] #640

        #write bounding box for yolo
        bboxfile = open(os.path.join(self.output_dir, 'bboxes', repr(index).zfill(4) + '.txt'), 'w')
        bboxfile.write('0\t' + repr(cen_label[0]/width) + '\t' + repr(cen_label[1]/height) + '\t' +
                        repr(sca_label*200/width) + '\t' + repr(sca_label*200/height) + '\n')
        bboxfile.close()

        #write center to center/center_0####.txt
        centerfile = os.path.join(self.output_dir, 'center', repr(index).zfill(4) + '.txt')
        np.savetxt(centerfile, cen_label)

        #write scale to scale/scales_0####.txt
        scalesfile = os.path.join(self.output_dir, 'scale', repr(index).zfill(4) + '.txt')
        np.savetxt(scalesfile, np.asarray([sca_label]))

        #write keypoints to label/label_0####.txt
        labelfile = os.path.join(self.output_dir, 'keypoint', repr(index).zfill(4) + '.txt')
        np.savetxt(labelfile, kpt_label)

        #write RGB image to frames/frame_0####.txt
        cv2.imwrite(os.path.join(self.output_dir, 'rgb', repr(index).zfill(4) + '.png'), rgb_image)

        #write mask label to masks/mask_0####.txt
        cv2.imwrite(os.path.join(self.output_dir, 'mask', repr(index).zfill(4) + '.png'), mask_label)

        #write Depth image to frames/frame_0####.txt
        cv2.imwrite(os.path.join(self.output_dir, 'depth', repr(index).zfill(4) + '.png'), depth_image)

        """ linemod .yml """
        rotation = pred_pose[:3, :3]
        translation = pred_pose[:3, 3]
        ymlLabel.append({
            'cam_R_m2c':rotation.flatten().tolist(),
            'cam_t_m2c':translation.flatten().tolist(),
            'obj_bb': bbox,
            'obj_id': 1 #class
        })

        out = {index : ymlLabel}
        with open(self.gtyml, 'a') as f:
            yaml.dump(out, f, default_flow_style=None)

        """ linemod .txt """
        #class
        txtLabel.append(0)

        #centeroid
        txtLabel.append(cent_cuboid[0,0]/width)
        txtLabel.append(cent_cuboid[0,1]/height)

        #vertices
        for point in range(len(proj_cuboid)):
            txtLabel.append(proj_cuboid[point,0]/width)
            txtLabel.append(proj_cuboid[point,1]/height)

        # xlim, ylim
        txtLabel.append(bbox[2]/width)
        txtLabel.append(bbox[3]/height)

        gttxt = open(os.path.join(self.output_dir, 'labels', repr(index).zfill(4) + '.txt'), 'w')
        for label in range(len(txtLabel)):
            gttxt.write(str(txtLabel[label]))
            if label < len(txtLabel) -1:
                gttxt.write(' ')
        gttxt.close()

        """ yolov4 .txt """
        image_path = repr(index).zfill(4)
        yolotxtLabel.append(image_path)
        for e in yoloBox:
            yolotxtLabel.append(e)

        yolotxt  = open(os.path.join(self.output_dir, 'yoloData.txt'), 'a')
        for label in range(len(yolotxtLabel)):
            yolotxt.write(str(yolotxtLabel[label]))
            if label < len(yolotxtLabel) -1:
                yolotxt.write(' ')
        yolotxt.write('\n')
        yolotxt.close()

        return

