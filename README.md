




# Automated Data Annotation for 6-DoF Object Pose Estimation

This is a tool for rapid generation of labeled training dataset primarily for the purpose of training keypoint detector networks for full pose estimation of a rigid, non-articulated 3D object in RGB images. The code is based on our paper: *Rapid Pose Label Generation through Sparse Representation of Unknown Objects*, [Rohan P. Singh](https://github.com/rohanpsingh), [Mehdi Benallegue](https://github.com/mehdi-benallegue), Yusuke Yoshiyasu, Fumio Kanehiro. [under-review]


We provide a very (arguably) user-friendly GUI to fetch minimal user input (where minimal = **few** clicks on **one** image per **scene**). Using the given software, we have been able to generate large, accurately--labeled, training datasets consisting of multiple objects in different scenes (environments with varying background conditions, illuminations, clutter etc.) using just a handheld RGB-D sensor in only a few hours, including the time involved in capturing the raw dataset. And ultimately, used the training dataset for training a bounding-box detector ([YOLOv3](https://github.com/AlexeyAB/darknet)) and a keypoint detector network ([ObjectKeypointTrainer](https://github.com/rohanpsingh/ObjectKeypointTrainer)).

The code in this repository forms Part-1 of the full software:
![pose-estimation-github](https://user-images.githubusercontent.com/16384313/84745705-ec04bf00-afef-11ea-9966-c88f24c9a3ba.png)

Links to other parts:
- Part-2: [ObjectKeypointTrainer](https://github.com/rohanpsingh/ObjectKeypointTrainer)
- Part-3: Not-yet-available

## Dependencies

All or several parts of the given Python 3.7.4 code are dependent on the following:
- OpenCV
- [open3d](http://www.open3d.org/docs/release/getting_started.html)
- [transforms3d](https://matthew-brett.github.io/transforms3d)

We recommend satisfying above dependencies to be able to use all scripts, though it should be possible to bypass some requirements depending to the use case. We recommend working in a [conda](https://docs.conda.io/en/latest/) environment.
### Other dependencies
For pre-processing of the raw dataset (extracting frames if you have a ROS bagfile and for dense 3D reconstruction) we rely on the following applications:
1. [bag-to-png](https://gist.github.com/rohanpsingh/9ac99c46aef8ccb618cdad18cd20e068)
2. [png-to-klg](https://github.com/HTLife/png_to_klg)
3. [ElasticFusion](https://github.com/mp3guy/ElasticFusion)

## Usage
### Preparing the dataset(s)
We assume that using [bag-to-png](https://gist.github.com/rohanpsingh/9ac99c46aef8ccb618cdad18cd20e068), [png-to-klg](https://github.com/HTLife/png_to_klg) and [ElasticFusion](https://github.com/mp3guy/ElasticFusion), the user is able to generate a dataset directory tree which looks like follows:
```
dataset_dir/
├── wrench_tool_data/
│   ├── 00/
│	│	├── 00.klg
│	│	├── 00.ply
│	│	├── associations.txt
│	│	├── camera.poses
│	│	├── depth.txt
│	│	├── rgb.txt
│	│	├── rgb/
│	│	└── depth/
│   ├── 01/
│   ├── 02/
│   ├── 03/
│   └── 04/
├── object_1_data/...
└── object_2_data/...
```
where ```camera.poses``` and ```00.ply``` are the camera trajectory and the dense scene generated by ElasticFusion respectively. Ideally, the user has collected raw dataset for different scenes/environments in directories ```00, 01, 02,...``` .


The program does not require any known CAD model (or any kind of object model). To generate labels for rgb-depth frame pair in each scene and/or to generate a sparse, keypoint-based representation of the object model:
```
$ python main.py --dataset <path-to-dataset-dir> --keypoints <number-of-keypoints-to-be>
```
This should bring up the main GUI:
<p align="center">
<img src="https://user-images.githubusercontent.com/16384313/84734452-d5ed0380-afdb-11ea-88e8-cddb0b01c312.png" alt="GUI" width="80%">
<p>

### When object model is NOT available
1. Click on "Create a new model".
2. Click on "Load New Image" and manually label all keypoints decided on the object which are visible.
3. Click on "Skip KeyPt" if keypoint is not visible. (**Keypoint labeling is order sensitive**)
4. To shuffle, click on "Load New Image" again.
5. Click on "Next Scene" when finished.
6. Repeat for each scene.
7. Click on "Compute"

If manual label was done maintaining the constraints described in the paper, the optimization step should succeed and produce a ```sparse_model.txt``` and ```saved_meta_data.npz``` in the output directory. The ```saved_meta_data.npz``` archive holds data of relative scene transformations and the manually clicked points with their IDs (important for generating the actual labels using ```generate.py``` and evaluation with respect to ground-truth, if available).

###  When object model is available
Once ```sparse_model.txt``` has been generated for a particular object, the user might want to reuse the same model for generating labels for a new scene (let's say directory ```05```) . This would require the user to only click on 4-5 points on one RGB image per scene and directly obtain the new labels.

1. Launch the GUI
2. Click on "Use existing model"
3. Choose a previously generated ```sparse_model.txt```. (A Meshlab *.pp file can also be used in this step, if a CAD model is available)
4. Follow the same procedure as before.

Clicking on "Compute" tries to solve an orthogonal Procrustes problem on the given manual clicks and in input sparse model file. This will generate the  ```saved_meta_data.npz``` again for the given scenes, which can be with the ```generate.py``` script to generate the labels.

### To generate labels on raw images
```
$ python generate.py --input <path-to-saved-meta-data-npz> --model <path-to-sparse-model-txt> --dataset <path-to-dataset-dir> --output <path-to-output-directory>
```
That is it. This should be enough to generate training dataset for stacked-hourglass-training as described in [ObjectKeypointTrainer](https://github.com/rohanpsingh/ObjectKeypointTrainer) and also bounding-box labels for training a generic object detector.

### To define a Grasp Point
The GUI can be used to define a 4x4 affine transformation from the origin of the sparse model to a grasp point, as desirable.
1. Launch the GUI (no need for ```--keypoint``` argument this time)
2. Select "Define grasp point"
3. Browse to the sparse model file.
4. Load an image from the ```00``` scene, and click on 2 points.

The first clicked point defines the position of grasp point and the second point decides the orientation.
TODO: Currently, this works only if user defines grasp point in the "first scene". This is because the sparse object model is defined with respect to "first viewpoint" in "first scene". Ideally, the user should be able to load any scene's PLY and define the grasp point in an interactive 3D environment.
TODO: Grasp point orientation is sometimes affected by noise in scene point cloud.


## Potential Issues
- Tested only with all raw images in 640x480 resolution.
- Grasp point selection should, ideally, be done in an interactive 3D environment.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
