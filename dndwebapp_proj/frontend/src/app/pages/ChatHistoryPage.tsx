import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { MessageSquare, Calendar, Clock, User, Bot, Search, Filter } from "lucide-react";
import { api } from "../../api/client";

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  lastActivity: string;
  messageCount: number;
  messages: ChatMessage[];
  isActive: boolean;
}

export function ChatHistoryPage() {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [selectedChat, setSelectedChat] = useState<ChatSession | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<'all' | 'active' | 'completed'>('all');
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem('currentUser');
    if (!userData) {
      navigate('/');
      return;
    }
    const user = JSON.parse(userData);
    const userId = user.id;

    const loadChats = async () => {
      try {
        const chats = await api.ai.getChats(userId);
        const mapped: ChatSession[] = chats.map((c: any) => ({
          id: c.id,
          title: c.title,
          createdAt: c.createdAt,
          lastActivity: c.lastActivity,
          messageCount: c.messageCount || 0,
          messages: (c.messages || []).map((m: any) => ({
            id: m.id,
            sender: m.sender === 'user' ? 'user' as const : 'assistant' as const,
            content: m.content,
            timestamp: m.timestamp
          })),
          isActive: c.isActive !== undefined ? c.isActive : true
        }));
        setChatSessions(mapped);
        if (mapped.length > 0) {
          setSelectedChat(mapped[0]);
        }
      } catch (err) {
        console.error("Failed to fetch chats:", err);
      }
    };
    loadChats();
  }, [navigate]);

  const filteredChats = chatSessions.filter(chat => {
    const matchesSearch = chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         chat.messages.some(msg => msg.content.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesFilter = filterType === 'all' ||
                         (filterType === 'active' && chat.isActive) ||
                         (filterType === 'completed' && !chat.isActive);

    return matchesSearch && matchesFilter;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-[#1A1A1A] pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: 'clamp(2.5rem, 8vw, 4rem)', lineHeight: 1.2 }}>
            История <span className="text-[#D4AF37]">Чатов</span>
          </h1>
          <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-base sm:text-lg mt-4 max-w-2xl mx-auto">
            Ваши беседы с ИИ-мастером и сохраненные истории приключений
          </p>
          <div className="w-16 h-1 bg-[#D4AF37] mx-auto mt-6 opacity-60" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8">
          {/* Chat List — on mobile, hidden when a chat is selected */}
          <div className={`lg:col-span-4 ${selectedChat ? 'hidden lg:block' : 'block'}`}>
            <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-5 sm:p-6 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500">
              <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

              <div className="relative z-10">
                <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-2xl mb-2 pl-1">
                  Поиск чатов
                </h3>
                <p className="font-['Lora',serif] text-[#F4EBD0]/60 text-sm mb-6 pl-1">
                  Найдите нужную беседу или переключитесь между активными и завершёнными.
                </p>

                {/* Search and Filter */}
                <div className="mb-6 space-y-4">
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Поиск чатов..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-4 pr-12 py-3 bg-[#111]/80 backdrop-blur-sm border border-[#D4AF37]/20 rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/40 font-['Lora',serif] focus:outline-none focus:border-[#D4AF37]/60 transition-all text-sm"
                    />
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#D4AF37]/70" />
                  </div>

                  <div className="flex gap-2">
                    {[
                      { key: 'all', label: 'Все' },
                      { key: 'active', label: 'Активные' },
                      { key: 'completed', label: 'Завершенные' }
                    ].map((filter) => (
                      <button
                        key={filter.key}
                        onClick={() => setFilterType(filter.key as any)}
                        className={`px-3 py-1 rounded-lg text-xs font-['Lora',serif] transition-all ${
                          filterType === filter.key
                            ? 'bg-[#D4AF37] text-[#1A1A1A]'
                            : 'bg-[#111]/50 text-[#F4EBD0]/70 hover:text-[#D4AF37] hover:bg-[#D4AF37]/10'
                        }`}
                      >
                        {filter.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Chat List */}
                <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-[#D4AF37]/20 scrollbar-track-transparent">
                  {filteredChats.map((chat) => (
                    <button
                      key={chat.id}
                      onClick={() => setSelectedChat(chat)}
                      className={`w-full p-4 rounded-xl border transition-all duration-300 text-left ${
                        selectedChat?.id === chat.id
                          ? 'border-[#D4AF37] bg-[#D4AF37]/10 shadow-[0_0_20px_rgba(212,175,55,0.3)]'
                          : 'border-[#D4AF37]/20 bg-[#111]/50 hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-sm line-clamp-2">
                          {chat.title}
                        </h4>
                        {chat.isActive && (
                          <div className="w-2 h-2 bg-[#D4AF37] rounded-full animate-pulse ml-2 flex-shrink-0" />
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-['Lora',serif] text-[#F4EBD0]/60 flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(chat.createdAt)}
                        </span>
                        <span className="font-['Lora',serif] text-[#D4AF37]">
                          {chat.messageCount} сообщ.
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Chat Content — on mobile, shown only when a chat is selected */}
          <div className={`lg:col-span-8 ${selectedChat ? 'block' : 'hidden lg:block'}`}>
            {selectedChat && (
              /* Mobile back button */
              <button
                onClick={() => setSelectedChat(null)}
                className="lg:hidden mb-4 flex items-center gap-2 text-[#D4AF37] hover:text-[#F4EBD0] transition-colors font-['Lora',serif] text-sm"
              >
                ← Вернуться к списку
              </button>
            )}
            {selectedChat ? (
              <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-6 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500">
                <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

                <div className="relative z-10">
                  {/* Chat Header */}
                  <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#D4AF37]/20">
                    <div>
                      <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-2xl mb-1">
                        {selectedChat.title}
                      </h2>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="font-['Lora',serif] text-[#F4EBD0]/70 flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          {formatDate(selectedChat.createdAt)}
                        </span>
                        <span className="font-['Lora',serif] text-[#F4EBD0]/70 flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {formatTime(selectedChat.lastActivity)}
                        </span>
                        <span className="font-['Lora',serif] text-[#D4AF37]">
                          {selectedChat.messageCount} сообщений
                        </span>
                      </div>
                    </div>
                    {selectedChat.isActive && (
                      <div className="flex items-center gap-2 px-3 py-1 bg-[#D4AF37]/20 rounded-full">
                        <div className="w-2 h-2 bg-[#D4AF37] rounded-full animate-pulse" />
                        <span className="font-['Lora',serif] text-[#D4AF37] text-sm">
                          Активный
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Messages */}
                  <div className="space-y-6 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-[#D4AF37]/20 scrollbar-track-transparent pr-4">
                    {selectedChat.messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex gap-4 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`flex gap-3 max-w-[80%] ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                          {/* Avatar */}
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                            message.sender === 'user'
                              ? 'bg-[#D4AF37]/20 border-2 border-[#D4AF37]'
                              : 'bg-[#8B0000]/20 border-2 border-[#8B0000]'
                          }`}>
                            {message.sender === 'user' ? (
                              <User className="w-4 h-4 text-[#D4AF37]" />
                            ) : (
                              <Bot className="w-4 h-4 text-[#8B0000]" />
                            )}
                          </div>

                          {/* Message */}
                          <div className={`rounded-2xl px-4 py-3 ${
                            message.sender === 'user'
                              ? 'bg-[#D4AF37]/20 border border-[#D4AF37]/30'
                              : 'bg-[#111]/50 border border-[#D4AF37]/20'
                          }`}>
                            <p className="font-['Lora',serif] text-[#F4EBD0] text-sm leading-relaxed whitespace-pre-wrap">
                              {message.content}
                            </p>
                            <span className="font-['Lora',serif] text-[#F4EBD0]/50 text-xs mt-2 block">
                              {formatTime(message.timestamp)}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Continue Chat Button */}
                  {selectedChat.isActive && (
                    <div className="mt-6 pt-4 border-t border-[#D4AF37]/20">
                      <button
                        onClick={() => {
                          const event = new CustomEvent("open_ai_chat", {
                            detail: { chatId: selectedChat.id }
                          });
                          window.dispatchEvent(event);
                        }}
                        className="w-full px-6 py-3 bg-[#D4AF37]/20 border-2 border-[#D4AF37] rounded-xl text-[#D4AF37] hover:bg-[#D4AF37]/30 transition-all duration-300 font-['Cormorant_Garamond',serif] font-bold"
                      >
                        Продолжить чат
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-12 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500">
                <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

                <div className="relative z-10 text-center">
                  <MessageSquare className="w-16 h-16 text-[#D4AF37]/50 mx-auto mb-4" />
                  <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-xl mb-2">
                    Выберите чат
                  </h3>
                  <p className="font-['Lora',serif] text-[#F4EBD0]/70">
                    Выберите чат из списка слева, чтобы просмотреть историю сообщений
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
