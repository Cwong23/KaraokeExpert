import torch
from unet import UNetModel
from data.dataset import SpectrogramDataset
import os
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import gc
# py -3.11 ./train.py


def manual_cleanup():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    print("GPU Memory Cleared")


manual_cleanup()
BATCH_SIZE = 4
EPOCHS = 50
LR = 5e-5

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if DEVICE.type != "cuda":
    print("Please use CUDA")
    raise SystemExit

print(f"Using device: {DEVICE}")
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
torch.cuda.empty_cache()
SAVE_MODEL_DIR = "resulting_model"
os.makedirs(SAVE_MODEL_DIR, exist_ok=True)

train_dataset = SpectrogramDataset(split="train")
val_dataset = SpectrogramDataset(split="valid")

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=True
)

print("DataLoaders created")

model = UNetModel(in_channels=1, out_channels=1).to(DEVICE)
print("Model created")

l1_loss = nn.L1Loss()
mse_loss = nn.MSELoss()


def hybrid_loss(pred, target):
    return 0.8 * l1_loss(pred, target) + 0.2 * mse_loss(pred, target)


optimizer = optim.Adam(model.parameters(), lr=LR)
scaler = torch.amp.GradScaler()


def train_epoch(model, dataloader):
    model.train()
    running_loss = 0.0

    for mix, vocals in dataloader:
        mix = mix.to(DEVICE)
        vocals = vocals.to(DEVICE)

        optimizer.zero_grad()

        with torch.autocast(device_type=DEVICE.type):
            outputs = model(mix)
            loss = hybrid_loss(outputs, vocals)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        running_loss += loss.detach().item()

    return running_loss / len(dataloader)


def validate_epoch(model, dataloader):
    model.eval()
    running_loss = 0.0

    with torch.no_grad():
        for mix, vocals in dataloader:
            mix = mix.to(DEVICE)
            vocals = vocals.to(DEVICE)

            outputs = model(mix)
            loss = hybrid_loss(outputs, vocals)

            running_loss += loss.detach().item()

    return running_loss / len(dataloader)


train_losses = []
val_losses = []

print(f"Starting training loop for {EPOCHS} epochs...")

for epoch in range(EPOCHS):
    train_loss = train_epoch(model, train_loader)
    val_loss = validate_epoch(model, val_loader)

    train_losses.append(train_loss)
    val_losses.append(val_loss)

    print(
        f"Epoch [{epoch+1}/{EPOCHS}] | "
        f"Train Loss: {train_loss:.5f} | "
        f"Val Loss: {val_loss:.5f}"
    )

    if (epoch + 1) % 5 == 0:
        torch.save(
            model.state_dict(),
            f"{SAVE_MODEL_DIR}/unet_epoch_{epoch+1}.pth"
        )

torch.save(model.state_dict(), f"{SAVE_MODEL_DIR}/unet_final.pth")
print("Training complete.")
