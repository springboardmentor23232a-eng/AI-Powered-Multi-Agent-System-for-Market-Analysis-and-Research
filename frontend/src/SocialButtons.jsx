import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "./AuthContext";
import { errorMessage } from "./api";

export default function SocialButtons() {
  const { googleLogin } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const onSuccess = async (response) => {
    setError("");
    try {
      await googleLogin(response.credential);
      navigate("/dashboard");
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-center">
        <GoogleLogin
          onSuccess={onSuccess}
          onError={() => setError("Google sign-in failed. Please try again.")}
          text="signin_with"
          shape="rectangular"
          width="350"
        />
      </div>

      <button
        type="button"
        disabled
        title="Coming soon"
        className="w-full cursor-not-allowed rounded-lg border border-gray-300 bg-gray-100 py-2.5 font-medium text-gray-400"
      >
        Sign in with Apple (coming soon)
      </button>

      {error && <p className="text-center text-sm text-red-600">{error}</p>}
    </div>
  );
}