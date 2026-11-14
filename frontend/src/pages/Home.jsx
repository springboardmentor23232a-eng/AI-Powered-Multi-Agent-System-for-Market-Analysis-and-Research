import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 text-center">
      <h1 className="text-4xl font-bold text-gray-900">
        Multi-Agent Stock Research Analyst
      </h1>
      <p className="mt-4 max-w-xl text-lg text-gray-600">
        Research stocks with a team of AI agents. Save your watchlist and keep
        your research history in one place.
      </p>
      <div className="mt-8 flex gap-4">
        <Link
          to="/login"
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white hover:bg-blue-700"
        >
          Login
        </Link>
        <Link
          to="/register"
          className="rounded-lg border border-blue-600 px-6 py-2.5 font-medium text-blue-600 hover:bg-blue-50"
        >
          Register
        </Link>
      </div>
    </div>
  );
}