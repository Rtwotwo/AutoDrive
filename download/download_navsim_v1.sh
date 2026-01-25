# !/bin/bash
# Download the NavSim datasets using modelscope CLI
# The NavSim datasets are hosted on ModelScope Datasets about 500G in total
# ~/navsim_workspace
# ├── navsim (containing the devkit)
# ├── exp
# └── dataset
#     ├── maps
#     ├── navsim_logs
#     |    ├── test
#     |    ├── trainval
#     |    ├── private_test_hard
#     |    |         └── private_test_hard.pkl
#     │    └── mini
#     └── sensor_blobs
#     |    ├── test
#     |    ├── trainval
#     |    ├── private_test_hard
#     |    |         ├──  CAM_B0
#     |    |         ├──  CAM_F0
#     |    |         ├──   ...
#     |    └── mini
#     └── navhard_two_stage
#     |    ├── openscene_meta_datas
#     |    ├── sensor_blobs
#     |    ├── synthetic_scene_pickles
#     |    └── synthetic_scenes_attributes.csv
#     └── warmup_two_stage
#     |    ├── openscene_meta_datas
#     |    ├── sensor_blobs
#     |    ├── synthetic_scene_pickles
#     |    └── synthetic_scenes_attributes.csv
#     └── private_test_hard_two_stage
#          ├── openscene_meta_datas
#          └── sensor_blobs


REPO_DIR=OpenDriveLab/OpenScene
LOCAL_DIR=/data/alg-model-datavol-0/xinyao/navsim


# --------------------------------------------------------------------------
# 2.Download Navsim-v1 Datasets for building navtrain and navtest datatest
# --------------------------------------------------------------------------
for i in {1..32};do
    # download the navtrain current data and unpack the tar file
    modelscope download --dataset $REPO_DIR navsim/navtrain_current_$i.tgz --local_dir $LOCAL_DIR
    tar -zxf $LOCAL_DIR/navsim/navtrain_current_$i.tgz -C $LOCAL_DIR/navsim
    rm $LOCAL_DIR/navsim/navtrain_current_$i.tgz
    echo "[INFO] Moving navtrain_current_$i data..."
    rsync -r $LOCAL_DIR/navsim/navtrain_current_$i/* $LOCAL_DIR/sensor_blobs/mytest
    
    # download the navtrain history data and unpack the tar file
    modelscope download --dataset $REPO_DIR navsim/navtrain_history_$i.tgz --local_dir $LOCAL_DIR
    tar -zxf $LOCAL_DIR/navsim/navtrain_history_$i.tgz -C $LOCAL_DIR/navsim
    rm $LOCAL_DIR/navsim/navtrain_history_$i.tgz
    echo "[INFO] Moving navtrain_history_$i data..."
    rsync -r $LOCAL_DIR/navsim/navtrain_history_$i/* $LOCAL_DIR/sensor_blobs/mytest
done