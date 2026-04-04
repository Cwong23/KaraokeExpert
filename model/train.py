import torch
from unet import UNetModel
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision.utils as vutils
from torchvision.models import vgg19, VGG19_Weights
from torch.nn import functional as F
from torchmetrics.image.ssim import StructuralSimilarityIndexMeasure

# hyper parameters
BATCH_SIZE = 8
EPOCHS = 50
LR = 5e-5
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# model/data setup stuff
SAVE_MODEL_DIR = "model/resulting_model"
os.makedirs(SAVE_MODEL_DIR, exist_ok=True)
