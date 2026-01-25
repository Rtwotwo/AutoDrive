# !/bin/bash
# Download the OpenScene v1.1 dataset using modelscope CLI
# The OpenScene dataset is hosted on ModelScope Datasets about 1.9TB in total
# dataset
# ├── openscene-v1.0 (optional)
# |   ├── occupancy (optional)
# └── openscene-v1.1
#     ├── meta_datas
#     |     ├── mini
#     │     │     ├── 2021.05.12.22.00.38_veh-35_01008_01518.pkl
#     │     │     ├── 2021.05.12.22.28.35_veh-35_00620_01164.pkl
#     │     │     ├── ...
#     │     │     └── 2021.10.11.08.31.07_veh-50_01750_01948.pkl
#     |     ├── trainval
#     |     └── test
#     |     
#     └── sensor_blobs
#             ├── mini
#             │    ├── 2021.05.12.22.00.38_veh-35_01008_01518                                           
#             │    │    ├── CAM_F0
#             │    │    │     ├── c082c104b7ac5a71.jpg
#             │    │    │     ├── af380db4b4ca5d63.jpg
#             │    │    │     ├── ...
#             │    │    │     └── 2270fccfb44858b3.jpg
#             │    │    ├── CAM_B0
#             │    │    ├── CAM_L0
#             │    │    ├── CAM_L1
#             │    │    ├── CAM_L2
#             │    │    ├── CAM_R0
#             │    │    ├── CAM_R1
#             │    │    ├── CAM_R2
#             │    │    └── MergedPointCloud
#             │    │            ├── 0079e06969ed5625.pcd
#             │    │            ├── 01817973fa0957d5.pcd
#             │    │            ├── ...
#             │    │            └── fffb7c8e89cd54a5.pcd       
#             │    ├── 2021.06.09.17.23.18_veh-38_00773_01140 
#             │    ├── ...                                                                            
#             │    └── 2021.10.11.08.31.07_veh-50_01750_01948
#             ├── trainval
#             └── test


REPO_DIR=OpenDriveLab/OpenScene
LOCAL_DIR=/data/alg-model-datavol-0/xinyao/


# --------------------------------------------------------
# 2.download openscene-v1.1 private_test dataset
# --------------------------------------------------------
modelscope download --dataset $REPO_DIR openscene-v1.1/openscene_metadata_private_test_e2e.tgz --local_dir $LOCAL_DIR
tar -zxf $LOCAL_DIR/openscene-v1.1/openscene_metadata_private_test_e2e.tgz
rm $LOCAL_DIR/openscene-v1.1/openscene_metadata_private_test_e2e.tgz
modelscope download --dataset $REPO_DIR openscene-v1.1/openscene_sensor_private_test_e2e.tgz --local_dir $LOCAL_DIR
tar -zxf $LOCAL_DIR/openscene-v1.1/openscene_sensor_private_test_e2e.tgz
rm $LOCAL_DIR/openscene-v1.1/openscene_sensor_private_test_e2e.tgz

modelscope download --dataset $REPO_DIR openscene-v1.1/openscene_metadata_private_test_hard.tar.gz --local_dir $LOCAL_DIR
tar -zxf $LOCAL_DIR/openscene-v1.1/openscene_metadata_private_test_hard.tar.gz
rm $LOCAL_DIR/openscene-v1.1/openscene_metadata_private_test_hard.tar.gz
modelscope download --dataset $REPO_DIR openscene-v1.1/openscene_sensor_private_test_hard.tar.gz --local_dir $LOCAL_DIR
tar -zxf $LOCAL_DIR/openscene-v1.1/openscene_sensor_private_test_hard.tar.gz
rm $LOCAL_DIR/openscene-v1.1/openscene_sensor_private_test_hard.tar.gz

modelscope download --dataset $REPO_DIR openscene-v1.1/openscene_metadata_private_test_wm.tgz --local_dir $LOCAL_DIR
tar -zxf $LOCAL_DIR/openscene-v1.1/openscene_metadata_private_test_wm.tgz
rm $LOCAL_DIR/openscene-v1.1/openscene_metadata_private_test_wm.tgz
modelscope download --dataset $REPO_DIR openscene-v1.1/openscene_sensor_private_test_wm.tgz --local_dir $LOCAL_DIR
tar -zxf $LOCAL_DIR/openscene-v1.1/openscene_sensor_private_test_wm.tgz
rm $LOCAL_DIR/openscene-v1.1/openscene_sensor_private_test_wm.tgz