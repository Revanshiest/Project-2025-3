import { X } from "lucide-react";
import { useEffect } from "react";

interface InfoModalProps {
  title: string;
  description: string;
  isOpen: boolean;
  onClose: () => void;
}

export function InfoModal({ title, description, isOpen, onClose }: InfoModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      // Запрещаем скролл body
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-2xl max-h-[80vh] relative bg-[#1e1a17] border border-[#D4AF37]/40 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Texture */}
        <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080')] bg-cover mix-blend-overlay pointer-events-none" />

        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 rounded-full bg-[#D4AF37]/10 hover:bg-[#D4AF37] text-[#D4AF37] hover:text-[#1A1A1A] transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="relative z-10 p-6 border-b border-[#D4AF37]/20">
          <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-2xl pr-8">
            {title}
          </h3>
        </div>

        <div className="relative z-10 p-6 overflow-y-auto custom-scrollbar">
          <div className="font-['Lora',serif] text-[#F4EBD0]/80 whitespace-pre-wrap leading-relaxed text-sm">
            {description}
          </div>
        </div>
      </div>
    </div>
  );
}
