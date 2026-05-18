"use client";

import { useEffect } from "react";
import { Outlet, useLocation } from "react-router";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { AIChatFAB } from "./components/AIChatFAB";

const titleMap: Record<string, string> = {
  "/": "Главная",
  "/handbook": "Справочник",
  "/glossary": "Глоссарий",
  "/create-character": "Создание героя",
  "/my-works": "Мои работы",
  "/profile": "Мой профиль",
  "/chat-history": "История чатов",
  "/admin": "Админ-панель",
};

export function Root() {
  const location = useLocation();

  useEffect(() => {
    const title = titleMap[location.pathname] || "D&D Helper";
    document.title = `${title}`;
  }, [location.pathname]);
  return (
    <div
      className="min-h-screen bg-[#1A1A1A] text-[#F4EBD0]"
      style={{ fontFamily: "'Google Sans', sans-serif" }}
    >
      <Header />
      <main>
        <Outlet />
      </main>
      <Footer />
      <AIChatFAB />
    </div>
  );
}