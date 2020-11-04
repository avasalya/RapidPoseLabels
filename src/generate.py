import os
import argparse
import random as rand
from utils.sparse_model import SparseModel
from utils.annotations import Annotations
from utils.dataset_writer import DatasetWriter

def create_sets(trainTest, lower, upper):
    with open(trainTest, 'a') as f:
        for i in range(lower, upper):
            fileName = str(indices[randomList[i]])
            # print(fileName, '\n')
            f.write(fileName + '\n')
    print('saved...', trainTest)

if __name__ == '__main__':

    # get command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help='path to root dir of raw dataset')
    ap.add_argument("--sparse", required=True, help='path to sparse model file')
    ap.add_argument("--dense", required=True, help='path to dense model PLY file')
    ap.add_argument("--meta", required=True, help='path to saved_meta_data.npz file')
    ap.add_argument("--output", required=True, help='path to output directory')
    ap.add_argument("--visualize", action='store_true', help='to visualize each label')
    ap.add_argument("--drawCuboid", action='store_true', help='to drawCuboid on each label')
    opt = ap.parse_args()

    #set up Annotations
    label_generator = Annotations(opt.dataset, opt.sparse, opt.dense, opt.meta, opt.visualize, opt.drawCuboid)
    #extract useful information from input array
    label_generator.process_input()
    #generate labels and writes to output directory
    samples = label_generator.generate_labels()

    indices = []

    #write each sample to disk
    label_writer = DatasetWriter(opt.output)
    for counter, item in enumerate(samples):
        label_writer.write_to_disk(item, counter)
        indices.append(repr(counter).zfill(4))
        print("Saved sample: {}".format(repr(counter).zfill(5)), end="\r", flush=True)
    print("Total number of samples generated: {}".format(len(samples)))


    print('creating train and test sets with random order 80-20%')
    trainTxt = os.path.join(opt.output, 'train.txt')
    testTxt = os.path.join(opt.output, 'test.txt')

    #erase old files
    open(trainTxt, 'w').close()
    open(testTxt, 'w').close()

    #generate random samples
    N = len(samples)
    randomList = rand.sample(range(0, N), N)

    #train.txt/test.txt 80/20
    create_sets(trainTxt, 0, int(N*0.80))
    create_sets(testTxt, int(N*0.80), N)

