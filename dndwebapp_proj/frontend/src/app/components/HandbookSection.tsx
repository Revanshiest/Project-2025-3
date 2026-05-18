import { Users, Swords, Shield, BookOpen } from "lucide-react";
import { motion } from "motion/react";
import { Link } from "react-router";

const cards = [
  {
    title: "Расы",
    desc: "Эльфы, Дварфы, Тифлинги и многие другие — открой свое наследие.",
    icon: Users,
    color: "#D4AF37",
    link: "/handbook#races",
  },
  {
    title: "Классы",
    desc: "От Волшебника до Варвара, найди путь, который зовет тебя.",
    icon: Shield,
    color: "#8B0000",
    link: "/handbook#classes",
  },
  {
    title: "Оружие",
    desc: "Мечи, посохи и зачарованные реликвии ждут своей участи.",
    icon: Swords,
    color: "#D4AF37",
    link: "/handbook#equipment",
  },
  {
    title: "Лор",
    desc: "Погрузись в богатую историю Забытых Королевств.",
    icon: BookOpen,
    color: "#8B0000",
    link: "/handbook#lore",
  },
];

export function HandbookSection() {
  return (
    <section
      id="handbook"
      className="relative py-24 px-4 sm:px-6 bg-[#1A1A1A]"
    >
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16 px-4">
          <h2
            className="font-['Cormorant_Garamond',serif] font-bold uppercase text-[#D4AF37] tracking-[0.2em] mb-4"
            style={{ fontSize: "1rem" }}
          >
            ВЕЛИКИЙ АРХИВ
          </h2>
          <h3
            className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] drop-shadow-md"
            style={{
              fontSize: "clamp(2rem, 5vw, 3rem)",
              lineHeight: 1.2,
            }}
          >
            Справочника Авантюриста
          </h3>
          <div className="w-24 h-1 bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent mx-auto mt-6" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {cards.map((card, i) => (
            <Link to={card.link} key={card.title}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="group relative bg-gradient-to-b from-[#222] to-[#1a1a1a] border border-[#333] rounded-xl p-8 cursor-pointer hover:border-[#D4AF37]/50 transition-all duration-300 hover:-translate-y-2 hover:shadow-[0_15px_40px_rgba(212,175,55,0.15)] h-full flex flex-col items-center text-center"
              >
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transition-transform duration-500 group-hover:scale-110 shadow-inner"
                  style={{
                    background: `linear-gradient(135deg, ${card.color}20, transparent)`,
                    border: `1px solid ${card.color}40`,
                  }}
                >
                  <card.icon
                    className="w-8 h-8 drop-shadow-md"
                    style={{ color: card.color }}
                  />
                </div>
                <h4
                  className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] mb-3 uppercase tracking-wider"
                  style={{ fontSize: "1.4rem" }}
                >
                  {card.title}
                </h4>
                <p
                  className="font-['Lora',serif] text-[#F4EBD0]/60"
                  style={{ fontSize: "1rem", lineHeight: 1.6 }}
                >
                  {card.desc}
                </p>
                <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-[#D4AF37]/0 to-transparent group-hover:via-[#D4AF37]/70 transition-all duration-500" />
              </motion.div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}