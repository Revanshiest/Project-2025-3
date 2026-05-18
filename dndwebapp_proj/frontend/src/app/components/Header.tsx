import { useState, useEffect } from "react";
import { Menu, X, Dices, Flame, Sparkles, LogIn, ChevronDown, User, MessageSquare, LogOut } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { AuthModal } from "./AuthModal";

const navLinks = [
  { name: "Главная", path: "/" },
  { name: "Справочник", path: "/handbook" },
  { name: "Инструменты", path: "/tools" },
  { name: "Глоссарий", path: "/glossary" },
];

interface User {
  id: number;
  username: string;
  email: string;
  avatar?: string;
}

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    // Check if user is logged in (from localStorage)
    const userData = localStorage.getItem("currentUser");
    if (userData) {
      setCurrentUser(JSON.parse(userData));
    }

    const hasVisited = localStorage.getItem("hasVisited");
    if (!hasVisited) {
      setAuthModalOpen(true);
      localStorage.setItem("hasVisited", "true");
    }
  }, []);

  const navigate = useNavigate();

  const handleLogin = (user: User) => {
    setCurrentUser(user);
    localStorage.setItem("currentUser", JSON.stringify(user));
    setAuthModalOpen(false);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem("currentUser");
    setUserMenuOpen(false);
    navigate("/");
  };

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#1A1A1A]/90 backdrop-blur-md border-b border-[#D4AF37]/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="relative w-10 h-10 flex items-center justify-center">
              {/* Custom DnD Logo: Dices with a subtle flame behind */}
              <Flame className="absolute inset-0 w-10 h-10 text-[#8B0000] opacity-80 group-hover:scale-110 transition-transform duration-500" />
              <Dices className="relative z-10 w-6 h-6 text-[#D4AF37] group-hover:rotate-12 transition-transform duration-500" />
              <div className="absolute inset-0 blur-md bg-[#D4AF37]/20 rounded-full group-hover:bg-[#D4AF37]/40 transition-colors duration-500" />
            </div>
            <span
              className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] tracking-wider"
              style={{ fontSize: "1.25rem" }}
            >
              D&D <span className="text-[#D4AF37]">Helper</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center flex-1 justify-center gap-12">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className="font-['Lora',serif] text-[#F4EBD0]/80 hover:text-[#D4AF37] transition-colors tracking-wide"
                style={{ fontSize: "1.05rem", lineHeight: "1.2" }}
              >
                {link.name}
              </Link>
            ))}
            <Link
              to="/my-works"
              className="font-['Lora',serif] text-[#F4EBD0]/80 hover:text-[#D4AF37] transition-colors tracking-wide"
              style={{ fontSize: "1.05rem", lineHeight: "1.2" }}
            >
              Мои работы
            </Link>
          </nav>

          <div className="hidden md:flex items-center gap-4">
            {currentUser ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-3 px-4 py-2 rounded-xl bg-[#D4AF37]/10 hover:bg-[#D4AF37]/20 border border-[#D4AF37]/30 transition-all duration-300 group"
                >
                  {currentUser.avatar ? (
                    <img
                      src={currentUser.avatar}
                      alt={currentUser.username}
                      className="w-8 h-8 rounded-full border-2 border-[#D4AF37]"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-[#D4AF37]/20 border-2 border-[#D4AF37] flex items-center justify-center">
                      <User className="w-4 h-4 text-[#D4AF37]" />
                    </div>
                  )}
                  <span className="font-['Lora',serif] text-[#F4EBD0] font-medium">
                    {currentUser.username}
                  </span>
                  <ChevronDown className={`w-4 h-4 text-[#D4AF37] transition-transform duration-300 ${userMenuOpen ? 'rotate-180' : ''}`} />
                </button>

                {userMenuOpen && (
                  <div className="absolute top-full right-0 mt-2 w-56 bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-xl shadow-2xl overflow-hidden z-50">
                    <div className="absolute top-0 right-8 -mt-2 w-5 h-5 rotate-45 bg-[#2c2722] border-t border-l border-[#D4AF37]/30 rounded-tl-md" />
                    <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-xl" />

                    <div className="relative z-10 pt-2">
                      <Link
                        to="/profile"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-3 text-[#F4EBD0] hover:bg-[#D4AF37]/10 transition-colors font-['Lora',serif]"
                      >
                        <User className="w-4 h-4 text-[#D4AF37]" />
                        <span>Мой профиль</span>
                      </Link>
                      <Link
                        to="/chat-history"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-3 text-[#F4EBD0] hover:bg-[#D4AF37]/10 transition-colors font-['Lora',serif]"
                      >
                        <MessageSquare className="w-4 h-4 text-[#D4AF37]" />
                        <span>История чатов</span>
                      </Link>
                      {currentUser?.username?.toLowerCase() === 'admin' && (
                        <Link
                          to="/admin"
                          onClick={() => setUserMenuOpen(false)}
                          className="flex items-center gap-3 px-4 py-3 text-[#F4EBD0] hover:bg-[#D4AF37]/10 transition-colors font-['Lora',serif]"
                        >
                          <Sparkles className="w-4 h-4 text-[#D4AF37]" />
                          <span>Админ-панель</span>
                        </Link>
                      )}
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 w-full px-4 py-3 text-[#F4EBD0] hover:bg-[#D4AF37]/10 transition-colors font-['Lora',serif]"
                      >
                        <LogOut className="w-4 h-4 text-[#D4AF37]" />
                        <span>Выйти</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setAuthModalOpen(true)}
                className="relative group px-6 py-2 font-['Cormorant_Garamond',serif] font-bold text-lg tracking-wide text-[#D4AF37] border-2 border-[#D4AF37] rounded-xl overflow-hidden transition-all duration-500 hover:shadow-[0_0_30px_rgba(212,175,55,0.5)]"
              >
                <div className="absolute inset-0 bg-[#D4AF37] opacity-0 group-hover:opacity-10 transition-opacity duration-500" />
                <Flame className="absolute inset-0 w-full h-full opacity-0 group-hover:opacity-20 text-[#8B0000] transition-opacity duration-500 blur-md" />
                <span className="relative flex items-center gap-2">
                  <LogIn className="w-5 h-5" />
                  Войти
                </span>
              </button>
            )}
          </div>

          <button
            className="md:hidden text-[#F4EBD0] p-2 -mr-2 hover:bg-[#F4EBD0]/10 rounded-full transition-colors"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {menuOpen && (
          <div className="md:hidden bg-[#1A1A1A]/95 backdrop-blur-md border-t border-[#D4AF37]/10 px-6 py-4 flex flex-col gap-4 shadow-xl">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className="font-['Lora',serif] text-[#F4EBD0]/80 hover:text-[#D4AF37] transition-colors py-2"
                onClick={() => setMenuOpen(false)}
              >
                {link.name}
              </Link>
            ))}
            <Link
              to="/tools"
              className="font-['Lora',serif] text-[#F4EBD0]/80 hover:text-[#D4AF37] transition-colors py-2"
              onClick={() => setMenuOpen(false)}
            >
              Инструменты
            </Link>
            <Link
              to="/my-works"
              className="font-['Lora',serif] text-[#F4EBD0]/80 hover:text-[#D4AF37] transition-colors py-2"
              onClick={() => setMenuOpen(false)}
            >
              Мои работы
            </Link>

            {currentUser ? (
              <div className="border-t border-[#D4AF37]/20 pt-4 mt-2">
                <div className="flex items-center gap-3 mb-4">
                  {currentUser.avatar ? (
                    <img
                      src={currentUser.avatar}
                      alt={currentUser.username}
                      className="w-8 h-8 rounded-full border-2 border-[#D4AF37]"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-[#D4AF37]/20 border-2 border-[#D4AF37] flex items-center justify-center">
                      <User className="w-4 h-4 text-[#D4AF37]" />
                    </div>
                  )}
                  <span className="font-['Lora',serif] text-[#F4EBD0] font-medium">
                    {currentUser.username}
                  </span>
                </div>
                <Link
                  to="/profile"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-3 w-full px-4 py-3 border border-[#D4AF37]/50 rounded-lg text-[#D4AF37] hover:bg-[#D4AF37]/10 transition-colors font-['Cormorant_Garamond',serif] font-medium tracking-wide mb-2"
                >
                  <User className="w-4 h-4" />
                  <span>Мой профиль</span>
                </Link>
                <Link
                  to="/chat-history"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-3 w-full px-4 py-3 border border-[#D4AF37]/50 rounded-lg text-[#D4AF37] hover:bg-[#D4AF37]/10 transition-colors font-['Cormorant_Garamond',serif] font-medium tracking-wide mb-2"
                >
                  <MessageSquare className="w-4 h-4" />
                  <span>История чатов</span>
                </Link>
                {currentUser?.username?.toLowerCase() === 'admin' && (
                  <Link
                    to="/admin"
                    onClick={() => setMenuOpen(false)}
                    className="flex items-center gap-3 w-full px-4 py-3 border border-[#D4AF37]/50 rounded-lg text-[#D4AF37] hover:bg-[#D4AF37]/10 transition-colors font-['Cormorant_Garamond',serif] font-medium tracking-wide mb-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Админ-панель</span>
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 w-full px-4 py-3 bg-[#D4AF37]/20 border-2 border-[#D4AF37] rounded-lg text-[#D4AF37] hover:bg-[#D4AF37]/30 transition-colors font-['Cormorant_Garamond',serif] font-bold tracking-wide text-lg"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Выйти</span>
                </button>
              </div>
            ) : (
              <button
                className="flex items-center justify-center gap-2 w-full mt-2 px-5 py-3 bg-[#D4AF37]/20 border-2 border-[#D4AF37] rounded-lg text-[#D4AF37] hover:bg-[#D4AF37]/30 transition-colors font-['Cormorant_Garamond',serif] font-bold tracking-wide text-lg"
                onClick={() => {
                  setAuthModalOpen(true);
                  setMenuOpen(false);
                }}
              >
                <LogIn className="w-5 h-5" />
                <span>Войти</span>
              </button>
            )}
          </div>
        )}
      </header>

      {authModalOpen && <AuthModal onClose={() => setAuthModalOpen(false)} onLogin={handleLogin} />}
    </>
  );
}