import { useClerk } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import "./App.css";

export default function Home() {
  const { signOut } = useClerk();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  return (
    <div>
      <button onClick={handleSignOut}>
        Back to Login
      </button>
    </div>
  );
}