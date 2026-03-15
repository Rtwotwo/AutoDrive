"""
Author: Redal
Date: 2026-01-28
Todo: Use the trained DiffusionDrive(TransfuserAgent) ckpt to perform trajectory 
      prediction and visualization on random scenes (overlay GT vs prediction on BEV).
Dependency environment variables:
    - OPENSCENE_DATA_ROOT: OpenScene data root directory (containing navsim_logs/ and sensor_blobs/)
    - NAVSIM_DEVKIT_ROOT: navsim code/resource root directory (containing traj_final/kmeans_navsim_traj_20.npy)
Homepage: https://github.com/Rtwotwo/Code-Exam.git
"""

from __future__ import annotations
import os
from pathlib import Path
import io
import numpy as np
import torch
import matplotlib.pyplot as plt
from PIL import Image
from tqdm import tqdm
import argparse
FILE_PATH = os.path.dirname(os.path.abspath(__file__))

from navsim.common.dataloader import SceneLoader
from navsim.common.dataclasses import SceneFilter, SensorConfig
from navsim.visualization.bev import add_configured_bev_on_ax, add_trajectory_to_bev_ax
from navsim.visualization.config import TRAJECTORY_CONFIG
from navsim.visualization.plots import (
    configure_ax,
    configure_bev_ax,
    plot_cameras_frame_with_annotations,
    plot_cameras_frame,
    plot_bev_frame,
)
from nuplan.planning.simulation.trajectory.trajectory_sampling import TrajectorySampling


def _require_env_path(var_name: str) -> Path:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Environment variable {var_name} is not set.")
    return Path(value)


def _get_agent_type(ckpt_path: Path) -> str:
    """Infer whether to use classic Transfuser or DiffusionDrive based on checkpoint path."""
    env_agent = os.getenv("NAVSIM_AGENT", "").strip().lower()
    if env_agent in ("transfuser", "diffusiondrive"):
        return env_agent
    s = str(ckpt_path).lower()
    if "train_transfuser" in s or ("transfuser" in s and "diffusiondrive" not in s):
        return "transfuser"
    return "diffusiondrive"


def main() -> None:
    split = os.getenv("NAVSIM_SPLIT", "mini")  # ["mini", "test", "trainval"]
    state_dict_path = "/data/alg-model-datavol-0/xinyao/navsim_workspace/exp/train_transfuser_resnet/epoch=69.ckpt"
    model_name = os.getenv("NAVSIM_MODEL_NAME", "transfuser_epoch69")
    ckpt_path = Path(
        os.getenv(
            "NAVSIM_CKPT_PATH",
            state_dict_path,
        )
    )
    openscene_data_root = _require_env_path("OPENSCENE_DATA_ROOT")
    navsim_devkit_root = _require_env_path("NAVSIM_DEVKIT_ROOT")

    # Common resnet34 weight file used during training/inference (timm pretrained_cfg_overlay will use it)
    bkb_path = Path(
        os.getenv(
            "NAVSIM_BKB_PATH",
            str(openscene_data_root / "models/resnet34_model.bin"),
        )
    )
    if not bkb_path.exists():
        raise FileNotFoundError(
            "Backbone weight file not found.\n"
            f"Current path: {bkb_path}\n"
            "Please place the weight file at this path, or set the environment variable NAVSIM_BKB_PATH to point to the actual existing file."
        )

    if not ckpt_path.exists():
        raise FileNotFoundError(f"[ERROR] Not found ckpt: {ckpt_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent_type = _get_agent_type(ckpt_path)

    # --- build agent (select classic Transfuser or DiffusionDrive based on ckpt) ---
    if agent_type == "transfuser":
        from navsim.agents.transfuser.transfuser_agent import TransfuserAgent
        from navsim.agents.transfuser.transfuser_config import TransfuserConfig

        cfg = TransfuserConfig(bkb_path=str(bkb_path))
        trajectory_sampling = TrajectorySampling(time_horizon=4, interval_length=0.5)
        agent = TransfuserAgent(
            config=cfg,
            lr=0.0,
            checkpoint_path=str(ckpt_path),
            trajectory_sampling=trajectory_sampling,
        )
    else:
        from navsim.agents.diffusiondrive.transfuser_agent import TransfuserAgent
        from navsim.agents.diffusiondrive.transfuser_config import TransfuserConfig

        plan_anchor_path = navsim_devkit_root / "traj_final/kmeans_navsim_traj_20.npy"
        if not plan_anchor_path.exists():
            raise FileNotFoundError(f"[ERROR] no plan anchor: {plan_anchor_path}")
        cfg = TransfuserConfig(
            bkb_path=str(bkb_path),
            plan_anchor_path=str(plan_anchor_path),
        )
        agent = TransfuserAgent(config=cfg, lr=0.0, checkpoint_path=str(ckpt_path))

    agent.to(device).eval()
    agent.initialize()  # classic Transfuser does not load weights in __init__, must be called explicitly

    # --- build scene loader ---
    # Here specifically for "visualization" to load full sensors (consistent with tutorial),
    # No longer use agent.get_sensor_config() for cropping, so camera data for the entire scene is available.
    scene_filter = SceneFilter()  # Default is equivalent to "no filtering"
    scene_loader = SceneLoader(
        openscene_data_root / f"navsim_logs/{split}",
        openscene_data_root / f"sensor_blobs/{split}",
        scene_filter,
        openscene_data_root / "warmup_two_stage/sensor_blobs",
        openscene_data_root / "warmup_two_stage/synthetic_scene_pickles",
        sensor_config=SensorConfig.build_all_sensors(),
    )

    # token = np.random.choice(scene_loader.tokens)
    print(f"[INFO] Number of Split's tokens: {split}: {len(scene_loader.tokens)}")
    for i in range(0, len(scene_loader.tokens), 500):
        token = scene_loader.tokens[i]
        print(f'[INFO] Chosen the {i:04d}: {token} trajectory for visualization')
        scene = scene_loader.get_scene_from_token(token)

        # --- inference ---
        frame_idx = scene.scene_metadata.num_history_frames - 1  # current frame index
        agent_input = scene.get_agent_input()
        pred = agent.compute_trajectory(agent_input, device=str(device))
        pred_traj = pred["trajectory"]
        gt_traj = scene.get_future_trajectory()

        # --- Static image: camera + BEV + GT (green) & prediction (red) ---
        # Use the 3x3 camera+BEV layout from the tutorial, overlay trajectories on the middle BEV.
        fig, ax = plot_cameras_frame_with_annotations(scene, frame_idx)
        try:
            bev_ax = ax[1][1]
            add_trajectory_to_bev_ax(bev_ax, gt_traj, TRAJECTORY_CONFIG["human"])
            add_trajectory_to_bev_ax(bev_ax, pred_traj, TRAJECTORY_CONFIG["agent"])
            configure_bev_ax(bev_ax)
        except Exception:
            # If layout or axis structure is abnormal, fall back to only drawing BEV+trajectory
            plt.close(fig)
            fig, bev_ax = plt.subplots(1, 1, figsize=(6, 6))
            add_configured_bev_on_ax(bev_ax, scene.map_api, scene.frames[frame_idx])
            add_trajectory_to_bev_ax(bev_ax, gt_traj, TRAJECTORY_CONFIG["human"])
            add_trajectory_to_bev_ax(bev_ax, pred_traj, TRAJECTORY_CONFIG["agent"])
            configure_bev_ax(bev_ax)
            configure_ax(bev_ax)

        # Save as jpg
        output_dir = os.path.join(FILE_PATH, 'visualization', split, model_name)
        os.makedirs(output_dir, exist_ok=True)
        bev_path = os.path.join(output_dir, f"trajectory_prediction_{split}_{token}.jpg")
        fig.savefig(bev_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"[INFO] Predicted BEV views have been saved to: {bev_path}")

        # --- Generate GIF of camera views + predicted trajectories (only keep frames with valid camera data) ---

        def try_plot_cameras_with_anns(s, idx):
            """Prefer to draw "camera + 2D box", fall back to only drawing camera if failed
            If still fails, throw exception and let the upper layer skip this frame"""
            try:
                return plot_cameras_frame_with_annotations(s, idx)
            except Exception:
                # When unable to draw annotations, only draw camera image
                return plot_cameras_frame(s, idx)

        images = []
        frame_indices = list(range(len(scene.frames)))
        for frame_idx in tqdm(frame_indices, desc="Rendering frames for GIF"):
            try:
                fig, ax = try_plot_cameras_with_anns(scene, frame_idx)
            except Exception:
                # Skip frames without valid camera data
                continue

            # Overlay GT and predicted trajectories on the BEV of the current frame
            if frame_idx == scene.scene_metadata.num_history_frames - 1:
                try:
                    bev_ax = ax[1][1]
                    add_trajectory_to_bev_ax(bev_ax, gt_traj, TRAJECTORY_CONFIG["human"])
                    add_trajectory_to_bev_ax(bev_ax, pred_traj, TRAJECTORY_CONFIG["agent"])
                    configure_bev_ax(bev_ax)
                except Exception:
                    # If 3x3 layout is not available, do not force overlay to avoid interrupting GIF generation
                    pass

            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)
            images.append(Image.open(buf).copy())
            buf.close()
            plt.close(fig)

        if images:
            gif_path = os.path.join(output_dir, f"trajectory_cameras_{split}_{token}.gif")
            images[0].save(
                gif_path,
                save_all=True,
                append_images=images[1:],
                duration=500,
                loop=0,
            )
            print(f"[INFO] The gif of cameras has been saved to: {gif_path}")
        else:
            print(f"[ERROR] No valid images and no GIF")


if __name__ == "__main__":
    main()

