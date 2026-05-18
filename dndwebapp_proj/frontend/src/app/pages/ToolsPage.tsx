import { DiceRoller } from "../components/DiceRoller";
import { Link } from "react-router";
import { Sparkles, Dices, Wrench } from "lucide-react";

export function ToolsPage() {
  return (
    <div className="min-h-screen bg-[#1A1A1A] pt-24 pb-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h1 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: 'clamp(3rem, 8vw, 4rem)', lineHeight: 1.2 }}>
            Настольные <span className="text-[#D4AF37]">Инструменты</span>
          </h1>
          <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-lg mt-4 max-w-2xl mx-auto">
            Кубики, генераторы и инструменты для вашего удобства за столом.
          </p>
          <div className="w-16 h-1 bg-[#D4AF37] mx-auto mt-6 opacity-60" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Create Character Card */}
          <Link to="/create-character">
            <div className="relative group bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-8 hover:border-[#D4AF37] transition-all duration-500 h-full flex flex-col justify-center items-center text-center overflow-hidden shadow-xl hover:shadow-[0_0_30px_rgba(212,175,55,0.2)]">
              <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080')] bg-cover mix-blend-overlay opacity-10 group-hover:opacity-20 transition-opacity" />
              
              <div className="w-20 h-20 rounded-full bg-[#D4AF37]/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500 border border-[#D4AF37]/30">
                <Sparkles className="w-10 h-10 text-[#D4AF37]" />
              </div>
              <h2 className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0] mb-4">
                Создание Персонажа
              </h2>
              <p className="font-['Lora',serif] text-[#F4EBD0]/70">
                Мощный и красивый мастер создания героя: характеристики, расы, классы и предыстории с поддержкой D&D 5e.
              </p>
            </div>
          </Link>

          {/* Quick Tools Info */}
          <div className="relative group bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-8 transition-all duration-500 h-full flex flex-col justify-center items-center text-center shadow-xl">
             <div className="w-20 h-20 rounded-full bg-[#1A1A1A] flex items-center justify-center mb-6 border border-[#333]">
                <Wrench className="w-10 h-10 text-[#F4EBD0]/50" />
              </div>
              <h2 className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0] mb-4">
                Быстрые инструменты
              </h2>
              <p className="font-['Lora',serif] text-[#F4EBD0]/70">
                Броски кубиков (уже ниже на странице), генераторы лута и инициативы (скоро появятся).
              </p>
          </div>
        </div>

        {/* Dice Roller */}
        <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl overflow-hidden shadow-2xl">
          <DiceRoller />
        </div>

      </div>
    </div>
  );
}
