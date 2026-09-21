// Access + refresh tokens only — never store the password anywhere.
// "Remember me" decides which Web Storage the tokens live in: localStorage
// persists across browser restarts, sessionStorage is cleared when the tab
// closes. Tokens are plain JWTs kept client-side; the backend has no
// server-side session to invalidate yet (see the /auth/logout endpoint).
const ACCESS_TOKEN_KEY = "rpip_access_token";
const REFRESH_TOKEN_KEY = "rpip_refresh_token";

function storageFor(persist) {
  return persist ? window.localStorage : window.sessionStorage;
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) ?? sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY) ?? sessionStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens({ accessToken, refreshToken, rememberMe }) {
  clearTokens();
  const storage = storageFor(rememberMe);
  storage.setItem(ACCESS_TOKEN_KEY, accessToken);
  storage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function setAccessToken(accessToken) {
  const persisted = Boolean(localStorage.getItem(REFRESH_TOKEN_KEY));
  storageFor(persisted).setItem(ACCESS_TOKEN_KEY, accessToken);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}
