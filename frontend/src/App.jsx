import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import { Login, Register } from './pages/AuthPages';
import Dashboard from './pages/Dashboard';
import StockSearch from './pages/StockSearch';
import History from './pages/History';
import Watchlist from './pages/Watchlist';
import Preferences from './pages/Preferences';
export default function App(){return <Routes><Route path="/login" element={<Login/>}/><Route path="/register" element={<Register/>}/><Route element={<ProtectedRoute/>}><Route element={<Layout/>}><Route path="/" element={<Dashboard/>}/><Route path="/search" element={<StockSearch/>}/><Route path="/history" element={<History/>}/><Route path="/watchlist" element={<Watchlist/>}/><Route path="/preferences" element={<Preferences/>}/></Route></Route><Route path="*" element={<Navigate to="/" replace/>}/></Routes>}
