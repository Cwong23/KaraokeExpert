import mongoose from "mongoose";

const LyricLineSchema = new mongoose.Schema({
  text: { type: String, required: true },
  startTime: { type: Number, required: true },
  endTime: { type: Number, required: true },
}, { _id: false });

const LyricsSchema = new mongoose.Schema({
  songId: { type: mongoose.Schema.Types.ObjectId, ref: "Song", required: true },
  language: { type: String, default: null },
  lines: [LyricLineSchema], // Array of lyrics lines
  createdAt: { type: Date, default: Date.now },
});

export const Lyrics = mongoose.model("Lyrics", LyricsSchema);