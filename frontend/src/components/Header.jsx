import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 bg-white px-8 py-4 shadow">
      <div className="flex items-center gap-6">
        <Link to="/dashboard" className="text-xl font-bold text-gray-900">
          Stock Research Analyst
        </Link>
        <nav className="flex gap-4 text-sm">
          <Link to="/dashboard" className="text-gray-600 hover:text-blue-600">Dashboard</Link>
          <Link to="/watchlists" className="text-gray-600 hover:text-blue-600">My Watchlists</Link>
        </nav>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-gray-600">{user.full_name}</span>
        <button
          onClick={onLogout}
          className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm hover:bg-gray-100"
        >
          Logout
        </button>
      </div>
    </header>
  );
}