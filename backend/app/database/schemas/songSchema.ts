import mongoose from "mongoose";

const SongSchema = new mongoose.Schema({
  userId: { type: String, required: true }, // Clerk user id
  title: { type: String, required: true },
  filePath: { type: String, required: true },
  instrumentalPath: { type: String, default: null },
  vocalPath: { type: String, default: null },
  duration: { type: Number, default: null },
  language: { type: String, default: null },
  lyrics: { type: String, default: null },
  status: {
    type: String,
    enum: ["uploaded", "processing", "ready", "failed"],
    default: "uploaded",
  },
  uploadedAt: { type: Date, default: Date.now },
});

export const Song = mongoose.model("Song", SongSchema);