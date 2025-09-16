import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { motion } from 'framer-motion';

// Pages
import OnboardingPage from './pages/OnboardingPage';
import ProcessingPage from './pages/ProcessingPage';
import TimelinePage from './pages/TimelinePage';
import NarrativePage from './pages/NarrativePage';

// Components
import Header from './components/Header';
import Footer from './components/Footer';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      
      <main className="flex-1">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Routes>
            <Route path="/" element={<OnboardingPage />} />
            <Route path="/processing" element={<ProcessingPage />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/narrative" element={<NarrativePage />} />
          </Routes>
        </motion.div>
      </main>
      
      <Footer />
    </div>
  );
}

export default App;