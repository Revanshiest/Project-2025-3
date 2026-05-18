import { useState } from "react";
import { Search, Book } from "lucide-react";
import { Link } from "react-router";

const glossaryTerms = [
  // 1. Основные термины
  { term: "Класс Брони (AC)", def: "Показатель того, насколько хорошо существо избегает ранений в бою.", category: "basic" },
  { term: "Очки Здоровья (HP)", def: "Представляют собой комбинацию физической и ментальной выносливости, воли к жизни и удачи.", category: "basic" },
  { term: "Бонус Мастерства", def: "Бонус, добавляемый к броскам для вещей, в которых ваш персонаж опытен.", category: "basic" },
  { term: "Инициатива", def: "Определяет порядок ходов во время боя, бросается в начале каждого столкновения.", category: "basic" },

  // 2. Игровая механика
  { term: "Преимущество", def: "Бросьте два кубика d20 и выберите наибольший результат.", category: "mechanics" },
  { term: "Помеха", def: "Бросьте два кубика d20 и выберите наименьший результат.", category: "mechanics" },
  { term: "Проверка Характеристик", def: "Бросок кубика d20, модифицированный соответствующей характеристикой, для преодоления препятствий.", category: "mechanics" },
  { term: "Бросок Атаки", def: "Бросок d20 для определения того, попадет ли удар по Классу Брони (AC) цели.", category: "mechanics" },
  { term: "Спасбросок", def: "Попытка сопротивляться заклинанию, ловушке, яду, болезни или подобной угрозе.", category: "mechanics" },

  // 3. Создание персонажа
  { term: "Класс", def: "Призвание персонажа, определяющее его умения, тактику в бою и доступные способности.", category: "creation" },
  { term: "Раса", def: "Наследие персонажа, дарующее особые физические черты, языки и расовые особенности.", category: "creation" },
  { term: "Предыстория", def: "Прошлое персонажа, раскрывающее его происхождение, навыки общения и стартовое снаряжение.", category: "creation" },
  { term: "Мировоззрение", def: "Этический и моральный ориентир персонажа, определяющий его отношение к закону и добру.", category: "creation" },

  // 4. Боевая система
  { term: "Критический удар", def: "Выпадение '20' на кубике атаки, удваивающее все кубики урона от этой атаки.", category: "combat" },
  { term: "Смертельные спасброски", def: "Особые спасброски без модификаторов при 0 HP, определяющие выживание персонажа.", category: "combat" },
  { term: "Недееспособность", def: "Состояние, при котором существо не может совершать действия или реакции.", category: "combat" },
  { term: "Уклонение", def: "Действие в бою, заставляющее все атаки против вас совершаться с помехой.", category: "combat" },

  // 5. Магия
  { term: "Заговор", def: "Заклинание, которое можно читать по желанию, не расходуя ячейку заклинания.", category: "magic" },
  { term: "Ячейка заклинания", def: "Ресурс заклинателя, отражающий количество магии, которую он может высвободить за день.", category: "magic" },
  { term: "Магическая дистанция", def: "Предел расстояния, на котором заклинание может подействовать на цель.", category: "magic" },
  { term: "Концентрация", def: "Необходимость удерживать фокус разума на некоторых заклинаниях, чтобы продлить их действие.", category: "magic" },

  // 6. Ролевой аспект
  { term: "Вдохновение", def: "Особая награда Мастера, позволяющая перебросить один бросок d20 с преимуществом.", category: "roleplay" },
  { term: "Короткий отдых", def: "Период затишья не менее 1 часа, во время которого можно потратить Кости Хитов для лечения.", category: "roleplay" },
  { term: "Длинный отдых", def: "Период сна не менее 8 часов, полностью восстанавливающий HP, ячейки заклинаний и силы.", category: "roleplay" },
  { term: "Опыт (XP)", def: "Показатель обучения и боевой закалки персонажа, служащий для повышения уровня.", category: "roleplay" }
];

const categories = [
  { id: "all", label: "Все" },
  { id: "basic", label: "Основные термины" },
  { id: "mechanics", label: "Игровая механика" },
  { id: "creation", label: "Создание персонажа" },
  { id: "combat", label: "Боевая система" },
  { id: "magic", label: "Магия" },
  { id: "roleplay", label: "Ролевой аспект" }
];

const suggestedQueries = ["AC", "HP", "Спасбросок", "Бонус мастерства"];

export function GlossarySection() {
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");

  const filtered = glossaryTerms.filter(
    (t) =>
      (activeCategory === "all" || t.category === activeCategory) &&
      (t.term.toLowerCase().includes(query.toLowerCase()) ||
       t.def.toLowerCase().includes(query.toLowerCase()))
  );

  return (
    <section id="glossary" className="relative py-32 px-4 sm:px-6 bg-[#1A1A1A]">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-['Cormorant_Garamond',serif] font-bold uppercase text-[#D4AF37] tracking-[0.2em] mb-4" style={{ fontSize: '1rem' }}>
            ЗНАНИЕ — СИЛА
          </h2>
          <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', lineHeight: 1.2 }}>
            Магический Глоссарий
          </h3>
          <div className="w-16 h-1 bg-[#D4AF37] mx-auto mt-6 opacity-60" />
        </div>

        {/* Parchment container */}
        <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-6 sm:p-10 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500">
          {/* Subtle texture overlay */}
          <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay" />

          {/* Search bar */}
          <div className="relative mb-6 z-10 max-w-2xl mx-auto">
            <input
              type="text"
              placeholder="Поиск терминов, правил и тайных знаний..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-4 pr-14 py-4 bg-[#111]/80 backdrop-blur-sm border-2 border-[#D4AF37]/20 rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/40 font-['Lora',serif] text-base focus:outline-none focus:border-[#D4AF37]/60 focus:bg-[#1A1A1A]/90 focus:shadow-[0_0_30px_rgba(212,175,55,0.15)] transition-all"
            />
            <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#D4AF37]/70" />
          </div>
          <div className="relative z-10 max-w-2xl mx-auto mb-6 flex flex-wrap gap-2">
            {suggestedQueries.map((item) => (
              <span 
                key={item} 
                onClick={() => setQuery(item)}
                className="px-3 py-1 rounded-full bg-[#D4AF37]/10 border border-[#D4AF37]/20 text-[#F4EBD0]/80 text-sm cursor-pointer hover:bg-[#D4AF37]/25 hover:text-[#D4AF37] transition-all"
              >
                {item}
              </span>
            ))}
          </div>

          {/* Tabs */}
          <div className="relative z-10 flex flex-wrap gap-2 justify-center mb-8 border-b border-[#D4AF37]/20 pb-4">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`px-4 py-2 rounded-lg font-['Cormorant_Garamond',serif] font-medium transition-all duration-300 text-sm ${
                  activeCategory === cat.id
                    ? 'bg-[#D4AF37] text-[#1A1A1A] shadow-[0_0_15px_rgba(212,175,55,0.4)] font-bold'
                    : 'text-[#F4EBD0]/70 hover:text-[#D4AF37] hover:bg-[#D4AF37]/10'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Results */}
          <div className="relative z-10 space-y-3 max-h-96 overflow-y-auto pr-3 scrollbar-thin scrollbar-thumb-[#D4AF37]/20 scrollbar-track-transparent">
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-[#F4EBD0]/40">
                <Book className="w-12 h-12 mb-4 opacity-50" />
                <p className="font-['Lora',serif] italic text-lg">Страница не найдена в архивах...</p>
              </div>
            ) : (
              filtered.map((item) => (
                <div
                  key={item.term}
                  className="p-5 rounded-xl bg-gradient-to-r from-[#1a1a1a]/50 to-transparent hover:from-[#D4AF37]/10 hover:to-transparent transition-all duration-300 border-l-2 border-transparent hover:border-[#D4AF37] cursor-pointer"
                >
                  <span className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] tracking-wide text-xl block mb-2">
                    {item.term}
                  </span>
                  <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-base leading-relaxed">
                    {item.def}
                  </p>
                </div>
              ))
            )}
          </div>
          
        </div>
      </div>
    </section>
  );
}