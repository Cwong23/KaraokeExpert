import mongoose from "mongoose";

const connectDB = async () => {
  const url = process.env.MONGO_URI as string; 
  if (!connection) {
    connection = await mongoose.connect(url);
    return connection;
  }
}

let connection: typeof mongoose;

export default connectDB;