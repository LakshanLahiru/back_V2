import logo from './logo.svg';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import Navi from './components/navibar/Navi';
import Home from './components/home/Home';
import History from './components/history/History';
import Dashboard from './components/dashboard/Dashboard';

function App() {
  return (
    <div >
      <BrowserRouter>
      
        <Routes>
        <Route path="/home" element={<Home/>}/>
        <Route path="/history" element={<History/>}/>
        <Route path="/dashboard" element={<Dashboard/>}/>

        </Routes>
      </BrowserRouter>
     
      
    </div>
  );
}

export default App;
