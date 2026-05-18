import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Dices, Sparkles } from "lucide-react";

const diceTypes = [
  { name: "d4", sides: 4, shape: "polygon(50% 0%, 0% 100%, 100% 100%)" },
  { name: "d6", sides: 6, shape: "" },
  { name: "d8", sides: 8, shape: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)" },
  { name: "d10", sides: 10, shape: "polygon(50% 0%, 95% 35%, 80% 100%, 20% 100%, 5% 35%)" },
  { name: "d12", sides: 12, shape: "polygon(50% 0%, 85% 15%, 100% 50%, 85% 85%, 50% 100%, 15% 85%, 0% 50%, 15% 15%)" },
  { name: "d20", sides: 20, shape: "polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%)" },
  { name: "d100", sides: 100, shape: "circle(50% at 50% 50%)" },
];

export function DiceRoller() {
  const [selectedDice, setSelectedDice] = useState<number | null>(null);
  const [result, setResult] = useState<number | null>(null);
  const [rolling, setRolling] = useState(false);

  const rollDice = () => {
    if (selectedDice === null) return;
    setRolling(true);
    setResult(null);

    let count = 0;
    const interval = setInterval(() => {
      setResult(Math.floor(Math.random() * diceTypes[selectedDice].sides) + 1);
      count++;
      if (count > 15) {
        clearInterval(interval);
        setRolling(false);
      }
    }, 60);
  };

  return (
    <section id="dice-roller" className="relative py-24 px-4 sm:px-6 bg-[#151515]">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] tracking-[0.3em] uppercase mb-4" style={{ fontSize: '1rem' }}>
            ВЕРШИТЕЛЬ СУДЕБ
          </h2>
          <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', lineHeight: 1.2 }}>
            Бросок Кубиков
          </h3>
          <div className="w-16 h-1 bg-[#8B0000] mx-auto mt-6" />
        </div>

        {/* Dice grid */}
        <div className="flex flex-wrap justify-center gap-4 sm:gap-6 mb-16 px-2">
          {diceTypes.map((dice, i) => (
            <button
              key={dice.name}
              onClick={() => { setSelectedDice(i); setResult(null); }}
              className={`relative w-16 h-16 sm:w-20 sm:h-20 flex flex-col items-center justify-center rounded-xl border-2 transition-all duration-300 transform hover:scale-105 ${
                selectedDice === i
                  ? "border-[#D4AF37] bg-[#D4AF37]/20 shadow-[0_0_25px_rgba(212,175,55,0.4)] scale-110 z-10"
                  : "border-[#333] bg-[#222] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5"
              }`}
            >
              <div
                className="w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center mb-1 sm:mb-2 transition-all"
                style={{
                  clipPath: dice.shape || undefined,
                  borderRadius: dice.shape ? undefined : "6px",
                  background: selectedDice === i ? "rgba(212,175,55,0.3)" : "rgba(244,235,208,0.1)",
                  border: `1px solid ${selectedDice === i ? "#D4AF37" : "rgba(244,235,208,0.2)"}`,
                }}
              >
                <span className="text-[#F4EBD0] font-['Cormorant_Garamond',serif] font-bold" style={{ fontSize: '0.75rem' }}>
                  {dice.sides}
                </span>
              </div>
              <span className="font-['Lora',serif] font-bold uppercase tracking-wider text-[#F4EBD0]/80" style={{ fontSize: '0.75rem' }}>
                {dice.name}
              </span>
            </button>
          ))}
        </div>

        {/* Result display */}
        <div className="flex flex-col items-center gap-10">
          <div className="relative w-40 h-40 flex items-center justify-center group">
            <div className={`absolute inset-0 rounded-full border border-[#D4AF37]/30 transition-all duration-700 ${rolling ? 'animate-spin bg-[#D4AF37]/20 shadow-[0_0_40px_rgba(212,175,55,0.4)]' : 'bg-[#D4AF37]/5'}`} />
            <div className={`absolute inset-3 rounded-full border border-[#D4AF37]/20 transition-all duration-500 ${rolling ? 'animate-ping' : ''}`} />
            
            <AnimatePresence mode="wait">
              {result !== null ? (
                <motion.span
                  key={result + (rolling ? Math.random() : 0)}
                  initial={{ scale: 0.5, opacity: 0, rotate: -30 }}
                  animate={{ scale: 1, opacity: 1, rotate: 0 }}
                  className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] relative z-10 drop-shadow-[0_2px_10px_rgba(0,0,0,1)]"
                  style={{ fontSize: rolling ? '2.5rem' : '4rem' }}
                >
                  {result}
                </motion.span>
              ) : (
                <Dices className="w-12 h-12 text-[#F4EBD0]/30 group-hover:text-[#D4AF37]/50 transition-colors" />
              )}
            </AnimatePresence>
          </div>

          <button
            onClick={rollDice}
            disabled={selectedDice === null || rolling}
            className="flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-[#8B0000] to-[#5C0000] text-[#F4EBD0] font-['Cormorant_Garamond',serif] font-bold uppercase tracking-widest rounded-xl transition-all hover:shadow-[0_0_40px_rgba(139,0,0,0.6)] hover:scale-105 active:scale-95 disabled:opacity-40 disabled:hover:scale-100 disabled:hover:shadow-none"
            style={{ fontSize: '1.2rem' }}
          >
            {rolling ? "Бросок..." : "Испытать Судьбу"}
            <Sparkles className={`w-5 h-5 ${rolling ? 'animate-pulse text-[#D4AF37]' : ''}`} />
          </button>
        </div>
      </div>
    </section>
  );
}