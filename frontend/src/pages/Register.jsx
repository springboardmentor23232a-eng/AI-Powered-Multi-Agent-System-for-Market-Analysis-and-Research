import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errorMessage } from "../api";
import SocialButtons from "../SocialButtons";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/auth/register", form);
      setSuccess("Registration successful! Redirecting to login...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const input =
    "w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none";

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow">
        <h2 className="text-2xl font-bold text-gray-900">Create your account</h2>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input className={input} name="full_name" placeholder="Full name"
            value={form.full_name} onChange={onChange} required />
          <input className={input} type="email" name="email" placeholder="Email address"
            value={form.email} onChange={onChange} required />
          <input className={input} type="password" name="password"
            placeholder="Password (min 8 characters)"
            value={form.password} onChange={onChange} required />
          <input className={input} type="password" name="confirm_password"
            placeholder="Confirm password"
            value={form.confirm_password} onChange={onChange} required />

          {error && <p className="text-sm text-red-600">{error}</p>}
          {success && <p className="text-sm text-green-600">{success}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-blue-600 py-2.5 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {submitting ? "Registering..." : "Register"}
          </button>
        </form>

        <div className="my-6 flex items-center gap-3 text-sm text-gray-400">
          <div className="h-px flex-1 bg-gray-200" /> or <div className="h-px flex-1 bg-gray-200" />
        </div>

        <SocialButtons />

        <p className="mt-6 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-blue-600 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}