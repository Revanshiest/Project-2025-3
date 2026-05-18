import { Dices, Flame } from "lucide-react";
import { Link } from "react-router";

export function Footer() {
  return (
    <footer className="bg-[#0A0A0A] border-t border-[#D4AF37]/20 py-16 px-4 sm:px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-10">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative w-8 h-8 flex items-center justify-center grayscale group-hover:grayscale-0 transition-all duration-700">
            <Flame className="absolute inset-0 w-8 h-8 text-[#8B0000] opacity-60" />
            <Dices className="relative z-10 w-5 h-5 text-[#D4AF37]/60 group-hover:text-[#D4AF37] transition-colors duration-500" />
          </div>
          <span className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]/50 group-hover:text-[#F4EBD0]/80 tracking-wider text-xl transition-colors duration-500 uppercase">
            D&D <span className="text-[#D4AF37]/60 group-hover:text-[#D4AF37]">Helper</span>
          </span>
        </Link>

        <p className="font-['Lora',serif] italic text-[#F4EBD0]/30 text-center md:text-right max-w-sm leading-relaxed" style={{ fontSize: '0.85rem' }}>
          Фанатский инструмент-помощник. Не связан с Wizards of the Coast. Все права на торговые марки принадлежат их законным владельцам.
        </p>
      </div>
      <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-[#1a1a1a] flex flex-col sm:flex-row items-center justify-between gap-4 text-[#F4EBD0]/20 font-['Lora',serif] text-xs">
        <p>© 2026 DnD Хелпер. Все права защищены.</p>
        <p>Да прибудет с вами критический успех.</p>
      </div>
    </footer>
  );
}