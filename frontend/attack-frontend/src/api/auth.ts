const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function loginApi(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${BASE_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }).toString(),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? "登入失敗");
  }
  return res.json();
}

export async function registerApi(email: string, password: string) {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail ?? "註冊失敗");
  }
  return res.json();
}