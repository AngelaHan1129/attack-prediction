const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

async function parseError(res: Response, fallback: string): Promise<string> {
  const err = await res.json().catch(() => null);

  if (Array.isArray(err?.detail)) {
    return err.detail
      .map((item: any) => {
        const path = Array.isArray(item?.loc) ? item.loc.join(" > ") : "欄位";
        return `${path}：${item?.msg ?? "格式錯誤"}`;
      })
      .join("；");
  }

  if (typeof err?.detail === "string") {
    return err.detail;
  }

  return fallback;
}

export async function loginApi(
  identifier: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${BASE_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      username: identifier,
      password,
    }).toString(),
  });

  if (!res.ok) {
    throw new Error(await parseError(res, "登入失敗"));
  }

  return res.json();
}

export async function registerApi(payload: RegisterPayload) {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => null);
  console.log("register response:", res.status, data);

  if (!res.ok) {
    if (Array.isArray(data?.detail)) {
      throw new Error(
        data.detail
          .map((item: any) => {
            const path = Array.isArray(item?.loc) ? item.loc.join(" > ") : "欄位";
            return `${path}：${item?.msg ?? "格式錯誤"}`;
          })
          .join("；")
      );
    }

    if (typeof data?.detail === "string") {
      throw new Error(data.detail);
    }

    throw new Error("註冊失敗");
  }

  return data;
}

export async function verifyEmailApi(token: string) {
  const res = await fetch(`${BASE_URL}/auth/verify-email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });

  if (!res.ok) {
    throw new Error(await parseError(res, "Email 驗證失敗"));
  }

  return res.json();
}