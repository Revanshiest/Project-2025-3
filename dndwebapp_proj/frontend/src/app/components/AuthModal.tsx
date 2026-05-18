import { useState, useEffect } from "react";
import { X, Sparkles } from "lucide-react";

interface AuthModalProps {
  onClose: () => void;
  onLogin?: (user: { id: number; username: string; email: string; avatar?: string }) => void;
}

// Simple hash function to generate numeric ID from email
function hashEmailToId(email: string): number {
  let hash = 0;
  for (let i = 0; i < email.length; i++) {
    const char = email.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash) || 1; // Fallback to 1 if empty
}

export function AuthModal({ onClose, onLogin }: AuthModalProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isLogin) {
      // Simulate login - in real app this would be API call
      const user = {
        id: hashEmailToId(email),
        username: "Адриан", // Default username for demo
        email: email,
        avatar: undefined
      };
      onLogin?.(user);
    } else {
      // Simulate registration
      if (password !== confirmPassword) {
        alert("Пароли не совпадают!");
        return;
      }
      const user = {
        id: hashEmailToId(email),
        username: username,
        email: email,
        avatar: undefined
      };
      onLogin?.(user);
    }
    
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl shadow-2xl overflow-visible">
        {/* Texture overlay */}
        <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

        <button
          onClick={onClose}
          className="absolute -top-4 -right-4 z-20 p-2 rounded-full bg-[#D4AF37] hover:bg-[#D4AF37]/80 text-[#1A1A1A] transition-all hover:scale-110 shadow-lg"
        >
          <X className="w-6 h-6" />
        </button>

        <div className="relative z-10 p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="font-['Cormorant_Garamond',serif] font-bold uppercase text-[#D4AF37] tracking-[0.2em] mb-2" style={{ fontSize: '0.9rem' }}>
              {isLogin ? "Добро пожаловать" : "Присоединись"}
            </h2>
            <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: '2rem', lineHeight: 1.2 }}>
              {isLogin ? "Вход в портал" : "Создание профиля"}
            </h3>
            <div className="w-12 h-1 bg-[#D4AF37] mx-auto mt-4 opacity-60" />
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block font-['Lora',serif] text-[#D4AF37] text-sm mb-2 tracking-wide">
                  Ник персонажа
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 bg-[#111]/80 backdrop-blur-sm border-2 border-[#D4AF37]/20 rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/40 font-['Lora',serif] focus:outline-none focus:border-[#D4AF37]/60 focus:bg-[#1A1A1A]/90 focus:shadow-[0_0_30px_rgba(212,175,55,0.15)] transition-all"
                  placeholder="Введите имя персонажа"
                  required
                />
              </div>
            )}

            <div>
              <label className="block font-['Lora',serif] text-[#D4AF37] text-sm mb-2 tracking-wide">
                Электронная почта
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-[#111]/80 backdrop-blur-sm border-2 border-[#D4AF37]/20 rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/40 font-['Lora',serif] focus:outline-none focus:border-[#D4AF37]/60 focus:bg-[#1A1A1A]/90 focus:shadow-[0_0_30px_rgba(212,175,55,0.15)] transition-all"
                placeholder="ваша@почта.ру"
                required
              />
            </div>

            <div>
              <label className="block font-['Lora',serif] text-[#D4AF37] text-sm mb-2 tracking-wide">
                Пароль
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#111]/80 backdrop-blur-sm border-2 border-[#D4AF37]/20 rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/40 font-['Lora',serif] focus:outline-none focus:border-[#D4AF37]/60 focus:bg-[#1A1A1A]/90 focus:shadow-[0_0_30px_rgba(212,175,55,0.15)] transition-all"
                placeholder="••••••••"
                required
              />
            </div>

            {!isLogin && (
              <div>
                <label className="block font-['Lora',serif] text-[#D4AF37] text-sm mb-2 tracking-wide">
                  Подтвердите пароль
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-[#111]/80 backdrop-blur-sm border-2 border-[#D4AF37]/20 rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/40 font-['Lora',serif] focus:outline-none focus:border-[#D4AF37]/60 focus:bg-[#1A1A1A]/90 focus:shadow-[0_0_30px_rgba(212,175,55,0.15)] transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              className="relative group w-full mt-6 px-6 py-3 font-['Cormorant_Garamond',serif] font-bold text-lg tracking-wide text-[#D4AF37] border-2 border-[#D4AF37] rounded-xl overflow-hidden transition-all duration-500 hover:shadow-[0_0_30px_rgba(212,175,55,0.5)]"
            >
              <div className="absolute inset-0 bg-[#D4AF37] opacity-0 group-hover:opacity-10 transition-opacity duration-500" />
              <span className="relative flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5" />
                {isLogin ? "Войти в миры" : "Создать героя"}
              </span>
            </button>
          </form>

          {/* Toggle Form */}
          <div className="mt-6 text-center">
            <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm mb-2">
              {isLogin ? "Нет аккаунта?" : "Уже есть аккаунт?"}
            </p>
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setEmail("");
                setPassword("");
                setUsername("");
                setConfirmPassword("");
              }}
              className="font-['Lora',serif] font-medium text-[#D4AF37] hover:text-[#F4EBD0] transition-colors tracking-wide underline"
            >
              {isLogin ? "Зарегистрироваться" : "Войти"}
            </button>
          </div>

          {/* Decorative text */}
          <p className="mt-8 font-['Lora',serif] text-[#F4EBD0]/50 text-xs text-center italic">
            "В магии нет проверок личности, только слово честь авантюриста"
          </p>
        </div>
      </div>
    </div>
  );
}
