import { useState, useRef, useEffect, ChangeEvent } from "react";
import { useNavigate } from "react-router";
import { User, Camera, Save, X, Mail, Calendar, Trophy, MessageSquare, Dice6, Loader2 } from "lucide-react";
import { api } from "../../api/client";

interface UserProfile {
  username: string;
  email: string;
  avatar?: string;
  bio?: string;
  joinDate: string;
  stats: {
    characters: number;
    chats: number;
    diceRolls: number;
    campaigns: number;
  };
}

export function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedBio, setEditedBio] = useState("");
  const [statsLoading, setStatsLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem("currentUser");
    if (!userData) {
      navigate("/");
      return;
    }

    const parsedUser = JSON.parse(userData);
    const userId = parsedUser.id || 1;

    // Set initial layout values
    setUser({
      ...parsedUser,
      bio: parsedUser.bio || "Мастер подземелий и повелитель кубиков судьбы.",
      joinDate: parsedUser.joinDate || "2024-01-01",
      stats: {
        characters: 0,
        chats: 0,
        diceRolls: 127,
        campaigns: 3,
      },
    });
    setEditedBio(parsedUser.bio || "Мастер подземелий и повелитель кубиков судьбы.");

    const fetchLiveStats = async () => {
      try {
        setStatsLoading(true);
        const charactersData = await api.characters.getUserCharacters(userId);
        const chatsData = await api.ai.getChats(userId);
        
        setUser(prev => prev ? {
          ...prev,
          stats: {
            characters: charactersData.length,
            chats: chatsData.length,
            diceRolls: 127,
            campaigns: 3,
          }
        } : null);
      } catch (err) {
        console.error("Failed to load user profile dynamic stats:", err);
      } finally {
        setStatsLoading(false);
      }
    };
    fetchLiveStats();
  }, [navigate]);

  const handleAvatarUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const avatarUrl = e.target?.result as string;
        if (user) {
          const updatedUser = { ...user, avatar: avatarUrl };
          setUser(updatedUser);
          localStorage.setItem("currentUser", JSON.stringify(updatedUser));
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveBio = () => {
    if (user) {
      const updatedUser = { ...user, bio: editedBio };
      setUser(updatedUser);
      localStorage.setItem("currentUser", JSON.stringify(updatedUser));
      setIsEditing(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-[#1A1A1A] pt-24 pb-16 flex items-center justify-center">
        <div className="text-center">
          <User className="w-16 h-16 text-[#D4AF37]/50 mx-auto mb-4" />
          <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-lg">
            Загрузка профиля...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1A1A1A] pt-24 pb-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: 'clamp(2.5rem, 8vw, 4rem)', lineHeight: 1.2 }}>
            Мой <span className="text-[#D4AF37]">Профиль</span>
          </h1>
          <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-base sm:text-lg mt-4">
            Управляйте своим авантюрным профилем
          </p>
          <div className="w-16 h-1 bg-[#D4AF37] mx-auto mt-6 opacity-60" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Profile Card */}
          <div className="lg:col-span-1">
            <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-8 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500">
              {/* Texture overlay */}
              <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

              <div className="relative z-10 text-center">
                {/* Avatar */}
                <div className="relative mb-6">
                  <div className="w-32 h-32 mx-auto rounded-full border-4 border-[#D4AF37] overflow-hidden bg-[#111]">
                    {user.avatar ? (
                      <img
                        src={user.avatar}
                        alt={user.username}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <User className="w-16 h-16 text-[#D4AF37]" />
                      </div>
                    )}
                  </div>

                  {/* Upload button */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="absolute bottom-0 right-1/2 translate-x-16 w-10 h-10 bg-[#D4AF37] hover:bg-[#D4AF37]/80 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-110 shadow-lg"
                  >
                    <Camera className="w-5 h-5 text-[#1A1A1A]" />
                  </button>

                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarUpload}
                    className="hidden"
                  />
                </div>

                {/* User Info */}
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-2xl mb-2">
                  {user.username}
                </h2>

                <div className="flex items-center justify-center gap-2 mb-4">
                  <Mail className="w-4 h-4 text-[#D4AF37]" />
                  <span className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm">
                    {user.email}
                  </span>
                </div>

                <div className="flex items-center justify-center gap-2 mb-6">
                  <Calendar className="w-4 h-4 text-[#D4AF37]" />
                  <span className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm">
                    Присоединился {new Date(user.joinDate).toLocaleDateString('ru-RU')}
                  </span>
                </div>

                {/* Bio */}
                <div className="mb-6">
                  <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-lg mb-3">
                    О себе
                  </h3>
                  {isEditing ? (
                    <div className="space-y-3">
                      <textarea
                        value={editedBio}
                        onChange={(e) => setEditedBio(e.target.value)}
                        rows={3}
                        className="w-full px-4 py-3 bg-[#111]/80 backdrop-blur-sm border-2 border-[#D4AF37]/20 rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/40 font-['Lora',serif] focus:outline-none focus:border-[#D4AF37]/60 focus:bg-[#1A1A1A]/90 focus:shadow-[0_0_30px_rgba(212,175,55,0.15)] transition-all resize-none"
                        placeholder="Расскажите о себе..."
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveBio}
                          className="flex-1 px-4 py-2 bg-[#D4AF37]/20 border-2 border-[#D4AF37] rounded-lg text-[#D4AF37] hover:bg-[#D4AF37]/30 transition-colors font-['Cormorant_Garamond',serif] font-bold text-sm"
                        >
                          Сохранить
                        </button>
                        <button
                          onClick={() => {
                            setIsEditing(false);
                            setEditedBio(user.bio || "");
                          }}
                          className="px-4 py-2 border-2 border-[#D4AF37]/30 rounded-lg text-[#D4AF37]/70 hover:text-[#D4AF37] hover:border-[#D4AF37]/50 transition-colors font-['Cormorant_Garamond',serif] font-bold text-sm"
                        >
                          Отмена
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div
                      onClick={() => setIsEditing(true)}
                      className="p-4 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20 hover:border-[#D4AF37]/50 transition-all duration-300 cursor-pointer"
                    >
                      <p className="font-['Lora',serif] text-[#F4EBD0]/80 text-sm leading-relaxed">
                        {user.bio}
                      </p>
                      <p className="font-['Lora',serif] text-[#D4AF37]/60 text-xs mt-2">
                        Нажмите для редактирования
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Stats and Activity */}
          <div className="lg:col-span-2 space-y-8">
            {/* Stats */}
            <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-5 sm:p-8 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500">
              <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

              <div className="relative z-10">
                <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6">
                  Статистика Авантюриста
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20 flex flex-col justify-between min-h-[125px] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5 transition-all duration-300">
                    <User className="w-8 h-8 text-[#D4AF37] mx-auto mb-2" />
                    <div className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-2xl mb-1 flex justify-center items-center h-8">
                      {statsLoading ? (
                        <Loader2 className="w-5 h-5 text-[#D4AF37] animate-spin" />
                      ) : (
                        user.stats.characters
                      )}
                    </div>
                    <div className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm mt-auto">
                      Персонажей
                    </div>
                  </div>

                  <div className="text-center p-4 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20 flex flex-col justify-between min-h-[125px] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5 transition-all duration-300">
                    <MessageSquare className="w-8 h-8 text-[#D4AF37] mx-auto mb-2" />
                    <div className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-2xl mb-1 flex justify-center items-center h-8">
                      {statsLoading ? (
                        <Loader2 className="w-5 h-5 text-[#D4AF37] animate-spin" />
                      ) : (
                        user.stats.chats
                      )}
                    </div>
                    <div className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm mt-auto">
                      Чатов
                    </div>
                  </div>

                  <div className="text-center p-4 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20 flex flex-col justify-between min-h-[125px] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5 transition-all duration-300">
                    <Dice6 className="w-8 h-8 text-[#D4AF37] mx-auto mb-2" />
                    <div className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-2xl mb-1 flex justify-center items-center h-8">
                      {user.stats.diceRolls}
                    </div>
                    <div className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm mt-auto">
                      Бросков
                    </div>
                  </div>

                  <div className="text-center p-4 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20 flex flex-col justify-between min-h-[125px] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5 transition-all duration-300">
                    <Trophy className="w-8 h-8 text-[#D4AF37] mx-auto mb-2" />
                    <div className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-2xl mb-1 flex justify-center items-center h-8">
                      {user.stats.campaigns}
                    </div>
                    <div className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm mt-auto">
                      Кампаний
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-5 sm:p-8 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500">
              <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

              <div className="relative z-10">
                <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6">
                  Недавняя Активность
                </h3>

                <div className="space-y-4">
                  <div className="flex items-center gap-4 p-4 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20">
                    <div className="w-10 h-10 rounded-full bg-[#D4AF37]/20 flex items-center justify-center">
                      <User className="w-5 h-5 text-[#D4AF37]" />
                    </div>
                    <div className="flex-1">
                      <p className="font-['Lora',serif] text-[#F4EBD0] text-sm">
                        Создан новый персонаж <span className="text-[#D4AF37] font-medium">Элдрин Теневой</span>
                      </p>
                      <p className="font-['Lora',serif] text-[#F4EBD0]/60 text-xs">
                        2 часа назад
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 p-4 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20">
                    <div className="w-10 h-10 rounded-full bg-[#D4AF37]/20 flex items-center justify-center">
                      <Dice6 className="w-5 h-5 text-[#D4AF37]" />
                    </div>
                    <div className="flex-1">
                      <p className="font-['Lora',serif] text-[#F4EBD0] text-sm">
                        Совершено <span className="text-[#D4AF37] font-medium">15 бросков кубиков</span>
                      </p>
                      <p className="font-['Lora',serif] text-[#F4EBD0]/60 text-xs">
                        4 часа назад
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 p-4 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20">
                    <div className="w-10 h-10 rounded-full bg-[#D4AF37]/20 flex items-center justify-center">
                      <MessageSquare className="w-5 h-5 text-[#D4AF37]" />
                    </div>
                    <div className="flex-1">
                      <p className="font-['Lora',serif] text-[#F4EBD0] text-sm">
                        Завершен чат <span className="text-[#D4AF37] font-medium">"Квест в Забытые Королевства"</span>
                      </p>
                      <p className="font-['Lora',serif] text-[#F4EBD0]/60 text-xs">
                        Вчера
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
