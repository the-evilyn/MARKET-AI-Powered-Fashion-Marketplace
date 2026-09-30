"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { api, User } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  cartCount: number;
  login: (email: string, pass: string) => Promise<void>;
  quickCustomerLogin: () => Promise<void>;
  logout: () => void;
  refreshCartCount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [cartCount, setCartCount] = useState<number>(0);

  const refreshCartCount = async () => {
    try {
      const cart = await api.getCart();
      const count = (cart.items || []).reduce((acc, item) => acc + item.quantity, 0);
      setCartCount(count);
    } catch {
      setCartCount(0);
    }
  };

  const loadUser = async () => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return;
    }

    try {
      setToken(storedToken);
      const me = await api.getMe();
      setUser(me);
      await refreshCartCount();
    } catch {
      localStorage.removeItem("token");
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const login = async (email: string, pass: string) => {
    const res = await api.login({ username: email, password: pass });
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    const me = await api.getMe();
    setUser(me);
    await refreshCartCount();
  };

  const quickCustomerLogin = async () => {
    // Attempt login with default customer, or register if needed
    const defaultEmail = "customer@example.com";
    const defaultPass = "Customer123!";
    try {
      await login(defaultEmail, defaultPass);
    } catch {
      // Register customer first
      try {
        await api.register({
          email: defaultEmail,
          password: defaultPass,
          first_name: "Demo",
          last_name: "Customer",
          role: "CUSTOMER",
        });
        await login(defaultEmail, defaultPass);
      } catch (err) {
        console.error("Quick login registration failed:", err);
      }
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setToken(null);
    setCartCount(0);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        cartCount,
        login,
        quickCustomerLogin,
        logout,
        refreshCartCount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
