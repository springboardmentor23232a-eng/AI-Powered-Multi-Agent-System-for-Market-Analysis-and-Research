import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

const MARKETS = ["NSE", "BSE", "NASDAQ", "NYSE"];
const PERIODS = [
  { value: "1M", label: "1 Month" },
  { value: "3M", label: "3 Months" },
  { value: "6M", label: "6 Months" },
  { value: "1Y", label: "1 Year" },
  { value: "5Y", label: "5 Years" },
];

export default function Preferences({ onChange }) {
  const [form, setForm] = useState({ market: "NSE", analysis_period: "1Y" });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    api
      .get("/preferences")
      .then((res) => {
        setForm(res.data);
        onChange(res.data);
      })
      .catch((err) => setMessage({ type: "error", text: errorMessage(err) }));
  }, []);

  const save = async () => {
    setSaving(true);
    setMessage({ type: "", text: "" });
    try {
      const res = await api.put("/preferences", form);
      setForm(res.data);
      onChange(res.data);
      setMessage({ type: "success", text: "Preferences saved" });
    } catch (err) {
      setMessage({ type: "error", text: errorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  const select =
    "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 focus:border-blue-500 focus:outline-none";

  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <h3 className="font-semibold text-gray-900">Preferences</h3>

      <label className="mt-4 block text-sm text-gray-600">Preferred market</label>
      <select
        className={select}
        value={form.market}
        onChange={(e) => setForm({ ...form, market: e.target.value })}
      >
        {MARKETS.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>

      <label className="mt-4 block text-sm text-gray-600">Analysis period</label>
      <select
        className={select}
        value={form.analysis_period}
        onChange={(e) => setForm({ ...form, analysis_period: e.target.value })}
      >
        {PERIODS.map((p) => (
          <option key={p.value} value={p.value}>{p.label}</option>
        ))}
      </select>

      <button
        onClick={save}
        disabled={saving}
        className="mt-5 w-full rounded-lg bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
      >
        {saving ? "Saving..." : "Save preferences"}
      </button>

      {message.text && (
        <p className={`mt-3 text-sm ${message.type === "error" ? "text-red-600" : "text-green-600"}`}>
          {message.text}
        </p>
      )}
    </div>
  );
}