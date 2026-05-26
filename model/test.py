"""
This is an artifact file for now. I'll clean it up in the future.
"""

# import torch
# import numpy as np
# import librosa
# import soundfile as sf
# import os
# from unet import UNetModel

# DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# SR = 44100
# TARGET_W = 1024

# model = UNetModel(in_channels=1, out_channels=1).to(DEVICE)
# model.load_state_dict(torch.load(
#     "resulting_model/unet_final.pth", map_location=DEVICE))
# model.eval()

# target = "sample_00002"
# root_dir = r".\data\processed_data\test"
# mix_npy = np.load(os.path.join(root_dir, target,
#                   "mixture.npy"))  # (1025, 2584)

# original_h, original_w = mix_npy.shape
# mix_input = mix_npy[:1024, :]

# pad_amount = TARGET_W - (original_w % TARGET_W)
# mix_padded = np.pad(mix_input, ((0, 0), (0, pad_amount)), mode='constant')

# processed_chunks = []

# with torch.no_grad():
#     for i in range(0, mix_padded.shape[1], TARGET_W):
#         chunk = mix_padded[:, i:i+TARGET_W]
#         tensor_chunk = torch.from_numpy(
#             chunk).float().unsqueeze(0).unsqueeze(0).to(DEVICE)
#         output_chunk = model(tensor_chunk)
#         processed_chunks.append(output_chunk.squeeze().cpu().numpy())

# full_pred = np.concatenate(processed_chunks, axis=1)

# pred_npy = full_pred[:, :original_w]
# final_pred_npy = np.vstack([pred_npy, np.zeros((1, original_w))])


# def reconstruct(data, sr):
#     db = (np.clip(data, 0, 1) * 80.0) - 80.0
#     amp = librosa.db_to_amplitude(db)

#     return librosa.griffinlim(
#         amp, n_iter=128, hop_length=512, win_length=2048, momentum=0.99
#     )


# wav_pred = reconstruct(final_pred_npy, SR)
# sf.write("data/testing_output/full_30s_vocal.wav", wav_pred, SR)
