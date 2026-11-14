import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="p-8 text-gray-600">Loading...</p>;
  return user ? children : <Navigate to="/login" replace />;
}