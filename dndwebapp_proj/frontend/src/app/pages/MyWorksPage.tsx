import { useState, useEffect } from "react";
import { useNavigate, Link, useLocation } from "react-router";
import { User, MessageSquare, Calendar, Eye, ChevronRight, Swords, Shield, Heart, Zap, Brain, Sparkles, PlusCircle, X, Loader2 } from "lucide-react";
import { api } from "../../api/client";
import { motion, AnimatePresence } from "motion/react";

interface CharacterSpells {
  cantrips?: string[];
  known_spells?: string[];
}

interface Character {
  id: string;
  name: string;
  race_name: string;
  class_name: string;
  level: number;
  experience: number;
  created_at: string;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  max_hp: number;
  armor_class: number;
  speed: number;
  proficiency_bonus: number;
  equipment?: string[];
  spells?: CharacterSpells;
}

interface ChatHistory {
  id: string;
  title: string;
  lastMessage: string;
  createdAt: string;
  messageCount: number;
}

export function MyWorksPage() {
  const [activeTab, setActiveTab] = useState<'characters' | 'chats'>('characters');
  const [characters, setCharacters] = useState<Character[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);
  const [openSection, setOpenSection] = useState<string>('abilities');
  const navigate = useNavigate();
  const location = useLocation();

  const [activeModalDetail, setActiveModalDetail] = useState<{
    name: string;
    subtitle?: string;
    description: string;
    properties?: { label: string; value: string | number }[];
  } | null>(null);
  const [modalLoading, setModalLoading] = useState(false);

  const handleItemClick = async (itemName: string) => {
    setModalLoading(true);
    setActiveModalDetail({ name: itemName, description: "Загрузка таинственных сведений..." });
    try {
      const itemsData = await api.reference.getItems();
      let found: any = null;
      let foundCategory = "";
      for (const cat of Object.keys(itemsData)) {
        const catItems = itemsData[cat];
        for (const itemKey of Object.keys(catItems)) {
          const item = catItems[itemKey];
          if (item.name.toLowerCase() === itemName.toLowerCase() || itemKey.toLowerCase() === itemName.toLowerCase()) {
            found = item;
            foundCategory = cat;
            break;
          }
        }
        if (found) break;
      }

      if (found) {
        const props = [
          { label: "Стоимость", value: found.cost || "н/д" },
          { label: "Вес", value: found.weight ? `${found.weight} фнт.` : "н/д" },
          { label: "Категория", value: found.category || foundCategory }
        ];
        if (found.damage) {
          props.push({ label: "Урон", value: `${found.damage} (${found.damage_type || ''})` });
        }
        if (found.ac) {
          props.push({ label: "Класс Брони (AC)", value: found.ac });
        }
        if (found.properties && found.properties.length > 0) {
          props.push({ label: "Свойства", value: found.properties.join(", ") });
        }

        setActiveModalDetail({
          name: found.name,
          subtitle: found.name_en || "",
          description: found.description || "Особое снаряжение для искателей приключений.",
          properties: props
        });
      } else {
        setActiveModalDetail({
          name: itemName,
          description: "Описание предмета не найдено в архивах, но он верно служит в ваших странствиях."
        });
      }
    } catch (err) {
      console.error(err);
      setActiveModalDetail({
        name: itemName,
        description: "Не удалось прочесть свитки описания из-за помех в магическом поле."
      });
    } finally {
      setModalLoading(false);
    }
  };

  const handleSpellClick = async (spellName: string, isCantrip: boolean) => {
    setModalLoading(true);
    setActiveModalDetail({ name: spellName, description: "Загрузка таинственных сведений..." });
    try {
      const level = isCantrip ? "0" : "1";
      const spellsData = await api.reference.getSpells(level);
      const items = spellsData.items || spellsData;
      let found: any = null;
      if (items && typeof items === 'object') {
        for (const sName of Object.keys(items)) {
          if (sName.toLowerCase() === spellName.toLowerCase()) {
            found = items[sName];
            found.name = sName;
            break;
          }
        }
      }

      if (found) {
        const props = [
          { label: "Время накладывания", value: found["Время накладывания"] || found.casting_time || "н/д" },
          { label: "Дистанция", value: found["Дистанция"] || found.range || "н/д" },
          { label: "Длительность", value: found["Длительность"] || found.duration || "н/д" },
          { label: "Компоненты", value: found["Компоненты"] || found.components || "н/д" },
          { label: "Классы", value: found["Классы"] || found.classes || "н/д" }
        ];

        setActiveModalDetail({
          name: found.name,
          subtitle: found["информация"] || found.info || "Заклинание",
          description: found["описание"] || found.description || "",
          properties: props
        });
      } else {
        setActiveModalDetail({
          name: spellName,
          description: "Описание заклинания не найдено в книгах магии."
        });
      }
    } catch (err) {
      console.error(err);
      setActiveModalDetail({
        name: spellName,
        description: "Не удалось прочесть свитки заклинаний из-за помех в магическом поле."
      });
    } finally {
      setModalLoading(false);
    }
  };

  useEffect(() => {
    const userStr = localStorage.getItem("currentUser");
    const userId = userStr ? JSON.parse(userStr).id : 1;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await api.characters.getUserCharacters(userId);
        setCharacters(data);
        
        // Auto-select character if passed in state (from CreateCharacterPage)
        const state = location.state as { newCharacterId?: string } | null;
        if (state && state.newCharacterId) {
          const char = data.find(c => c.id === state.newCharacterId);
          if (char) {
            setSelectedCharacter(char);
            // Replace state to clear it so it doesn't reopen on refresh
            navigate(location.pathname, { replace: true, state: {} });
          }
        }
      } catch (error) {
        console.error("Failed to load characters:", error);
      } finally {
        setLoading(false);
      }
      
      // Загрузка реальных чатов из базы
      try {
        const chats = await api.ai.getChats(userId);
        setChatHistory(chats.map((c: any) => ({
          id: c.id,
          title: c.title,
          lastMessage: c.lastMessage || 'Нет сообщений',
          createdAt: c.createdAt ? c.createdAt.split('T')[0] : '',
          messageCount: c.messageCount || 0
        })));
      } catch (err) {
        console.error("Failed to load chat history:", err);
      }
    };
    
    fetchData();
  }, []);

  const handleLevelUp = async (charId: string) => {
    try {
      const xpToAdd = prompt("Введите количество опыта для добавления:", "300");
      if (!xpToAdd || isNaN(parseInt(xpToAdd))) return;
      
      const userStr = localStorage.getItem("currentUser");
      const userId = userStr ? JSON.parse(userStr).id : 1;

      const response = await api.characters.addExperience(userId, charId, parseInt(xpToAdd));
      if (response.leveled_up) {
        alert(`Уровень повышен! Новый уровень: ${response.character.level}`);
      } else {
        alert(`Опыт добавлен. Текущий опыт: ${response.character.experience}`);
      }
      
      // Обновляем список и выбранного персонажа
      const updatedChars = await api.characters.getUserCharacters(userId);
      setCharacters(updatedChars);
      setSelectedCharacter(response.character);
    } catch (error) {
      console.error("Failed to add experience:", error);
      alert("Ошибка при добавлении опыта.");
    }
  };

  const getStatModifier = (score: number) => {
    const mod = Math.floor((score - 10) / 2);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  return (
    <div className="min-h-screen bg-[#1A1A1A] pt-24 pb-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: 'clamp(2.5rem, 8vw, 4rem)', lineHeight: 1.2 }}>
            Мои <span className="text-[#D4AF37]">Работы</span>
          </h1>
          <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-base sm:text-lg mt-4 max-w-2xl mx-auto">
            Ваши персонажи и история приключений.
          </p>
          <div className="w-16 h-1 bg-[#D4AF37] mx-auto mt-6 opacity-60" />
        </div>

        <div className="flex justify-center mb-6 sm:mb-8">
          <div className="flex bg-[#2c2722] border border-[#D4AF37]/30 rounded-xl p-1">
            <button
              onClick={() => {setActiveTab('characters'); setSelectedCharacter(null);}}
              className={`flex items-center gap-1.5 sm:gap-2 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-['Cormorant_Garamond',serif] font-medium transition-all duration-300 text-sm sm:text-base ${
                activeTab === 'characters'
                  ? 'bg-[#D4AF37] text-[#1A1A1A] shadow-[0_0_20px_rgba(212,175,55,0.5)]'
                  : 'text-[#F4EBD0]/70 hover:text-[#D4AF37] hover:bg-[#D4AF37]/10'
              }`}
            >
              <User className="w-4 h-4" />
              Персонажи
            </button>
            <button
              onClick={() => {setActiveTab('chats'); setSelectedCharacter(null);}}
              className={`flex items-center gap-1.5 sm:gap-2 px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-['Cormorant_Garamond',serif] font-medium transition-all duration-300 text-sm sm:text-base ${
                activeTab === 'chats'
                  ? 'bg-[#D4AF37] text-[#1A1A1A] shadow-[0_0_20px_rgba(212,175,55,0.5)]'
                  : 'text-[#F4EBD0]/70 hover:text-[#D4AF37] hover:bg-[#D4AF37]/10'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              Чаты с ИИ
            </button>
          </div>
        </div>

        <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-5 sm:p-8 md:p-12 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500 min-h-[400px]">
          <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay rounded-2xl" />

          <div className="relative z-10">
            {loading ? (
              <div className="text-center py-12 text-[#D4AF37] font-['Cormorant_Garamond',serif] text-xl animate-pulse">
                Загрузка данных...
              </div>
            ) : activeTab === 'characters' && !selectedCharacter && (
              <div>
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6">
                  Зал Героев
                </h2>
                {characters.length === 0 ? (
                  <div className="text-center py-12">
                    <User className="w-16 h-16 text-[#D4AF37]/50 mx-auto mb-4" />
                    <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-lg mb-4">
                      У вас пока нет созданных персонажей
                    </p>
                    <Link
                      to="/tools"
                      className="inline-flex items-center gap-2 px-6 py-3 bg-[#D4AF37]/20 border-2 border-[#D4AF37] rounded-xl text-[#D4AF37] hover:bg-[#D4AF37]/30 transition-all duration-300 font-['Cormorant_Garamond',serif] font-bold"
                    >
                      Создать героя в Инструментах
                    </Link>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {characters.map((character) => (
                      <div
                        key={character.id}
                        onClick={() => setSelectedCharacter(character)}
                        className="p-6 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20 hover:border-[#D4AF37]/70 hover:bg-[#D4AF37]/10 transition-all duration-300 hover:shadow-[0_0_20px_rgba(212,175,55,0.2)] cursor-pointer group"
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-xl mb-1 group-hover:text-[#D4AF37] transition-colors">
                              {character.name}
                            </h3>
                            <p className="font-['Lora',serif] text-[#D4AF37] text-sm">
                              {character.race_name} • {character.class_name}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-xl">
                              Ур. {character.level}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between mt-6">
                          <span className="font-['Lora',serif] text-[#F4EBD0]/60 text-sm flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {new Date(character.created_at).toLocaleDateString('ru-RU')}
                          </span>
                          <span className="flex items-center gap-1 text-[#D4AF37] text-sm font-['Lora',serif] opacity-0 group-hover:opacity-100 transition-opacity">
                            Подробнее <ChevronRight className="w-4 h-4" />
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'characters' && selectedCharacter && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <button 
                  onClick={() => setSelectedCharacter(null)}
                  className="mb-6 flex items-center gap-2 text-[#D4AF37] hover:text-[#F4EBD0] transition-colors font-['Lora',serif] text-sm"
                >
                  <ChevronRight className="w-4 h-4 rotate-180" /> Вернуться к списку
                </button>
                
                <div className="flex flex-col md:flex-row gap-8 items-start">
                  {/* Left Column: Avatar & Basic Info */}
                  <div className="w-full md:w-1/3 bg-[#111]/60 p-6 rounded-2xl border border-[#D4AF37]/30 text-center">
                    <div className="w-32 h-32 mx-auto rounded-full border-4 border-[#D4AF37]/30 flex items-center justify-center bg-[#1A1A1A] mb-4">
                      <User className="w-16 h-16 text-[#D4AF37]/50" />
                    </div>
                    <h2 className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0] mb-2">
                      {selectedCharacter.name}
                    </h2>
                    <p className="font-['Lora',serif] text-[#D4AF37] text-lg mb-6">
                      {selectedCharacter.race_name} • {selectedCharacter.class_name}
                    </p>
                    
                    <div className="flex justify-center gap-4 mb-6">
                      <div className="text-center">
                        <span className="block text-3xl font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]">{selectedCharacter.level}</span>
                        <span className="text-xs text-[#F4EBD0]/50 uppercase tracking-wider font-['Lora',serif]">Уровень</span>
                      </div>
                      <div className="w-px h-12 bg-[#D4AF37]/20" />
                      <div className="text-center">
                        <span className="block text-3xl font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]">{selectedCharacter.experience}</span>
                        <span className="text-xs text-[#F4EBD0]/50 uppercase tracking-wider font-['Lora',serif]">Опыт</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-6">
                      {/* HP Card */}
                      <div className="bg-[#111]/50 border border-[#D4AF37]/20 rounded-xl p-4 flex flex-col items-center justify-center min-h-[100px] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5 transition-all duration-300 shadow-md">
                        <Heart className="w-5 h-5 text-[#ff4444] mb-2" />
                        <span className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0]">{selectedCharacter.max_hp}</span>
                        <span className="text-xs text-[#F4EBD0]/50 mt-1 uppercase tracking-wider font-['Lora',serif]">Здоровье</span>
                      </div>

                      {/* AC Card */}
                      <div className="bg-[#111]/50 border border-[#D4AF37]/20 rounded-xl p-4 flex flex-col items-center justify-center min-h-[100px] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5 transition-all duration-300 shadow-md">
                        <Shield className="w-5 h-5 text-[#D4AF37] mb-2" />
                        <span className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0]">{selectedCharacter.armor_class}</span>
                        <span className="text-xs text-[#F4EBD0]/50 mt-1 uppercase tracking-wider font-['Lora',serif]">Класс Брони</span>
                      </div>

                      {/* Speed Card */}
                      <div className="bg-[#111]/50 border border-[#D4AF37]/20 rounded-xl p-4 flex flex-col items-center justify-center min-h-[100px] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5 transition-all duration-300 shadow-md">
                        <Zap className="w-5 h-5 text-[#5b9bd5] mb-2" />
                        <span className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0]">{selectedCharacter.speed}</span>
                        <span className="text-xs text-[#F4EBD0]/50 mt-1 uppercase tracking-wider font-['Lora',serif]">Скорость (фт)</span>
                      </div>

                      {/* Proficiency Bonus Card */}
                      <div className="bg-[#111]/50 border border-[#D4AF37]/20 rounded-xl p-4 flex flex-col items-center justify-center min-h-[100px] hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5 transition-all duration-300 shadow-md">
                        <Sparkles className="w-5 h-5 text-[#a67c00] mb-2" />
                        <span className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0]">+{selectedCharacter.proficiency_bonus}</span>
                        <span className="text-xs text-[#F4EBD0]/50 mt-1 uppercase tracking-wider font-['Lora',serif]">Бонус Маст.</span>
                      </div>
                    </div>

                    <button 
                      onClick={() => handleLevelUp(selectedCharacter.id)}
                      className="w-full py-3 bg-[#D4AF37] text-[#1A1A1A] rounded-xl font-bold font-['Cormorant_Garamond',serif] flex items-center justify-center gap-2 hover:bg-[#F4EBD0] transition-colors shadow-[0_0_15px_rgba(212,175,55,0.4)]"
                    >
                      <PlusCircle className="w-5 h-5" />
                      Повысить уровень
                    </button>
                  </div>

                  {/* Right Column: Collapsible Accordion Drawer */}
                  <div className="w-full md:w-2/3 space-y-4">
                    {/* Section 1: Способности */}
                    <div className="border border-[#D4AF37]/30 rounded-2xl bg-[#111]/40 overflow-hidden transition-all duration-300">
                      <button
                        onClick={() => setOpenSection(openSection === 'abilities' ? '' : 'abilities')}
                        className="w-full px-6 py-4 flex items-center justify-between text-left font-['Cormorant_Garamond',serif] font-bold text-xl text-[#D4AF37] hover:bg-[#D4AF37]/5 transition-colors border-b border-[#D4AF37]/10"
                      >
                        <span className="flex items-center gap-2">
                          <User className="w-5 h-5" />
                          Способности (Характеристики)
                        </span>
                        <span className={`transform transition-transform duration-300 ${openSection === 'abilities' ? 'rotate-90' : ''}`}>
                          <ChevronRight className="w-5 h-5" />
                        </span>
                      </button>
                      
                      <div className={`transition-all duration-500 ease-in-out ${
                        openSection === 'abilities' ? 'max-h-[800px] opacity-100 p-6' : 'max-h-0 opacity-0 overflow-hidden'
                      }`}>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                          {[
                            { label: 'Сила', value: selectedCharacter.strength, icon: Swords },
                            { label: 'Ловкость', value: selectedCharacter.dexterity, icon: Zap },
                            { label: 'Телосложение', value: selectedCharacter.constitution, icon: Heart },
                            { label: 'Интеллект', value: selectedCharacter.intelligence, icon: Brain },
                            { label: 'Мудрость', value: selectedCharacter.wisdom, icon: Eye },
                            { label: 'Харизма', value: selectedCharacter.charisma, icon: Sparkles },
                          ].map((stat) => (
                            <div key={stat.label} className="bg-[#111]/60 border border-[#D4AF37]/20 rounded-xl p-4 text-center flex flex-col items-center justify-center gap-2">
                              <stat.icon className="w-5 h-5 text-[#D4AF37]/70" />
                              <span className="font-['Lora',serif] text-xs text-[#F4EBD0]/60 uppercase tracking-widest">{stat.label}</span>
                              <span className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#F4EBD0]">{stat.value}</span>
                              <div className="w-10 h-6 bg-[#D4AF37]/20 rounded flex items-center justify-center font-bold text-sm text-[#D4AF37]">
                                {getStatModifier(stat.value)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Section 2: Снаряжение */}
                    <div className="border border-[#D4AF37]/30 rounded-2xl bg-[#111]/40 overflow-hidden transition-all duration-300">
                      <button
                        onClick={() => setOpenSection(openSection === 'equipment' ? '' : 'equipment')}
                        className="w-full px-6 py-4 flex items-center justify-between text-left font-['Cormorant_Garamond',serif] font-bold text-xl text-[#D4AF37] hover:bg-[#D4AF37]/5 transition-colors border-b border-[#D4AF37]/10"
                      >
                        <span className="flex items-center gap-2">
                          <Swords className="w-5 h-5" />
                          Снаряжение
                        </span>
                        <span className={`transform transition-transform duration-300 ${openSection === 'equipment' ? 'rotate-90' : ''}`}>
                          <ChevronRight className="w-5 h-5" />
                        </span>
                      </button>
                      
                      <div className={`transition-all duration-500 ease-in-out ${
                        openSection === 'equipment' ? 'max-h-[500px] opacity-100 p-6' : 'max-h-0 opacity-0 overflow-hidden'
                      }`}>
                        <div className="flex flex-wrap gap-2">
                          {selectedCharacter.equipment && selectedCharacter.equipment.length > 0 ? (
                            selectedCharacter.equipment.map((item) => (
                              <button
                                key={item}
                                onClick={() => handleItemClick(item)}
                                className="px-4 py-2 bg-[#D4AF37]/10 border border-[#D4AF37]/30 hover:bg-[#D4AF37]/20 hover:border-[#D4AF37]/50 text-sm rounded-xl font-['Lora',serif] text-[#F4EBD0]/90 shadow-[0_2px_8px_rgba(0,0,0,0.2)] transition-all active:scale-95 text-left"
                              >
                                {item}
                              </button>
                            ))
                          ) : (
                            <p className="text-[#F4EBD0]/40 italic text-sm font-['Lora',serif] w-full py-4 text-center">
                              У этого персонажа нет снаряжения.
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Section 3: Заклинания */}
                    <div className="border border-[#D4AF37]/30 rounded-2xl bg-[#111]/40 overflow-hidden transition-all duration-300">
                      <button
                        onClick={() => setOpenSection(openSection === 'spells' ? '' : 'spells')}
                        className="w-full px-6 py-4 flex items-center justify-between text-left font-['Cormorant_Garamond',serif] font-bold text-xl text-[#D4AF37] hover:bg-[#D4AF37]/5 transition-colors border-b border-[#D4AF37]/10"
                      >
                        <span className="flex items-center gap-2">
                          <Sparkles className="w-5 h-5" />
                          Заклинания 1-го уровня
                        </span>
                        <span className={`transform transition-transform duration-300 ${openSection === 'spells' ? 'rotate-90' : ''}`}>
                          <ChevronRight className="w-5 h-5" />
                        </span>
                      </button>
                      
                      <div className={`transition-all duration-500 ease-in-out ${
                        openSection === 'spells' ? 'max-h-[500px] opacity-100 p-6' : 'max-h-0 opacity-0 overflow-hidden'
                      }`}>
                        <div className="flex flex-wrap gap-2">
                          {selectedCharacter.spells?.known_spells && selectedCharacter.spells.known_spells.length > 0 ? (
                            selectedCharacter.spells.known_spells.map((spell) => (
                              <button
                                key={spell}
                                onClick={() => handleSpellClick(spell, false)}
                                className="px-4 py-2 bg-[#D4AF37]/10 border border-[#D4AF37]/30 hover:bg-[#D4AF37]/20 hover:border-[#D4AF37]/50 text-sm rounded-xl font-['Lora',serif] text-[#F4EBD0]/90 shadow-[0_2px_8px_rgba(0,0,0,0.2)] transition-all active:scale-95 text-left"
                              >
                                {spell}
                              </button>
                            ))
                          ) : (
                            <p className="text-[#F4EBD0]/40 italic text-sm font-['Lora',serif] w-full py-4 text-center">
                              У этого персонажа нет известных заклинаний 1-го уровня.
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Section 4: Заговоры */}
                    <div className="border border-[#D4AF37]/30 rounded-2xl bg-[#111]/40 overflow-hidden transition-all duration-300">
                      <button
                        onClick={() => setOpenSection(openSection === 'cantrips' ? '' : 'cantrips')}
                        className="w-full px-6 py-4 flex items-center justify-between text-left font-['Cormorant_Garamond',serif] font-bold text-xl text-[#D4AF37] hover:bg-[#D4AF37]/5 transition-colors border-b border-[#D4AF37]/10"
                      >
                        <span className="flex items-center gap-2">
                          <Zap className="w-5 h-5" />
                          Заговоры (Cantrips)
                        </span>
                        <span className={`transform transition-transform duration-300 ${openSection === 'cantrips' ? 'rotate-90' : ''}`}>
                          <ChevronRight className="w-5 h-5" />
                        </span>
                      </button>
                      
                      <div className={`transition-all duration-500 ease-in-out ${
                        openSection === 'cantrips' ? 'max-h-[500px] opacity-100 p-6' : 'max-h-0 opacity-0 overflow-hidden'
                      }`}>
                        <div className="flex flex-wrap gap-2">
                          {selectedCharacter.spells?.cantrips && selectedCharacter.spells.cantrips.length > 0 ? (
                            selectedCharacter.spells.cantrips.map((cantrip) => (
                              <button
                                key={cantrip}
                                onClick={() => handleSpellClick(cantrip, true)}
                                className="px-4 py-2 bg-[#D4AF37]/10 border border-[#D4AF37]/30 hover:bg-[#D4AF37]/20 hover:border-[#D4AF37]/50 text-sm rounded-xl font-['Lora',serif] text-[#F4EBD0]/90 shadow-[0_2px_8px_rgba(0,0,0,0.2)] transition-all active:scale-95 text-left"
                              >
                                {cantrip}
                              </button>
                            ))
                          ) : (
                            <p className="text-[#F4EBD0]/40 italic text-sm font-['Lora',serif] w-full py-4 text-center">
                              У этого персонажа нет известных заговоров.
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'chats' && (
              <div>
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6">
                  История Чатов
                </h2>
                {chatHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <MessageSquare className="w-16 h-16 text-[#D4AF37]/50 mx-auto mb-4" />
                    <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-lg">
                      История чатов пуста
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {chatHistory.map((chat) => (
                      <div
                        key={chat.id}
                        onClick={() => {
                          const event = new CustomEvent("open_ai_chat", {
                            detail: { chatId: chat.id }
                          });
                          window.dispatchEvent(event);
                        }}
                        className="p-6 bg-[#111]/50 rounded-xl border border-[#D4AF37]/20 hover:border-[#D4AF37]/50 transition-all duration-300 hover:shadow-[0_0_20px_rgba(212,175,55,0.2)] cursor-pointer"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-lg">
                            {chat.title}
                          </h3>
                          <span className="font-['Lora',serif] text-[#F4EBD0]/60 text-sm">
                            {chat.messageCount} сообщений
                          </span>
                        </div>
                        <p className="font-['Lora',serif] text-[#F4EBD0]/70 mb-3 line-clamp-2">
                          {chat.lastMessage}
                        </p>
                        <div className="flex items-center justify-between">
                          <span className="font-['Lora',serif] text-[#F4EBD0]/60 text-sm flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {chat.createdAt}
                          </span>
                          <button className="px-3 py-1 bg-[#D4AF37]/20 hover:bg-[#D4AF37]/30 rounded-lg text-[#D4AF37] text-sm font-['Lora',serif] transition-colors">
                            Продолжить
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Detailed Spell / Item Modal */}
      <AnimatePresence>
        {activeModalDetail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setActiveModalDetail(null)}
              className="absolute inset-0 bg-[#000]/80 backdrop-blur-sm"
            />

            {/* Modal content box */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-xl bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/40 rounded-2xl shadow-2xl p-6 overflow-hidden z-10"
            >
              {/* Subtle parchment background texture overlay */}
              <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')] bg-cover mix-blend-overlay" />

              {/* Close button */}
              <button
                onClick={() => setActiveModalDetail(null)}
                className="absolute top-4 right-4 text-[#F4EBD0]/70 hover:text-[#D4AF37] transition-colors z-20"
              >
                <X className="w-6 h-6" />
              </button>

              <div className="relative z-10">
                {/* Header info */}
                <h3 className="font-['Cormorant_Garamond',serif] font-bold text-3xl text-[#D4AF37] tracking-wide mb-1">
                  {activeModalDetail.name}
                </h3>
                {activeModalDetail.subtitle && (
                  <p className="font-['Lora',serif] text-sm text-[#F4EBD0]/60 italic uppercase tracking-wider mb-4">
                    {activeModalDetail.subtitle}
                  </p>
                )}
                <div className="w-12 h-[2px] bg-[#D4AF37] opacity-60 mb-6" />

                {/* Properties grid */}
                {activeModalDetail.properties && activeModalDetail.properties.length > 0 && (
                  <div className="grid grid-cols-2 gap-4 mb-6 bg-[#111]/60 border border-[#D4AF37]/15 rounded-xl p-4">
                    {activeModalDetail.properties.map((prop, idx) => (
                      <div key={idx} className="flex flex-col">
                        <span className="font-['Lora',serif] text-[#D4AF37]/70 text-xs uppercase tracking-wider">
                          {prop.label}
                        </span>
                        <span className="font-['Lora',serif] text-[#F4EBD0] text-sm font-medium mt-0.5">
                          {prop.value}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Loading spinner or text description */}
                <div className="max-h-60 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-[#D4AF37]/20 scrollbar-track-transparent">
                  {modalLoading ? (
                    <div className="flex items-center gap-3 py-6 justify-center text-[#D4AF37]">
                      <Loader2 className="w-6 h-6 animate-spin" />
                      <span className="font-['Lora',serif] text-sm text-[#F4EBD0]/80">Извлечение записей из библиотек...</span>
                    </div>
                  ) : (
                    <p className="font-['Lora',serif] text-[#F4EBD0]/85 text-sm leading-relaxed whitespace-pre-wrap">
                      {activeModalDetail.description}
                    </p>
                  )}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
