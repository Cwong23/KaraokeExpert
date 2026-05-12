import mongoose from "mongoose";

// One single pitch point
const PitchPointSchema = new mongoose.Schema({
  time: Number,
  pitch: Number,
}, { _id: false });

// Whole graph
const PitchGraphSchema = new mongoose.Schema({
  userId: { type: String, required: true }, // Clerk user ID
  songId: { type: String, required: true },
  artistPitch: [PitchPointSchema],
  userPitch: [PitchPointSchema],
  accuracyScore: Number,
  createdAt: { type: Date, default: Date.now },
});

export const PitchGraph = mongoose.model("PitchGraph", PitchGraphSchema);