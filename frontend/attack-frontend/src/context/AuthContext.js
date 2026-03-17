import React, { createContext, useState, useEffect } from 'react';
import { login, getProfile } from '../api/auth';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      getProfile().then(res => setUser(res.data)).catch(() => localStorage.removeItem('token'));
    }
    setLoading(false);
  }, []);

  const signin = async (credentials) => {
    const { data } = await login(credentials);
    localStorage.setItem('token', data.access_token);
    const profile = await getProfile();
    setUser(profile.data);
  };

  const hasRole = (role) => user?.roles?.includes(role);

  return (
    <AuthContext.Provider value={{ user, signin, logout: () => { setUser(null); localStorage.removeItem('token'); }, hasRole, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
