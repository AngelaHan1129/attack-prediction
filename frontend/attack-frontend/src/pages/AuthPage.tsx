import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function AuthPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [isLogin, setIsLogin] = useState(true);
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      if (isLogin) {
        await login(identifier, password);
        navigate("/dashboard");
      } else {
        await register({
          username,
          email,
          password,
        });
        setMessage("註冊成功，請先到信箱或後端 console 取得驗證連結完成 Email 驗證後再登入。");
        setIsLogin(true);
        setIdentifier(email);
        setPassword("");
      }
    } catch (err: any) {
      setError(err?.message || "操作失敗");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="bg-white p-8 rounded-2xl shadow-md w-full max-w-sm">
        <h2 className="text-2xl font-bold mb-6 text-center">
          {isLogin ? "登入" : "註冊"}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isLogin ? (
            <div>
              <label htmlFor="identifier" className="block text-sm font-medium mb-1">
                使用者名稱或電子郵件
              </label>
              <input
                id="identifier"
                name="username"
                type="text"
                autoComplete="username"
                placeholder="請輸入使用者名稱或 user@example.com"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
                required
              />
            </div>
          ) : (
            <>
              <div>
                <label htmlFor="username" className="block text-sm font-medium mb-1">
                  使用者名稱
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  placeholder="請輸入使用者名稱"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  required
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-1">
                  電子郵件
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  placeholder="user@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  required
                />
              </div>
            </>
          )}

          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              密碼
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete={isLogin ? "current-password" : "new-password"}
              placeholder={isLogin ? "請輸入密碼" : "請設定密碼"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
              required
            />
          </div>

          {message && <p className="text-green-600 text-sm">{message}</p>}
          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 disabled:opacity-60 text-white py-2 rounded-lg font-semibold transition"
          >
            {loading ? "處理中..." : isLogin ? "登入" : "註冊"}
          </button>
        </form>

        <p className="text-center text-sm mt-4 text-gray-500">
          {isLogin ? "還沒有帳號？" : "已有帳號？"}
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
              setMessage("");
              setPassword("");
            }}
            className="text-blue-500 ml-1 hover:underline"
          >
            {isLogin ? "註冊" : "登入"}
          </button>
        </p>
      </div>
    </div>
  );
}