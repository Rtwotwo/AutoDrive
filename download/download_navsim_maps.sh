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


# --------------------------------------------------------------------------
# 1.Download maps Datasets 
# --------------------------------------------------------------------------
wget https://motional-nuplan.s3-ap-northeast-1.amazonaws.com/public/nuplan-v1.1/nuplan-maps-v1.1.zip
unzip nuplan-maps-v1.1.zip
rm nuplan-maps-v1.1.zip
mv nuplan-maps-v1.1 maps
 