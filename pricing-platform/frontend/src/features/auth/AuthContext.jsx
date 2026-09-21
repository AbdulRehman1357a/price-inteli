import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { setOnAuthExpired } from "../../api/client";
import { fetchCurrentUser, login as loginRequest, logoutRequest, registerOrganization } from "./api";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./tokenStorage";

const AuthContext = createContext(undefined);

const EMPTY_ME = { user: null, organization: null, roles: [], permissions: [] };

export function AuthProvider({ children }) {
  const [status, setStatus] = useState("loading"); // "loading" | "authenticated" | "unauthenticated"
  const [me, setMe] = useState(EMPTY_ME);

  const clearAuth = useCallback(() => {
    clearTokens();
    setMe(EMPTY_ME);
    setStatus("unauthenticated");
  }, []);

  const loadCurrentUser = useCallback(async () => {
    try {
      const data = await fetchCurrentUser();
      setMe(data);
      setStatus("authenticated");
    } catch {
      clearAuth();
    }
  }, [clearAuth]);

  useEffect(() => {
    setOnAuthExpired(clearAuth);
    if (getAccessToken() || getRefreshToken()) {
      loadCurrentUser();
    } else {
      setStatus("unauthenticated");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async ({ email, password, rememberMe }) => {
      const tokens = await loginRequest({ email, password, rememberMe });
      setTokens({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        rememberMe: Boolean(rememberMe),
      });
      await loadCurrentUser();
    },
    [loadCurrentUser]
  );

  const register = useCallback(
    async (formValues) => {
      const tokens = await registerOrganization(formValues);
      setTokens({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        rememberMe: true,
      });
      await loadCurrentUser();
    },
    [loadCurrentUser]
  );

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } catch {
      // best-effort — tokens are discarded client-side regardless
    }
    clearAuth();
  }, [clearAuth]);

  const value = useMemo(
    () => ({
      status,
      isAuthenticated: status === "authenticated",
      user: me.user,
      organization: me.organization,
      roles: me.roles,
      permissions: me.permissions,
      hasPermission: (code) => me.permissions.includes(code),
      login,
      register,
      logout,
      refreshMe: loadCurrentUser,
    }),
    [status, me, login, register, logout, loadCurrentUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
