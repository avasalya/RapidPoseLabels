#!/bin/bash


###############################
### to save in same folder
###############################


# counter=1
echo -n "Enter starting number: "
read count
counter=$count
echo -n "files will be renamed starting from:"
echo $counter



###############################
#        .txt files           #
###############################


# mkdir -p labels
# for file in `\find . -maxdepth 1 -mindepth 1 -type f | sort`; do

#     if [[ $file = *.txt ]]; then
#         echo $file
#         cp $file ./labels/"$counter".txt
#         counter=`expr $counter + 1`
#     fi
# done



###############################
#        .png files           #
###############################

mkdir -p rgb
# mkdir -p mask
# mkdir -p depth

for file in `\find . -maxdepth 1 -mindepth 1 -type f | sort`; do

    if [[ $file = *.png ]]; then
        echo $file
        cp $file ./rgb/"$counter".png
        counter=`expr $counter + 1`
    fi
done