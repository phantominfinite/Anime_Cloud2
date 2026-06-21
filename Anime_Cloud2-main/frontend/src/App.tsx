import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { Watch } from './pages/Watch';
import Search from './pages/Search';
import Library from './pages/Library';
import Profile from './pages/Profile';
import Details from './pages/Details';

const AnimatedRoutes = () => {
  const location = useLocation();
  const hideNav = location.pathname.startsWith('/anime/') || location.pathname.startsWith('/watch/');
  return (
    <>
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageWrapper><Home /></PageWrapper>} />
        <Route path="/anime/:id" element={<PageWrapper><Watch /></PageWrapper>} />
        <Route path="/anime/:id/details" element={<PageWrapper><Details /></PageWrapper>} />
        <Route path="/watch/:id/:episode" element={<PageWrapper><Watch /></PageWrapper>} />
        <Route path="/search" element={<PageWrapper><Search /></PageWrapper>} />
        <Route path="/library" element={<PageWrapper><Library /></PageWrapper>} />
        <Route path="/profile" element={<PageWrapper><Profile /></PageWrapper>} />
        <Route path="*" element={<PageWrapper><Home /></PageWrapper>} />
      </Routes>
    </AnimatePresence>
    {!hideNav && <Navbar />}
    </>
  );
};

const PageWrapper = ({ children }: { children: React.ReactNode }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    transition={{ duration: 0.3 }}
  >
    {children}
  </motion.div>
);

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-black text-white font-sans antialiased">
        <AnimatedRoutes />
      </div>
    </Router>
  );
};

export default App;
