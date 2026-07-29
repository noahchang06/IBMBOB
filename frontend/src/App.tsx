import React, { useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useAppStore } from './store/appStore';
import { useApi } from './hooks/useApi';
import { DiscoveryView } from './components/discovery/DiscoveryView';
import { AppShell } from './components/layout/AppShell';

export default function App() {
  const { view, setChallenges } = useAppStore();
  const api = useApi();

  useEffect(() => {
    // Initial data load
    api.fetchChallenges()
      .then(challenges => setChallenges(challenges))
      .catch(err => console.error('Failed to load challenges:', err));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="w-full h-full text-text-primary bg-surface-0 overflow-hidden font-sans">
      <AnimatePresence mode="wait">
        {view === 'discovery' ? (
          <motion.div
            key="discovery"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.02 }}
            transition={{ duration: 0.4, ease: "easeInOut" }}
            className="w-full h-full"
          >
            <DiscoveryView />
          </motion.div>
        ) : (
          <motion.div
            key="workspace"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full h-full"
          >
            <AppShell />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
