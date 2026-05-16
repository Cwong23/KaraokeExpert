import torch
from unet import UNetModel
from data.dataset import SpectrogramDataset
import os
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import gc


def manual_cleanup():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    print("GPU Memory Cleared")


l1_loss = nn.L1Loss()


def multi_target_loss(outputs, targets, mix):
    # trains on both the vocals and instrumental
    # TODO: Also train on other things? Maybe this will make the model better
    pred_v = torch.sigmoid(outputs[:, 0, :, :].unsqueeze(1))
    pred_i = torch.sigmoid(outputs[:, 1, :, :].unsqueeze(1))

    true_v = targets[:, 0, :, :].unsqueeze(1)
    true_i = targets[:, 1, :, :].unsqueeze(1)

    v_l1 = l1_loss(pred_v, true_v)
    i_l1 = l1_loss(pred_i, true_i)

    consistency = l1_loss(pred_v + pred_i, mix)

    return (v_l1 + i_l1) + (0.2 * consistency)


def train_epoch(model, dataloader, optimizer, scaler, device):
    model.train()
    running_loss = 0.0
    for mix, target in dataloader:
        mix = mix.to(device)
        target = target.to(device)
        mix, target = augment(mix, target)

        optimizer.zero_grad()
        with torch.autocast(device_type=device.type):
            outputs = model(mix)
            loss = multi_target_loss(outputs, target, mix)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        running_loss += loss.detach().item()

    return running_loss / len(dataloader)


def validate_epoch(model, dataloader, device):
    model.eval()
    running_loss = 0.0
    with torch.no_grad():
        for mix, target in dataloader:
            mix = mix.to(device)
            target = target.to(device)
            outputs = model(mix)
            loss = multi_target_loss(outputs, target, mix)
            running_loss += loss.detach().item()
    return running_loss / len(dataloader)


def augment(mix, target):
    if torch.rand(1) > 0.5:
        mix = torch.flip(mix, [3])
        target = torch.flip(target, [3])

    gain = torch.rand(1).to(mix.device) * 0.4 + 0.8
    mix = mix * gain
    target = target * gain

    freq_mask_size = torch.randint(10, 50, (1,)).item()
    freq_start = torch.randint(0, 1024 - freq_mask_size, (1,)).item()
    mix[:, :, freq_start:freq_start + freq_mask_size, :] = 0
    target[:, :, freq_start:freq_start + freq_mask_size, :] = 0

    time_mask_size = torch.randint(10, 50, (1,)).item()
    time_start = torch.randint(0, mix.shape[3] - time_mask_size, (1,)).item()
    mix[:, :, :, time_start:time_start + time_mask_size] = 0
    target[:, :, :, time_start:time_start + time_mask_size] = 0

    noise = torch.randn_like(mix) * 0.01
    mix = torch.clamp(mix + noise, 0, 1)

    return mix, target


if __name__ == '__main__':
    manual_cleanup()

    BATCH_SIZE = 8
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

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=4, pin_memory=True, persistent_workers=True)
    val_loader = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=4, pin_memory=True, persistent_workers=True)

    print("DataLoaders created")

    model = UNetModel(in_channels=1, out_channels=2).to(DEVICE)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {total_params / 1e6:.1f}M")

    optimizer = optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    scaler = torch.amp.GradScaler()
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, 'min', patience=5, factor=0.5)

    print(f"Starting training loop for {EPOCHS} epochs...")

    for epoch in range(EPOCHS):
        train_loss = train_epoch(
            model, train_loader, optimizer, scaler, DEVICE)
        val_loss = validate_epoch(model, val_loader, DEVICE)

        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        print(
            f"Epoch [{epoch+1}/{EPOCHS}] | "
            f"Train Loss: {train_loss:.5f} | "
            f"Val Loss: {val_loss:.5f} | "
            f"LR: {current_lr:.6f}"
        )

        if (epoch + 1) % 25 == 0:
            torch.save(model.state_dict(),
                       f"{SAVE_MODEL_DIR}/unet_epoch_{epoch+1}.pth")

    torch.save(model.state_dict(), f"{SAVE_MODEL_DIR}/unet_final.pth")
    print("Training complete.")
