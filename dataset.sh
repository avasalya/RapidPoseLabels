#!/bin/bash
# set -e
# Any subsequent(*) commands which fail will cause the shell script to exit immediately

# to record rosbag using realsense D435
# rosbag record /camera/aligned_depth_to_color/image_raw /camera/color/image_raw --duration=1m

# to run this file
# ./dataset.sh or
# bash -e dataset.sh

# path to scene(s) data directory
rpl="RapidPoseLabels"
dataDir="data/onigiri"


echo "---this script assumes you have fullfilled all the requirements and following folders exists in your $HOME directory"
echo "---rosbagfiles/, which contains all the *.bag files"
echo "---pngtoklg/, assumes you have complied it correctly and 'pngtoklg' file exist within build folder"
echo "---ElasticFusion/, compiled and build correctly"
echo "---that you have created conda environment named 'rpl' using conda env create -f environment.yml, if not please do so right now.."
echo " "
echo "---Also following files exists in your $HOME/$rpl directory 'camera.txt', dense.ply, sparse_model.pp (meshlab file), bag_to_png.py"


while true; do
    echo " "
    read -p "Do you wish to continue [Y/n]?" yn
    read -p "Do you want to overwrite previous dataset in $HOME$rpl/data/txonigiri [Y/n]?" yn
    echo " "
    case $yn in
        [Yy]* )
            echo "activating conda environment"
            source ~/anaconda3/etc/profile.d/conda.sh
            conda activate rpl
            echo " "
            echo "copying bag_to_png.py to $HOME/rosbagfiles"
            cp bag_to_png.py $HOME/rosbagfiles
            break;;

        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done


echo "found following rosbag files in the directory '$HOME/rosbagfiles'"
cd $HOME/rosbagfiles
ls *.bag
echo "renaming .bag files as 01, 02, 03 ..."
a=0
for i in *.bag; do
    new=$(printf "%02d.bag" "$a")
    mv -i -- "$i" "$new"
    let a=a+1
done
echo " "

echo "converting rosbag files to png "
for b in *.bag; do
    echo "converting $b file"
    python2.7 bag_to_png.py --out ${b%%.*} --rgb /camera/color/image_raw  --dep /camera/aligned_depth_to_color/image_raw --bag $b;
done
echo " "


echo "moving all converted folders, in this case to $HOME/$rpl/$dataDir"
for d in */; do
    rm -rf $HOME/$rpl/$dataDir/$d #delete old folder if any
    echo "moving folder $d to $HOME/$rpl/$dataDir"
    mv $d $HOME/$rpl/$dataDir
done
echo " "


echo "converting .png to .klg format"
echo "creating associations.txt for each scene(s)"
cd $HOME/$rpl/$dataDir
for d in */; do
    echo "now working with $d scene"
    python2.7 $HOME/png_to_klg/associate.py $d/depth.txt $d/rgb.txt > $d/associations.txt
    $HOME/png_to_klg/build/pngtoklg -w $HOME/$rpl/$dataDir/$d -o ${d%%/*}.klg -s 1000
    echo " "
done
echo " "


echo "copying camera.txt to $dataDir"
cp $HOME/$rpl/camera.txt $HOME/$rpl/$dataDir
echo " "


echo "Time to run ElasticFusion on each scene(s)"
echo " "
echo "when rendering is completed!!, Please save and close GUI manually for each scene"
for d in */; do
    echo "now in scene $d"
    /.$HOME/ElasticFusion/GUI/build/ElasticFusion -f -l $d${d%%/*}.klg -cal $HOME/$rpl/camera.txt
done
echo " "


echo "renaming .ply and .freiburg files"
for d in */; do
    mv $d${d%%/*}.klg.ply  $d${d%%/*}.ply
    mv $d${d%%/*}.klg.freiburg  $d/camera.poses
done
echo " "


cd $HOME/$rpl/
keypoints=5
echo "Run RPL with $keypoints keypoints to create model or use existing model and create .npz file"
python3 $HOME/$rpl/src/main.py --dataset $HOME/$rpl/$dataDir/ --keypoints $keypoints
echo " "


latest_outDir=$(ls -td */ | head -1)
echo "Copying dense.ply and sparse_model.pp to $HOME/$rpl/$latest_outDir"
cp sparse_model.pp $HOME/$rpl/$latest_outDir
cp dense-tex.ply $HOME/$rpl/$latest_outDir
cp dense-tex.jpg $HOME/$rpl/$latest_outDir
echo " "


echo "Finally generate dataset and labels"
python3  $HOME/$rpl/src/generate.py  --dataset $dataDir  --sparse $latest_outDir/sparse_model.pp --dense $latest_outDir/dense-tex.ply  --meta $latest_outDir/saved_meta_data.npz --output $latest_outDir/  --visualize --drawCuboid
echo " "


echo "If all above steps worked without any 'error', that means you have successfully generated labels at $HOME/$rpl/$latest_outDir"