import numpy as np
import torch
from torch.utils.data import Dataset
import os


class SpectrogramDataset(Dataset):
    def __init__(self, split="train", target_width=512):
        self.root_dir = r".\data\processed_data"
        self.split_dir = os.path.join(self.root_dir, split)
        self.samples = sorted(os.listdir(self.split_dir))
        self.target_width = target_width  # e.g., 512 frames

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample_name = self.samples[index]
        sample_path = os.path.join(self.split_dir, sample_name)

        mix = np.load(os.path.join(sample_path, "mixture.npy"))
        vocals = np.load(os.path.join(sample_path, "vocals.npy"))

        mix = mix[:1024, :]
        vocals = vocals[:1024, :]

        if mix.shape[1] > self.target_width:
            mix = mix[:, :self.target_width]
            vocals = vocals[:, :self.target_width]
        elif mix.shape[1] < self.target_width:
            pad_amount = self.target_width - mix.shape[1]
            mix = np.pad(mix, ((0, 0), (0, pad_amount)), mode='constant')
            vocals = np.pad(vocals, ((0, 0), (0, pad_amount)), mode='constant')

        mix = torch.from_numpy(mix).float()
        vocals = torch.from_numpy(vocals).float()

        if mix.ndim == 2:
            mix = mix.unsqueeze(0)
        if vocals.ndim == 2:
            vocals = vocals.unsqueeze(0)

        return mix, vocals
