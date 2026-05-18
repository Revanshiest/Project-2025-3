import { useEffect } from "react";
import { useNavigate } from "react-router";
import { ShieldCheck, Activity, Folder, FileText, MessageCircle, UserPlus, Settings, Lock } from "lucide-react";

const adminItems = [
  {
    title: "Управление пользователями",
    description: "Просматривайте и управляйте учетными записями, права доступа и блокировки.",
    icon: UserPlus,
  },
  {
    title: "Просмотр аналитики",
    description: "Собирайте метрики по активности пользователей, чатов и создания персонажей.",
    icon: Activity,
  },
  {
    title: "Управление контентом",
    description: "Редактируйте разделы, добавляйте новые записи в глоссарий и справочник.",
    icon: Folder,
  },
  {
    title: "Просмотр логов",
    description: "Отслеживайте системные события и историю изменений для анализа.",
    icon: FileText,
  },
  {
    title: "Модерация AI",
    description: "Контролируйте ответы ассистента и корректируйте поведение генерации.",
    icon: ShieldCheck,
  },
  {
    title: "Бан пользователей",
    description: "Блокируйте нарушителей и управляйте списками запрещенных аккаунтов.",
    icon: Lock,
  },
  {
    title: "Feedback management",
    description: "Собирайте обратную связь и распределяйте задачи для доработки.",
    icon: MessageCircle,
  },
  {
    title: "Управление ролями",
    description: "Назначайте роли и уровни доступа для членов команды и модераторов.",
    icon: Settings,
  },
];

export function AdminPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem("currentUser");
    if (!userData) {
      navigate("/");
      return;
    }

    const currentUser = JSON.parse(userData);
    if (currentUser.username?.toLowerCase() !== "admin") {
      navigate("/");
    }
  }, [navigate]);

  return (
    <div className="min-h-screen bg-[#1A1A1A] pt-24 pb-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h1 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: 'clamp(3rem, 8vw, 4rem)', lineHeight: 1.2 }}>
            Админ <span className="text-[#D4AF37]">Панель</span>
          </h1>
          <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-lg mt-4 max-w-2xl mx-auto">
            Управляйте пользователями, контентом, аналитикой и модерацией.
          </p>
          <div className="w-16 h-1 bg-[#D4AF37] mx-auto mt-6 opacity-60" />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {adminItems.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.title} className="relative overflow-hidden rounded-3xl border border-[#D4AF37]/30 bg-gradient-to-br from-[#2c2722] to-[#1e1a17] p-6 shadow-2xl transition-all duration-500 hover:border-[#D4AF37]/50">
                <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-[#D4AF37]/10 blur-3xl" />
                <div className="relative z-10 flex items-start gap-4 mb-4">
                  <div className="w-12 h-12 rounded-2xl bg-[#D4AF37]/20 text-[#D4AF37] flex items-center justify-center shadow-inner">
                    <Icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-xl mb-2">
                      {item.title}
                    </h2>
                    <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </div>
                <div className="mt-4">
                  <button className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/20 hover:bg-[#D4AF37]/20 transition-colors font-['Lora',serif] text-sm">
                    Открыть раздел
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
