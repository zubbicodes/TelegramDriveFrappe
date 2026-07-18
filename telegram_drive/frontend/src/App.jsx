import React, { useState, useEffect } from 'react';
import AuthScreen from './components/AuthScreen';
import FileManager from './components/FileManager';
import PortalManager from './components/PortalManager';
import { authMe, portalMe } from './api';

function App() {
  const [token, setToken] = useState(localStorage.getItem('td_token'));
  const [portalToken, setPortalToken] = useState(localStorage.getItem('td_portal_token'));
  const [checking, setChecking] = useState(true);
  const [theme, setTheme] = useState('light');

  const getFrappeTheme = () => {
    const serverTheme = String(window.telegram_drive_theme || '').toLowerCase();
    if (serverTheme === 'dark') return 'dark';
    if (serverTheme === 'light') return 'light';
    if (serverTheme === 'automatic') {
      return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    const explicitTheme = document.documentElement.dataset.theme || document.body?.dataset.theme || '';
    const storedTheme = localStorage.getItem('desk_theme') || localStorage.getItem('theme') || localStorage.getItem('frappe_theme') || '';
    const themeValue = `${explicitTheme} ${storedTheme}`.toLowerCase();
    if (themeValue.includes('dark') || document.documentElement.classList.contains('dark')) return 'dark';
    return 'light';
  };

  const applyThemeValue = (themeValue) => {
    const normalized = String(themeValue || '').toLowerCase();
    const resolved = normalized === 'automatic'
      ? (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : (normalized === 'dark' ? 'dark' : 'light');
    window.telegram_drive_theme = themeValue || (resolved === 'dark' ? 'Dark' : 'Light');
    setTheme(resolved);
    document.documentElement.classList.toggle('dark', resolved === 'dark');
  };

  useEffect(() => {
    const verify = async () => {
      try {
        const response = await authMe();
        if (response.data?.desk_theme) applyThemeValue(response.data.desk_theme);
        if (response.data?.frappe_user) {
          localStorage.removeItem('td_token');
          localStorage.removeItem('td_portal_token');
          setToken('frappe-session');
          setPortalToken(null);
          setChecking(false);
          return;
        }
      } catch (e) {
        // Fall through to the legacy owner token and friend portal checks.
      }

      if (token) {
        try {
          const response = await authMe();
          if (response.data?.desk_theme) applyThemeValue(response.data.desk_theme);
          setToken(token);
        } catch (e) {
          localStorage.removeItem('td_token');
          setToken(null);
        }
      }
      if (!token && portalToken) {
        try {
          await portalMe();
          setPortalToken(portalToken);
        } catch (e) {
          localStorage.removeItem('td_portal_token');
          setPortalToken(null);
        }
      }
      setChecking(false);
    };
    verify();
  }, []);

  useEffect(() => {
    const applyFrappeTheme = () => {
      const frappeTheme = getFrappeTheme();
      setTheme(frappeTheme);
      document.documentElement.classList.toggle('dark', frappeTheme === 'dark');
    };
    applyFrappeTheme();
    const observer = new MutationObserver(applyFrappeTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class', 'data-theme'] });
    if (document.body) observer.observe(document.body, { attributes: true, attributeFilter: ['class', 'data-theme'] });
    const mediaQuery = window.matchMedia?.('(prefers-color-scheme: dark)');
    mediaQuery?.addEventListener?.('change', applyFrappeTheme);
    const interval = window.setInterval(applyFrappeTheme, 1000);
    return () => {
      observer.disconnect();
      mediaQuery?.removeEventListener?.('change', applyFrappeTheme);
      window.clearInterval(interval);
    };
  }, []);

  const handleLogin = (t, mode = 'owner') => {
    if (mode === 'portal') {
      setPortalToken(t);
      setToken(null);
      return;
    }
    localStorage.removeItem('td_portal_token');
    setPortalToken(null);
    setToken(t);
  };

  const handleLogout = () => {
    localStorage.removeItem('td_token');
    localStorage.removeItem('td_portal_token');
    setToken(null);
    setPortalToken(null);
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-600 font-medium">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen">
      {token ? (
        <FileManager onLogout={handleLogout} theme={theme} />
      ) : portalToken ? (
        <PortalManager onLogout={handleLogout} theme={theme} />
      ) : (
        <AuthScreen onLogin={handleLogin} theme={theme} />
      )}
    </div>
  );
}

export default App;
