import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import API from "../services/api";
import "./Register.css";

function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    try {
      setLoading(true);

      const response = await API.post("/auth/login", formData);

      sessionStorage.setItem("access_token", response.data.access_token);

      navigate("/dashboard");
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Login failed. Please check your email and password.",
      );
    } finally {
      setLoading(false);
    }
  }
  async function handleGoogleSuccess(credentialResponse) {
    if (!credentialResponse.credential) {
      setError("Google authentication failed. Please try again.");
      return;
    }

    try {
      setError("");
      setLoading(true);

      const response = await API.post("/auth/google", {
        credential: credentialResponse.credential,
      });

      sessionStorage.setItem("access_token", response.data.access_token);

      navigate("/dashboard");
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Google login failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>Welcome Back</h1>

        <p className="auth-subtitle">Login to Stock Research Analyst</p>

        <div className="social-login">
          <div className="google-login-button">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError("Google authentication failed.")}
            />
          </div>

          <button
            type="button"
            className="social-button apple-button"
            onClick={() =>
              setError(
                "Sign in with Apple is coming soon. Please use Google or email login for now.",
              )
            }
          >
            <span className="apple-icon"></span>
            Continue with Apple
          </button>
        </div>

        <div className="login-divider">
          <span>OR</span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email Address</label>

            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>

            <input
              type="password"
              name="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          {error && <p style={{ color: "red" }}>{error}</p>}

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <p className="auth-footer">
          Don't have an account? <Link to="/register">Create Account</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
