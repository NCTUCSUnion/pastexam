export function decodeToken(token) {
  if (!token) return null;

  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );

    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error("Error decoding token:", error);
    return null;
  }
}

export function getCurrentUser() {
  const token = localStorage.getItem("authToken");
  if (!token) return null;

  const decoded = decodeToken(token);
  if (!decoded) return null;

  return {
    id: decoded.uid,
    email: decoded.email,
    name: decoded.name,
    is_admin: decoded.is_admin || false,
    avatar: decoded.avatar_url,
    roles: decoded.realm_roles || {},
  };
}

export function isAuthenticated() {
  const token = localStorage.getItem("authToken");
  if (!token) return false;

  const decoded = decodeToken(token);
  if (!decoded) return false;

  const currentTime = Math.floor(Date.now() / 1000);
  const bufferTime = 60;

  return decoded.exp > currentTime - bufferTime;
}
