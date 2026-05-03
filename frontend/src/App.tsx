import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { Watch } from './pages/Watch';
import Search from './pages/Search';
import Library from './pages/Library';
import Profile from './pages/Profile';

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-black text-white font-sans antialiased">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/anime/:id" element={<Watch />} />
          <Route path="/search" element={<Search />} />
          <Route path="/library" element={<Library />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="*" element={<Home />} />
        </Routes>
        <Navbar />
      </div>
    </Router>
  );
};

export default App;
