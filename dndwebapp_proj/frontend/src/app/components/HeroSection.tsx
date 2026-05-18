import { Sparkles, ArrowRight, ChevronDown } from "lucide-react";
import { Link } from "react-router";
import heroImageImp from '../../images/head.png';
const heroImage = heroImageImp;

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      {/* Main cinematic overlay */}
      <div className="absolute inset-0 bg-[#0F1115]/35" />

      {/* Bottom fade into site background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#1A1A1A]" />

      {/* Side vignette */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#1A1A1A]/55 via-transparent to-[#1A1A1A]/35" />

      {/* Soft top fade */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0B0D12]/50 via-transparent to-transparent" />

      <div className="absolute inset-0 noise opacity-[0.025] pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 text-center px-4 max-w-4xl mx-auto flex flex-col items-center mt-12 mb-16">

        <h1
          className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] mb-6 tracking-wide drop-shadow-lg"
          style={{
            fontSize: "clamp(2.5rem, 8vw, 5rem)",
            lineHeight: 1.1,
          }}
        >
          Начни свою
          <br />
          <span className="text-[#D4AF37] relative inline-block mt-2">
            историю
            <div className="absolute -inset-2 bg-[#D4AF37]/10 blur-2xl rounded-full -z-10" />
          </span>
        </h1>

        <p
          className="font-['Lora',serif] text-[#F4EBD0]/80 max-w-2xl mx-auto mb-12 drop-shadow-md px-4"
          style={{ fontSize: "1.1rem", lineHeight: 1.6 }}
        >
          Создавай героев, бросай кубики судьбы и исследуй
          бесконечные миры Dungeons & Dragons вместе с
          цифровым помощником на базе искусственного интеллекта.
        </p>
      </div>

      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <ChevronDown className="w-6 h-6 text-[#D4AF37]" />
      </div>

    </section>
  );
}