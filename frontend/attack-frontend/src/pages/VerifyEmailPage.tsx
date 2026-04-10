import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { verifyEmailApi } from "../api/auth";

const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [message, setMessage] = useState("正在驗證 Email...");

  useEffect(() => {
    const runVerification = async () => {
      if (!token) {
        setSuccess(false);
        setMessage("缺少驗證 token，請重新檢查驗證連結。");
        setLoading(false);
        return;
      }

      try {
        const result = await verifyEmailApi(token);
        setSuccess(true);
        setMessage(result?.message ?? "Email 驗證成功，現在可以登入。");
      } catch (error) {
        setSuccess(false);
        setMessage(error instanceof Error ? error.message : "Email 驗證失敗");
      } finally {
        setLoading(false);
      }
    };

    runVerification();
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 px-4 text-white">
      <div className="w-full max-w-md rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-xl">
        <h1 className="mb-4 text-2xl font-bold">Email 驗證</h1>

        <p className="mb-6 text-sm text-white/75">{message}</p>

        {loading ? (
          <div className="text-sm text-lime-300">驗證中，請稍候...</div>
        ) : success ? (
          <div className="space-y-4">
            <div className="rounded-2xl border border-lime-400/30 bg-lime-400/10 p-4 text-sm text-lime-200">
              驗證成功，你現在可以登入系統。
            </div>
            <Link
              to="/login"
              className="inline-flex w-full justify-center rounded-full bg-lime-300 px-5 py-3 font-semibold text-black transition hover:bg-lime-200"
            >
              前往登入
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-2xl border border-red-400/30 bg-red-400/10 p-4 text-sm text-red-200">
              驗證失敗，連結可能已失效或 token 不正確。
            </div>
            <Link
              to="/login"
              className="inline-flex w-full justify-center rounded-full bg-white/10 px-5 py-3 font-semibold text-white transition hover:bg-white/20"
            >
              返回登入
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmailPage;