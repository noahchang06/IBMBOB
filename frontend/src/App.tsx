import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useAppStore } from './store/appStore';
import { useApi } from './hooks/useApi';
import { DiscoveryView } from './components/discovery/DiscoveryView';
import { AppShell } from './components/layout/AppShell';

export default function App() {
  const { view, setChallenges } = useAppStore();
  const api = useApi();
  const [initError, setInitError] = useState<string | null>(null);

  useEffect(() => {
    api.fetchChallenges()
      .then(challenges => setChallenges(challenges))
      .catch(() => setInitError(
        'Could not connect to the backend. Make sure the server is running on port 8000.'
      ));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="w-full h-full text-text-primary bg-surface-0 overflow-hidden font-sans">
      {initError && (
        <div
          role="alert"
          className="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-red-500/10 border border-red-500/30 rounded-xl px-5 py-3 text-sm text-red-400 text-center"
        >
          {initError}
        </div>
      )}
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
