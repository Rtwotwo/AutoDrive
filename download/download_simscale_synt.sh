# !/bin/bash
# Download SimScale synthetic data from ModelScope
# navsim_workspace/
# ├── simscale/
# ├── exp/
# └── dataset/
#     ├── maps/
#     ├── navsim_logs/
#     │   ├── test/
#     │   ├── trainval/
#     │   ├── synthetic_reaction_pdm_v1.0-*/
#     │   │   ├── [log]-00*.pkl
#     │   │   └── ...
#     │   └── synthetic_reaction_recovery_v1.0-*/
#     ├── sensor_blobs/
#     │   ├── test/
#     │   ├── trainval/
#     │   ├── synthetic_reaction_pdm_v1.0-*/
#     │   │   └── [token]-00*/
#     │   │       ├── CAM_B0/
#     │   │       └── ...
#     │   └── synthetic_reaction_recovery_v1.0-*/
#     └── navhard_two_stage/


repo=OpenDriveLab/SimScale
local_dir=/data/alg-model-datavol-0/xinyao/navsim/simscale

# ------------------------------------------------------------
# 1. simulation data with planner-based pseudo-expert
# ------------------------------------------------------------
rounds=5
splits=(66 56 47 39 33)
for round in $(seq 0 $((rounds - 1))); do
    # 1. meta data
    modelscope download --dataset ${repo} SimScale_data/synthetic_reaction_pdm_v1.0-${round}/simscale_pdm_v1.0-${round}_meta_datas.tar.gz --local_dir ${local_dir}/
    echo "[Planner-based] Downloaded meta data for round ${round}"
    tar -xzf ${local_dir}/SimScale_data/synthetic_reaction_pdm_v1.0-${round}/simscale_pdm_v1.0-${round}_meta_datas.tar.gz  -C ${local_dir}
    rm ${local_dir}/SimScale_data/synthetic_reaction_pdm_v1.0-${round}/simscale_pdm_v1.0-${round}_meta_datas.tar.gz
 
    # 2. hist sensor data
    split=${splits[$round]}
    echo "[INFO] Downloading hist sensor data for split ${split}"
    for idx in $(seq 0 $((split - 1))); do
        echo "[INFO] date now is $(date)"
        echo "[Planner-based] Downloaded hist sensor data ${idx} for round ${round}"
        modelscope download --dataset ${repo} SimScale_data/synthetic_reaction_pdm_v1.0-${round}/simscale_pdm_v1.0-${round}_sensor_blobs_hist/simscale_pdm_v1.0-${round}_sensor_blobs_hist_${idx}.tar.gz --local_dir ${local_dir}/
        tar -xzf ${local_dir}/SimScale_data/synthetic_reaction_pdm_v1.0-${round}/simscale_pdm_v1.0-0_sensor_blobs_hist/simscale_pdm_v1.0-${round}_sensor_blobs_hist_${idx}.tar.gz  -C ${local_dir}
        rm ${local_dir}/SimScale_data/synthetic_reaction_pdm_v1.0-${round}/simscale_pdm_v1.0-0_sensor_blobs_hist/simscale_pdm_v1.0-${round}_sensor_blobs_hist_${idx}.tar.gz
    done

    # 3. future sensor data (OPTIONAL)
    split=${splits[$round]}
    for idx in $(seq 0 $((split - 1))); do
        modelscope download --dataset ${repo} SimScale_data/synthetic_reaction_pdm_v1.0-${round}/simscale_pdm_v1.0-${round}_sensor_blobs_fut/simscale_pdm_v1.0-${round}_sensor_blobs_fut_${idx}.tar.gz  --local_dir ./
        echo "[Planner-based] Downloaded fut sensor data ${idx} for round ${round}"
        tar -xzvf simscale_pdm_v1.0-${round}_sensor_blobs_fut_${idx}.tar.gz
        rm simscale_pdm_v1.0-${round}_sensor_blobs_fut_${idx}.tar.gz
    done
done


# ------------------------------------------------------------
# 2. simulation data with recovery-based pseudo-expert
# ------------------------------------------------------------
rounds=5
splits=(45 36 28 22 17)
for round in $(seq 0 $((rounds - 1))); do
    # 1. meta data
    modelscope download --dataset ${repo} SimScale_data/synthetic_reaction_recovery_v1.0-${round}/simscale_recovery_v1.0-${round}_meta_datas.tar.gz --local_dir ${local_dir}/
    echo "[Recovery-based] Downloaded meta data for round ${round}"
    tar -xzf ${local_dir}/SimScale_data/synthetic_reaction_recovery_v1.0-${round}/simscale_recovery_v1.0-${round}_meta_datas.tar.gz -C ${local_dir}
    rm ${local_dir}/SimScale_data/synthetic_reaction_recovery_v1.0-${round}/simscale_recovery_v1.0-${round}_meta_datas.tar.gz
 
    # 2. hist sensor data
    split=${splits[$round]}
    echo "Downloading hist sensor data for split ${split}"
    for idx in $(seq 0 $((split - 1))); do
        echo "[INFO] date now is $(date)"
        echo "[Recovery-based] Downloaded hist sensor data ${idx} for round ${round}"
        modelscope download --dataset ${repo} SimScale_data/synthetic_reaction_recovery_v1.0-${round}/simscale_recovery_v1.0-${round}_sensor_blobs_hist/simscale_recovery_v1.0-${round}_sensor_blobs_hist_${idx}.tar.gz --local_dir ${local_dir}/
        tar -xzf ${local_dir}/SimScale_data/synthetic_reaction_recovery_v1.0-${round}/simscale_recovery_v1.0-0_sensor_blobs_hist/simscale_recovery_v1.0-${round}_sensor_blobs_hist_${idx}.tar.gz  -C ${local_dir}
        rm ${local_dir}/SimScale_data/synthetic_reaction_recovery_v1.0-${round}/simscale_recovery_v1.0-0_sensor_blobs_hist/simscale_recovery_v1.0-${round}_sensor_blobs_hist_${idx}.tar.gz
    done

    # 3. future sensor data (OPTIONAL)
    split=${splits[$round]}
    for idx in $(seq 0 $((split - 1))); do
        modelscope download --dataset ${repo} SimScale_data/synthetic_reaction_recovery_v1.0-${round}/simscale_recovery_v1.0-${round}_sensor_blobs_fut/simscale_recovery_v1.0-${round}_sensor_blobs_fut_${idx}.tar.gz --local_dir ./
        echo "[Recovery-based] Downloaded fut sensor data ${idx} for round ${round}"
        tar -xzvf simscale_recovery_v1.0-${round}_sensor_blobs_fut_${idx}.tar.gz
        rm simscale_recovery_v1.0-${round}_sensor_blobs_fut_${idx}.tar.gz
    done
done