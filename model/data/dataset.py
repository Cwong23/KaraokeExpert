import numpy as np
import torch
from torch.utils.data import Dataset
import os


class SpectrogramDataset(Dataset):
    def __init__(self, split="train", target_width=512):
        self.root_dir = r".\data\processed_data"
        self.split_dir = os.path.join(self.root_dir, split)
        self.samples = sorted(os.listdir(self.split_dir))
        self.target_width = target_width

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample_name = self.samples[index]
        sample_path = os.path.join(self.split_dir, sample_name)

        try:
            mix = np.load(os.path.join(sample_path, "mixture.npy"))
            vocals = np.load(os.path.join(sample_path, "vocals.npy"))
            instr = np.load(os.path.join(sample_path, "instrumental.npy"))

            if mix.size == 0 or vocals.size == 0 or instr.size == 0:
                raise ValueError("Empty array")

        except Exception as e:
            print(f"Error loading {sample_name}: {e}. Skipping...")
            return self.__getitem__((index + 1) % len(self.samples))

        mix = mix[:1024, :]
        vocals = vocals[:1024, :]
        instr = instr[:1024, :]

        if mix.shape[1] > self.target_width:
            start = np.random.randint(0, mix.shape[1] - self.target_width)
            mix = mix[:, start:start + self.target_width]
            vocals = vocals[:, start:start + self.target_width]
            instr = instr[:, start:start + self.target_width]
        elif mix.shape[1] < self.target_width:
            pad_amount = self.target_width - mix.shape[1]
            mix = np.pad(mix, ((0, 0), (0, pad_amount)), mode='constant')
            vocals = np.pad(vocals, ((0, 0), (0, pad_amount)), mode='constant')
            instr = np.pad(instr, ((0, 0), (0, pad_amount)), mode='constant')

        mix = torch.from_numpy(mix).float()
        vocals = torch.from_numpy(vocals).float()
        instr = torch.from_numpy(instr).float()

        if mix.ndim == 2:
            mix = mix.unsqueeze(0)

        target = torch.stack([vocals, instr], dim=0)

        return mix, target
