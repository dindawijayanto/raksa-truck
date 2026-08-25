import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Rute from './pages/Rute';
import Kesehatan from './pages/Kesehatan';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {}
        <Route path="/" element={<Dashboard />} />
        
        {}
        <Route path="/rute" element={<Rute />} />

        {}
        <Route path="/kesehatan" element={<Kesehatan />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;