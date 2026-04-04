from PIL import Image
import os
import torch
from torch.utils.data import Dataset
import torchvision.transforms as T
import torchvision.transforms.functional as TF
import random


class Spectrogram(Dataset):
    def __init__(self, split="train"):
        self.root_dir = r".\processed_data"

        # get spectrogram paths and store them in a list
        self.samples = sorted(os.listdir(self.root_dir + "/" + split))

        self.transform = T.Compose([
            T.Resize((128, 512)),
            T.ToTensor(),
            T.Normalize([0.5], [0.5])
        ])

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        parent_path = self.samples[index]

        mix_path = os.path.join(self.root_dir, parent_path, "mixture.png")
        vocals_path = os.path.join(self.root_dir, parent_path, "vocals.png")

        mix_img = Image.open(mix_path).convert("RGB")
        vocals_img = Image.open(vocals_path).convert("RGB")

        mix_img = self.transform(mix_img)
        vocals_img = self.transform(vocals_img)

        return mix_img, vocals_img
