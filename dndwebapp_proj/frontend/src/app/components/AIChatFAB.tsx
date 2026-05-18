import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { X, Send, Sparkles, Wand2, Loader2 } from "lucide-react";
import { api } from "../../api/client";

export function AIChatFAB() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "ai" as const, text: "Приветствую, путник! Я твой Тайный Проводник. Спроси меня о правилах, заклинаниях или лоре." },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatId, setChatId] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    const handleOpenChat = async (e: Event) => {
      const customEvent = e as CustomEvent;
      const targetChatId = customEvent.detail?.chatId;
      if (targetChatId) {
        setChatId(targetChatId);
        const userStr = localStorage.getItem("currentUser");
        const userId = userStr ? JSON.parse(userStr).id : 1;
        try {
          const session = await api.ai.getChatSession(userId, targetChatId);
          if (session && session.messages) {
            setMessages(session.messages.map((m: any) => ({
              role: m.sender === 'user' ? 'user' as const : 'ai' as const,
              text: m.content
            })));
          }
        } catch (err) {
          console.error("Failed to load chat session:", err);
        }
      } else {
        setChatId(undefined);
        setMessages([
          { role: "ai" as const, text: "Приветствую, путник! Я твой Тайный Проводник. Спроси меня о правилах, заклинаниях или лоре." }
        ]);
      }
      setOpen(true);
    };

    window.addEventListener("open_ai_chat", handleOpenChat);
    return () => {
      window.removeEventListener("open_ai_chat", handleOpenChat);
    };
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = input;
    setMessages((m) => [...m, { role: "user" as const, text: userMessage }]);
    setInput("");
    setIsLoading(true);
    
    const userStr = localStorage.getItem("currentUser");
    const userId = userStr ? JSON.parse(userStr).id : 1;
    
    try {
      const response = await api.ai.ask(userMessage, 'general', userId, chatId);
      if (response.chat_id && !chatId) {
        setChatId(response.chat_id);
      }
      setMessages((m) => [
        ...m,
        { role: "ai" as const, text: response.answer },
      ]);
    } catch (error) {
      console.error("AI Assistant Error:", error);
      setMessages((m) => [
        ...m,
        { role: "ai" as const, text: "Простите, магия исказилась в эфире. Я не могу сейчас ответить на этот вопрос." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* FAB Button */}
      <motion.button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full flex items-center justify-center shadow-[0_5px_20px_rgba(212,175,55,0.4)] transition-all border border-[#D4AF37]/50 group"
        style={{
          background: "radial-gradient(circle at 30% 30%, #D4AF37, #8B6914)",
        }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {open ? (
          <X className="w-6 h-6 text-[#1A1A1A] transition-transform duration-300" />
        ) : (
          <Wand2 className="w-7 h-7 text-[#1A1A1A] group-hover:animate-wiggle" />
        )}
        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-[#F4EBD0]/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      </motion.button>

      {/* Chat window */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            className="fixed bottom-28 right-4 sm:right-6 z-50 w-[calc(100vw-2rem)] sm:w-96 bg-[#1A1A1A] border border-[#D4AF37]/30 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[70vh]"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-[#2c2419] to-[#1A1A1A] px-5 py-4 border-b border-[#D4AF37]/20 flex items-center gap-4 shrink-0">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#D4AF37]/30 to-transparent flex items-center justify-center border border-[#D4AF37]/40 shadow-inner">
                <Sparkles className="w-5 h-5 text-[#D4AF37]" />
              </div>
              <div>
                <p className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] tracking-wide text-lg">Тайный Проводник</p>
                <p className="font-['Lora',serif] text-[#D4AF37]/70 text-xs uppercase tracking-widest">ИИ Ассистент</p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-[#D4AF37]/20 scrollbar-track-transparent bg-[#111]">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-2xl font-['Lora',serif] text-sm leading-relaxed shadow-md ${
                      msg.role === "user"
                        ? "bg-gradient-to-br from-[#8B0000]/80 to-[#5C0000]/80 text-[#F4EBD0] border border-[#8B0000] rounded-tr-sm"
                        : "bg-gradient-to-br from-[#222] to-[#1a1a1a] text-[#F4EBD0]/90 border border-[#333] rounded-tl-sm prose prose-invert prose-p:my-1 prose-a:text-[#D4AF37]"
                    }`}
                  >
                    {msg.role === "ai" ? (
                      <div dangerouslySetInnerHTML={{ __html: msg.text }} />
                    ) : (
                      msg.text
                    )}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="max-w-[85%] px-4 py-3 rounded-2xl bg-gradient-to-br from-[#222] to-[#1a1a1a] text-[#F4EBD0]/90 border border-[#333] rounded-tl-sm flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-[#D4AF37]" />
                    <span className="font-['Lora',serif] text-sm text-[#D4AF37]/70">Ищет ответ в древних свитках...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 border-t border-[#D4AF37]/20 bg-[#1A1A1A] flex gap-2 shrink-0">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                placeholder="Спроси оракула..."
                disabled={isLoading}
                className="flex-1 px-4 py-3 bg-[#222] border-2 border-[#333] rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/30 font-['Lora',serif] focus:outline-none focus:border-[#D4AF37]/50 focus:bg-[#2a2a2a] transition-all text-sm disabled:opacity-50"
              />
              <button
                onClick={sendMessage}
                disabled={isLoading}
                className="px-4 py-3 bg-gradient-to-br from-[#D4AF37] to-[#B8962E] rounded-xl hover:from-[#E5C048] hover:to-[#C9A73F] transition-all shadow-md active:scale-95 group flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-5 h-5 text-[#1A1A1A] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}