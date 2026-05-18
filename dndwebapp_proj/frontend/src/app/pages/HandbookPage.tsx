import { useState, useEffect } from "react";
import { Link } from "react-router";
import { Shield, Swords, Users, BookOpen, ArrowLeft, Loader2, Heart, Zap, Sparkles, Brain, Eye } from "lucide-react";
import { api } from "../../api/client";

export function HandbookPage() {
  const [activeCategory, setActiveCategory] = useState<'none' | 'races' | 'classes' | 'equipment'>('none');
  const [loading, setLoading] = useState(false);
  const [races, setRaces] = useState<any[]>([]);
  const [classes, setClasses] = useState<any[]>([]);
  const [items, setItems] = useState<any>(null);
  
  const [selectedKey, setSelectedKey] = useState<string>("");
  const [activeEquipmentTab, setActiveEquipmentTab] = useState<'weapons' | 'armor' | 'adventuring_gear'>('weapons');

  // Load category data when tab changes
  useEffect(() => {
    if (activeCategory === 'none') return;
    
    const loadCategoryData = async () => {
      setLoading(true);
      try {
        if (activeCategory === 'races' && races.length === 0) {
          const res = await api.reference.getRaces();
          setRaces(res.items || []);
          if (res.items && res.items.length > 0) {
            setSelectedKey(res.items[0].key || res.items[0].name);
          }
        } else if (activeCategory === 'classes' && classes.length === 0) {
          const res = await api.reference.getClasses();
          setClasses(res.items || []);
          if (res.items && res.items.length > 0) {
            setSelectedKey(res.items[0].id || res.items[0].name);
          }
        } else if (activeCategory === 'equipment') {
          let currentItems = items;
          if (!items) {
            const res = await api.reference.getItems();
            setItems(res);
            currentItems = res;
          }
          if (currentItems && currentItems[activeEquipmentTab]) {
            const keys = Object.keys(currentItems[activeEquipmentTab]);
            if (keys.length > 0) {
              setSelectedKey(keys[0]);
            }
          }
        }
      } catch (err) {
        console.error("Failed to load handbook category:", err);
      } finally {
        setLoading(false);
      }
    };
    loadCategoryData();
  }, [activeCategory, activeEquipmentTab]);

  // Helpers to get selected details
  const getSelectedRace = () => {
    return races.find(r => r.key === selectedKey || r.name === selectedKey);
  };

  const getSelectedClass = () => {
    return classes.find(c => c.id === selectedKey || c.name === selectedKey);
  };

  const getSelectedItem = () => {
    if (!items || !items[activeEquipmentTab]) return null;
    return items[activeEquipmentTab][selectedKey];
  };

  // Render Root Catalog Cards
  if (activeCategory === 'none') {
    return (
      <div className="min-h-[80vh] py-32 px-4 sm:px-6 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] tracking-[0.3em] uppercase mb-4" style={{ fontSize: '1.2rem' }}>
            ВЕЛИКИЙ АРХИВ
          </h1>
          <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] mb-8" style={{ fontSize: 'clamp(2.5rem, 6vw, 4rem)', lineHeight: 1.1 }}>
            Справочник Авантюриста
          </h2>
          <p className="font-['Lora',serif] text-[#F4EBD0]/70 max-w-2xl mx-auto text-lg leading-relaxed">
            Вся мудрость Забытых Королевств собрана здесь. Изучай расы, классы, снаряжение и правила, чтобы подготовиться к своему следующему приключению.
          </p>
        </div>

        <div className="grid gap-12 lg:grid-cols-2">
          {/* Races Section */}
          <section 
            onClick={() => setActiveCategory('races')}
            className="bg-[#111] border border-[#D4AF37]/20 rounded-2xl p-8 hover:border-[#D4AF37]/50 cursor-pointer transition-all hover:shadow-[0_0_20px_rgba(212,175,55,0.1)] group"
          >
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-[#D4AF37]/10 flex items-center justify-center border border-[#D4AF37]/30 group-hover:bg-[#D4AF37]/20 transition-all">
                <Users className="w-6 h-6 text-[#D4AF37]" />
              </div>
              <h3 className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0] group-hover:text-[#D4AF37] transition-all">Расы</h3>
            </div>
            <p className="font-['Lora',serif] text-[#F4EBD0]/60 mb-6">Выбор расы определяет не только внешний вид, но и врожденные способности вашего персонажа.</p>
            <ul className="space-y-3 font-['Lora',serif] text-[#F4EBD0]/80">
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" /> Человек (Human) - Адаптивность и амбиции</li>
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" /> Эльф (Elf) - Грация, магия и долголетие</li>
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" /> Дварф (Dwarf) - Стойкость, традиции и мастерство</li>
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" /> Тифлинг (Tiefling) - Дьявольское наследие</li>
            </ul>
            <div className="mt-6 text-sm text-[#D4AF37] font-bold font-['Cormorant_Garamond',serif] uppercase tracking-wider flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Открыть свиток рас &rarr;</span>
            </div>
          </section>

          {/* Classes Section */}
          <section 
            onClick={() => setActiveCategory('classes')}
            className="bg-[#111] border border-[#8B0000]/40 rounded-2xl p-8 hover:border-[#8B0000]/70 cursor-pointer transition-all hover:shadow-[0_0_20px_rgba(139,0,0,0.15)] group"
          >
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-[#8B0000]/10 flex items-center justify-center border border-[#8B0000]/40 group-hover:bg-[#8B0000]/20 transition-all">
                <Shield className="w-6 h-6 text-[#8B0000]" />
              </div>
              <h3 className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0] group-hover:text-[#8B0000] transition-all">Классы</h3>
            </div>
            <p className="font-['Lora',serif] text-[#F4EBD0]/60 mb-6">Класс — это призвание вашего персонажа, источник его основных способностей и путь развития.</p>
            <ul className="space-y-3 font-['Lora',serif] text-[#F4EBD0]/80">
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#8B0000]" /> Воин (Fighter) - Мастер оружия и брони</li>
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#8B0000]" /> Волшебник (Wizard) - Исследователь тайной магии</li>
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#8B0000]" /> Плут (Rogue) - Ловкий и скрытный специалист</li>
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#8B0000]" /> Жрец (Cleric) - Целитель, наделенный божественной силой</li>
            </ul>
            <div className="mt-6 text-sm text-[#8B0000] font-bold font-['Cormorant_Garamond',serif] uppercase tracking-wider flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Открыть кодекс классов &rarr;</span>
            </div>
          </section>

          {/* Equipment Section */}
          <section 
            onClick={() => setActiveCategory('equipment')}
            className="bg-[#111] border border-[#D4AF37]/20 rounded-2xl p-8 hover:border-[#D4AF37]/50 cursor-pointer transition-all hover:shadow-[0_0_20px_rgba(212,175,55,0.1)] group"
          >
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-[#D4AF37]/10 flex items-center justify-center border border-[#D4AF37]/30 group-hover:bg-[#D4AF37]/20 transition-all">
                <Swords className="w-6 h-6 text-[#D4AF37]" />
              </div>
              <h3 className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0] group-hover:text-[#D4AF37] transition-all">Снаряжение</h3>
            </div>
            <p className="font-['Lora',serif] text-[#F4EBD0]/60 mb-6">Хороший клинок и прочная броня — лучшие друзья авантюриста в диких землях.</p>
            <ul className="space-y-3 font-['Lora',serif] text-[#F4EBD0]/80">
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" /> Простые и воинские клинки, арбалеты и щиты</li>
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" /> Тяжелая, средняя и легкая броня</li>
              <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" /> Дорожные наборы, факелы и веревки</li>
            </ul>
            <div className="mt-6 text-sm text-[#D4AF37] font-bold font-['Cormorant_Garamond',serif] uppercase tracking-wider flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Открыть арсенал снаряжения &rarr;</span>
            </div>
          </section>

          {/* Lore Section */}
          <section id="lore" className="bg-[#111] border border-[#D4AF37]/20 rounded-2xl p-8 hover:border-[#D4AF37]/40 transition-colors">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-[#D4AF37]/10 flex items-center justify-center border border-[#D4AF37]/30">
                <BookOpen className="w-6 h-6 text-[#D4AF37]" />
              </div>
              <h3 className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0]">Лор и Правила</h3>
            </div>
            <p className="font-['Lora',serif] text-[#F4EBD0]/60 mb-6">История миров D&D безгранична. Здесь вы найдете основы мироустройства и базовые правила игры.</p>
            <Link to="/glossary" className="inline-flex items-center gap-2 px-6 py-3 bg-[#D4AF37]/10 text-[#D4AF37] hover:bg-[#D4AF37]/20 rounded-lg border border-[#D4AF37]/30 transition-colors font-['Cormorant_Garamond',serif] font-bold tracking-wider uppercase text-sm">
              <span>Перейти в Глоссарий</span>
            </Link>
          </section>
        </div>
      </div>
    );
  }

  // RENDER DYNAMIC EXPLORER VIEWS
  return (
    <div className="min-h-[85vh] py-28 px-4 sm:px-6 max-w-6xl mx-auto flex flex-col">
      {/* Explorer Top Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 border-b border-[#D4AF37]/20 pb-6">
        <button
          onClick={() => {
            setActiveCategory('none');
            setSelectedKey("");
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#D4AF37]/10 text-[#D4AF37] hover:bg-[#D4AF37]/20 rounded-lg border border-[#D4AF37]/30 transition-colors font-['Cormorant_Garamond',serif] font-bold uppercase tracking-wider text-sm w-fit active:scale-95"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Назад в архив</span>
        </button>

        <h2 className="font-['Cormorant_Garamond',serif] font-bold text-2xl sm:text-3xl text-[#F4EBD0]">
          {activeCategory === 'races' && "Великая Библиотека Рас"}
          {activeCategory === 'classes' && "Кодекс Героических Классов"}
          {activeCategory === 'equipment' && "Королевская Оружейная"}
        </h2>
      </div>

      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center py-20 text-[#D4AF37]">
          <Loader2 className="w-12 h-12 animate-spin mb-4" />
          <p className="font-['Lora',serif] text-lg text-[#F4EBD0]/70">Расшифровка древних текстов...</p>
        </div>
      ) : (
        <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 items-start">
        {/* LEFT COLUMN: NAVIGATION LIST — hidden on mobile when item selected */}
        <div className={`md:col-span-1 bg-[#111]/70 border border-[#D4AF37]/20 rounded-2xl p-4 max-h-[600px] overflow-y-auto scrollbar-thin scrollbar-thumb-[#D4AF37]/25 scrollbar-track-transparent ${selectedKey ? 'hidden md:block' : 'block'}`}>
            {/* Additional Sub-Tabs for Equipment */}
            {activeCategory === 'equipment' && (
              <div className="flex gap-1 mb-4 bg-[#1A1A1A] p-1 rounded-lg border border-[#D4AF37]/15">
                {(['weapons', 'armor', 'adventuring_gear'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveEquipmentTab(tab)}
                    className={`flex-1 py-1.5 text-xs font-bold uppercase tracking-widest rounded transition-all ${
                      activeEquipmentTab === tab 
                        ? 'bg-[#D4AF37] text-[#111]' 
                        : 'text-[#F4EBD0]/60 hover:text-[#D4AF37]'
                    }`}
                  >
                    {tab === 'weapons' && "Оружие"}
                    {tab === 'armor' && "Доспехи"}
                    {tab === 'adventuring_gear' && "Вещи"}
                  </button>
                ))}
              </div>
            )}

            {/* List entries */}
            <div className="space-y-2">
              {activeCategory === 'races' && races.map((race) => {
                const key = race.key || race.name;
                const isSelected = key === selectedKey;
                return (
                  <button
                    key={key}
                    onClick={() => setSelectedKey(key)}
                    className={`w-full text-left px-4 py-3 rounded-xl border font-['Cormorant_Garamond',serif] font-bold text-lg transition-all ${
                      isSelected 
                        ? 'bg-[#D4AF37]/15 border-[#D4AF37] text-[#D4AF37] shadow-[0_0_15px_rgba(212,175,55,0.15)]' 
                        : 'bg-[#1A1A1A]/50 border-transparent text-[#F4EBD0]/70 hover:bg-[#1A1A1A] hover:border-[#D4AF37]/35'
                    }`}
                  >
                    {race.name}
                  </button>
                );
              })}

              {activeCategory === 'classes' && classes.map((cls) => {
                const id = cls.id || cls.name;
                const isSelected = id === selectedKey;
                return (
                  <button
                    key={id}
                    onClick={() => setSelectedKey(id)}
                    className={`w-full text-left px-4 py-3 rounded-xl border font-['Cormorant_Garamond',serif] font-bold text-lg transition-all ${
                      isSelected 
                        ? 'bg-[#8B0000]/20 border-[#8B0000] text-[#ff4d4d] shadow-[0_0_15px_rgba(139,0,0,0.2)]' 
                        : 'bg-[#1A1A1A]/50 border-transparent text-[#F4EBD0]/70 hover:bg-[#1A1A1A] hover:border-[#8B0000]/40'
                    }`}
                  >
                    {cls.name}
                  </button>
                );
              })}

              {activeCategory === 'equipment' && items && items[activeEquipmentTab] && 
                Object.keys(items[activeEquipmentTab]).map((itemKey) => {
                  const item = items[activeEquipmentTab][itemKey];
                  const isSelected = itemKey === selectedKey;
                  return (
                    <button
                      key={itemKey}
                      onClick={() => setSelectedKey(itemKey)}
                      className={`w-full text-left px-4 py-3 rounded-xl border font-['Cormorant_Garamond',serif] font-bold text-lg transition-all ${
                        isSelected 
                          ? 'bg-[#D4AF37]/15 border-[#D4AF37] text-[#D4AF37] shadow-[0_0_15px_rgba(212,175,55,0.15)]' 
                          : 'bg-[#1A1A1A]/50 border-transparent text-[#F4EBD0]/70 hover:bg-[#1A1A1A] hover:border-[#D4AF37]/35'
                      }`}
                    >
                      {item.name}
                    </button>
                  );
                })
              }
            </div>
          </div>

        {/* RIGHT COLUMN: DISPLAY PANE — on mobile, shows only when item selected */}
        <div className={`md:col-span-2 relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-5 md:p-8 shadow-2xl overflow-hidden min-h-[400px] ${selectedKey ? 'block' : 'hidden md:block'}`}>
          {/* Mobile back-to-list button */}
          <button
            onClick={() => setSelectedKey('')}
            className="md:hidden mb-4 flex items-center gap-2 text-[#D4AF37] hover:text-[#F4EBD0] transition-colors font-['Lora',serif] text-sm"
          >
            ← Назад к списку
          </button>
            {/* Subtle parchment background texture overlay */}
            <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

            <div className="relative z-10">
              {/* RENDER RACE DETAILS */}
              {activeCategory === 'races' && (() => {
                const race = getSelectedRace();
                if (!race) return <p className="text-[#F4EBD0]/50 italic">Выберите расу для просмотра</p>;
                return (
                  <div>
                    <h3 className="font-['Cormorant_Garamond',serif] font-bold text-4xl text-[#D4AF37] mb-2">{race.name}</h3>
                    <p className="font-['Lora',serif] text-sm text-[#F4EBD0]/50 uppercase tracking-widest mb-6">Древняя раса D&D</p>
                    <div className="w-16 h-[2px] bg-[#D4AF37]/40 mb-6" />

                    <div className="font-['Lora',serif] text-[#F4EBD0]/90 text-sm leading-relaxed whitespace-pre-line space-y-4">
                      {race.description}
                    </div>
                  </div>
                );
              })()}

              {/* RENDER CLASS DETAILS */}
              {activeCategory === 'classes' && (() => {
                const cls = getSelectedClass();
                if (!cls) return <p className="text-[#F4EBD0]/50 italic">Выберите класс для просмотра</p>;
                return (
                  <div>
                    <div className="flex items-center justify-between gap-4 mb-2 flex-wrap">
                      <h3 className="font-['Cormorant_Garamond',serif] font-bold text-4xl text-[#ff4d4d]">{cls.name}</h3>
                      {cls.is_spellcaster && (
                        <span className="px-3 py-1 bg-[#8B0000]/30 border border-[#8B0000]/60 rounded-full text-xs font-bold text-[#ff8080] uppercase tracking-widest">
                          Заклинатель
                        </span>
                      )}
                    </div>
                    <p className="font-['Lora',serif] text-sm text-[#F4EBD0]/50 uppercase tracking-widest mb-6">Героический класс D&D</p>
                    <div className="w-16 h-[2px] bg-[#8B0000]/40 mb-6" />

                    <div className="font-['Lora',serif] text-[#F4EBD0]/90 text-sm leading-relaxed whitespace-pre-line space-y-4">
                      {cls.description}
                    </div>
                  </div>
                );
              })()}

              {/* RENDER EQUIPMENT DETAILS */}
              {activeCategory === 'equipment' && (() => {
                const item = getSelectedItem();
                if (!item) return <p className="text-[#F4EBD0]/50 italic">Выберите предмет для просмотра</p>;
                return (
                  <div>
                    <h3 className="font-['Cormorant_Garamond',serif] font-bold text-4xl text-[#D4AF37] mb-1">{item.name}</h3>
                    {item.name_en && (
                      <p className="font-['Lora',serif] text-xs text-[#F4EBD0]/50 uppercase tracking-widest italic mb-6">
                        {item.name_en}
                      </p>
                    )}
                    <div className="w-16 h-[2px] bg-[#D4AF37]/40 mb-6" />

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6 bg-[#111]/60 border border-[#D4AF37]/15 rounded-xl p-4">
                      <div className="flex flex-col">
                        <span className="font-['Lora',serif] text-[#D4AF37]/70 text-xs uppercase tracking-wider">Цена</span>
                        <span className="font-['Lora',serif] text-[#F4EBD0] text-sm font-medium mt-0.5">{item.cost || "н/д"}</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="font-['Lora',serif] text-[#D4AF37]/70 text-xs uppercase tracking-wider">Вес</span>
                        <span className="font-['Lora',serif] text-[#F4EBD0] text-sm font-medium mt-0.5">
                          {item.weight ? `${item.weight} фнт.` : "н/д"}
                        </span>
                      </div>
                      <div className="flex flex-col">
                        <span className="font-['Lora',serif] text-[#D4AF37]/70 text-xs uppercase tracking-wider">Категория</span>
                        <span className="font-['Lora',serif] text-[#F4EBD0] text-sm font-medium mt-0.5">
                          {item.category || (activeEquipmentTab === 'weapons' ? 'Оружие' : activeEquipmentTab === 'armor' ? 'Доспех' : 'Снаряжение')}
                        </span>
                      </div>
                      {item.damage && (
                        <div className="flex flex-col">
                          <span className="font-['Lora',serif] text-[#D4AF37]/70 text-xs uppercase tracking-wider">Урон</span>
                          <span className="font-['Lora',serif] text-[#F4EBD0] text-sm font-medium mt-0.5">
                            {item.damage} ({item.damage_type || ''})
                          </span>
                        </div>
                      )}
                      {item.ac && (
                        <div className="flex flex-col">
                          <span className="font-['Lora',serif] text-[#D4AF37]/70 text-xs uppercase tracking-wider">Класс Брони (AC)</span>
                          <span className="font-['Lora',serif] text-[#F4EBD0] text-sm font-medium mt-0.5">{item.ac}</span>
                        </div>
                      )}
                    </div>

                    {/* Properties List */}
                    {item.properties && item.properties.length > 0 && (
                      <div className="mb-6">
                        <h4 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-lg mb-2">Свойства:</h4>
                        <ul className="space-y-1.5 font-['Lora',serif] text-[#F4EBD0]/80 text-sm">
                          {item.properties.map((prop: string, idx: number) => (
                            <li key={idx} className="flex items-center gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" />
                              {prop}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Description */}
                    {item.description && (
                      <div>
                        <h4 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-lg mb-2">Описание:</h4>
                        <p className="font-['Lora',serif] text-[#F4EBD0]/85 text-sm leading-relaxed whitespace-pre-line">
                          {item.description}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}