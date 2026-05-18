import { useState, useEffect } from "react";
import { Sparkles, User, Sword, Shield, Heart, Zap, Eye, Crown, Dices, List, Calculator, Edit3, GripHorizontal, Info } from "lucide-react";
import { useNavigate } from "react-router";
import { api } from "../../api/client";
import { useCharacterStore } from "../../store/characterStore";
import { AbilityScores, ReferenceItem } from "../../types/api";
import { InfoModal } from "../components/InfoModal";

const abilityNames: Record<keyof AbilityScores, string> = {
  strength: 'Сила',
  dexterity: 'Ловкость',
  constitution: 'Телосложение',
  intelligence: 'Интеллект',
  wisdom: 'Мудрость',
  charisma: 'Харизма'
};

type GenMethod = 'roll' | 'standard' | 'pointbuy' | 'manual';

const parseCostToGold = (costStr?: string): number => {
  if (!costStr) return 0;
  const match = costStr.trim().match(/^([\d.,]+)\s*(зм|см|мм|gp|sp|cp)/i);
  if (!match) {
    const num = parseFloat(costStr.replace(/[^0-9.,]/g, '').replace(',', '.'));
    return isNaN(num) ? 0 : num;
  }
  const val = parseFloat(match[1].replace(',', '.'));
  if (isNaN(val)) return 0;
  const unit = match[2].toLowerCase();
  if (unit === 'зм' || unit === 'gp') {
    return val;
  } else if (unit === 'см' || unit === 'sp') {
    return val * 0.1;
  } else if (unit === 'мм' || unit === 'cp') {
    return val * 0.01;
  }
  return val;
};

export function CreateCharacterPage() {
  const [step, setStep] = useState(1);

  const { 
    name, race, characterClass, background, abilities, cantrips, knownSpells, equipment,
    setName, setRace, setClass, setBackground, setAbilities, setCantrips, setKnownSpells, setEquipment, reset 
  } = useCharacterStore();
  
  const [races, setRaces] = useState<ReferenceItem[]>([]);
  const [classes, setClasses] = useState<ReferenceItem[]>([]);
  const [backgrounds, setBackgrounds] = useState<ReferenceItem[]>([]);
  const [availableCantrips, setAvailableCantrips] = useState<any[]>([]);
  const [availableSpells, setAvailableSpells] = useState<any[]>([]);
  const [availableEquipment, setAvailableEquipment] = useState<any[]>([]);
  const [standardArrayData, setStandardArrayData] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRolling, setIsRolling] = useState(false);
  const navigate = useNavigate();
  
  // Info Modal state
  const [infoModalOpen, setInfoModalOpen] = useState(false);
  const [infoModalTitle, setInfoModalTitle] = useState("");
  const [infoModalDesc, setInfoModalDesc] = useState("");

  const [method, setMethod] = useState<GenMethod>('roll');
  const [unassignedValues, setUnassignedValues] = useState<number[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [racesData, classesData, backgroundsData, arrayData, cantripsData, spells1Data, itemsData] = await Promise.all([
          api.reference.getRaces(),
          api.reference.getClasses(),
          api.reference.getBackgrounds(),
          api.characters.getStandardArray().catch(() => [15, 14, 13, 12, 10, 8]),
          api.reference.getSpells("cantrips").catch(() => ({items: {}})),
          api.reference.getSpells("1").catch(() => ({items: {}})),
          api.reference.getItems().catch(() => ({}))
        ]);
        setRaces(racesData.items);
        setClasses(classesData.items);
        setBackgrounds(backgroundsData.items);
        setStandardArrayData(arrayData);
        
        // Преобразуем словари в массивы для удобства
        setAvailableCantrips(Object.entries(cantripsData.items).map(([k, v]) => ({ name: k, ...(v as object) })));
        setAvailableSpells(Object.entries(spells1Data.items).map(([k, v]) => ({ name: k, ...(v as object) })));
        
        // Для снаряжения собираем полноценные объекты
        if (itemsData && typeof itemsData === 'object') {
           const eqList: any[] = [];
           Object.entries(itemsData).forEach(([catKey, cat]: [string, any]) => {
             if (typeof cat === 'object') {
               Object.entries(cat).forEach(([itemKey, itemVal]: [string, any]) => {
                 eqList.push({
                   key: itemKey,
                   name: itemVal.name || itemKey,
                   description: itemVal.description || itemVal.category || '',
                   cost: itemVal.cost || ''
                 });
               });
             }
           });
           setAvailableEquipment(eqList);
        }
      } catch (error) {
        console.error('Failed to fetch reference data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleNext = () => {
    if (step === 5) {
      if (characterClass?.is_spellcaster) {
        setStep(6);
      } else {
        setStep(7);
      }
    } else if (step < 7) {
      setStep(step + 1);
    }
  };

  const handlePrev = () => {
    if (step === 7) {
      if (characterClass?.is_spellcaster) {
        setStep(6);
      } else {
        setStep(5);
      }
    } else if (step > 1) {
      setStep(step - 1);
    }
  };

  const initAbilities = (val: number) => {
    setAbilities({
      strength: val, dexterity: val, constitution: val,
      intelligence: val, wisdom: val, charisma: val
    });
  };

  const handleMethodChange = (m: GenMethod) => {
    setMethod(m);
    if (m === 'pointbuy') {
      initAbilities(8);
      setUnassignedValues([]);
    } else if (m === 'manual') {
      initAbilities(10);
      setUnassignedValues([]);
    } else if (m === 'standard') {
      initAbilities(0); 
      setUnassignedValues([...standardArrayData]);
    } else {
      setAbilities(null);
      setUnassignedValues([]);
    }
  };

  const handleRollAbilities = async () => {
    setIsRolling(true);
    try {
      const result = await api.characters.rollAbilities();
      setUnassignedValues(result.sort((a,b) => b-a));
      initAbilities(0);
    } catch (error) {
      console.error('Failed to roll abilities:', error);
      const fallback = Array.from({length: 6}, () => Math.floor(Math.random() * 10) + 8).sort((a,b) => b-a);
      setUnassignedValues(fallback);
      initAbilities(0);
    } finally {
      setIsRolling(false);
    }
  };

  // --- Drag and Drop Logic ---
  const handleDragStart = (e: React.DragEvent, source: 'pool' | keyof AbilityScores, val: number, idx?: number) => {
    e.dataTransfer.setData('source', source);
    e.dataTransfer.setData('value', val.toString());
    if (idx !== undefined) e.dataTransfer.setData('index', idx.toString());
  };

  const handleDropOnStat = (e: React.DragEvent, targetStat: keyof AbilityScores) => {
    e.preventDefault();
    if (!abilities) return;
    const source = e.dataTransfer.getData('source');
    if (!source) return;
    
    const value = parseInt(e.dataTransfer.getData('value'), 10);
    const targetCurrentValue = abilities[targetStat];

    if (source === 'pool') {
      const idx = parseInt(e.dataTransfer.getData('index'), 10);
      const newPool = [...unassignedValues];
      newPool.splice(idx, 1);
      if (targetCurrentValue > 0) newPool.push(targetCurrentValue);
      setUnassignedValues(newPool.sort((a,b) => b-a));
      setAbilities({ ...abilities, [targetStat]: value });
    } else if (source !== targetStat) {
      setAbilities({
        ...abilities,
        [targetStat]: value,
        [source as keyof AbilityScores]: targetCurrentValue
      });
    }
  };

  const handleDropOnPool = (e: React.DragEvent) => {
    e.preventDefault();
    if (!abilities) return;
    const source = e.dataTransfer.getData('source');
    if (source && source !== 'pool') {
      const value = parseInt(e.dataTransfer.getData('value'), 10);
      setAbilities({ ...abilities, [source as keyof AbilityScores]: 0 });
      setUnassignedValues([...unassignedValues, value].sort((a,b) => b-a));
    }
  };

  const allowDrop = (e: React.DragEvent) => {
    e.preventDefault();
  };
  // -------------------------

  const handleSave = async () => {
    if (!name || !race || !characterClass || !abilities) return;
    
    if ((method === 'standard' || method === 'roll') && Object.values(abilities).some(v => v === 0)) {
      alert("Пожалуйста, распределите все значения.");
      return;
    }

    setIsSubmitting(true);
    try {
      const userStr = localStorage.getItem("currentUser");
      const userId = userStr ? JSON.parse(userStr).id : 1;

      const response = await api.characters.createCharacter({
        user_id: userId,
        name: name,
        race_name: race.name,
        class_id: characterClass.id || characterClass.key || characterClass.name,
        background_id: useCharacterStore.getState().background?.id || "",
        abilities: abilities,
        cantrips: useCharacterStore.getState().cantrips,
        known_spells: useCharacterStore.getState().knownSpells,
        equipment: useCharacterStore.getState().equipment
      });
      alert('Персонаж успешно создан и сохранен на бекенде!');
      reset();
      setStep(1);
      navigate("/my-works", { state: { newCharacterId: response.character_id } });
    } catch (error) {
      console.error('Save failed:', error);
      alert('Ошибка при сохранении персонажа. Проверьте консоль для деталей.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getPointBuyCost = (val: number) => {
    if (val <= 8) return 0;
    if (val === 9) return 1;
    if (val === 10) return 2;
    if (val === 11) return 3;
    if (val === 12) return 4;
    if (val === 13) return 5;
    if (val === 14) return 7;
    if (val === 15) return 9;
    return 0;
  };

  const pointsLeft = () => {
    if (!abilities) return 27;
    return 27 - Object.values(abilities).reduce((acc, val) => acc + getPointBuyCost(val), 0);
  };

  const updateStat = (stat: keyof AbilityScores, delta: number) => {
    if (!abilities) return;
    const current = abilities[stat];
    const next = current + delta;
    
    if (method === 'pointbuy') {
      if (next < 8 || next > 15) return;
      const costDiff = getPointBuyCost(next) - getPointBuyCost(current);
      if (pointsLeft() - costDiff < 0) return;
    } else if (method === 'manual') {
      if (next < 3 || next > 18) return;
    }
    
    setAbilities({ ...abilities, [stat]: next });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
        <div className="text-[#D4AF37] text-2xl font-['Cormorant_Garamond',serif] animate-pulse">Загрузка древних свитков...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1A1A1A] pt-24 pb-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0]" style={{ fontSize: 'clamp(3rem, 8vw, 4rem)', lineHeight: 1.2 }}>
            Создание <span className="text-[#D4AF37]">Героя</span>
          </h1>
          <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-lg mt-4 max-w-2xl mx-auto">
            Воплотите своего персонажа в жизнь. Выберите расу, класс и определите его судьбу в мире Dungeons & Dragons.
          </p>
          <div className="w-16 h-1 bg-[#D4AF37] mx-auto mt-6 opacity-60" />
        </div>

        {/* Progress Bar */}
        <div className="flex justify-center mb-8 sm:mb-12 overflow-x-auto pb-2">
          <div className="flex items-center gap-1 sm:gap-4 shrink-0">
            {[1, 2, 3, 4, 5, 6, 7].map((num) => {
              // Скрываем шаг 6 для немагов
              if (num === 6 && characterClass && !characterClass.is_spellcaster) return null;
              
              return (
                <div key={num} className="flex items-center">
                  <div
                    className={`w-7 h-7 sm:w-8 sm:h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center font-['Cormorant_Garamond',serif] font-bold text-sm md:text-base transition-all duration-500 ${
                      step >= num
                        ? 'bg-[#D4AF37] text-[#1A1A1A] shadow-[0_0_20px_rgba(212,175,55,0.5)]'
                        : 'bg-[#2c2722] border-2 border-[#D4AF37]/30 text-[#D4AF37]/50'
                    }`}
                  >
                    {num}
                  </div>
                  {num < 7 && (
                    <div
                      className={`w-3 sm:w-6 md:w-12 h-1 mx-0.5 sm:mx-1 md:mx-2 transition-all duration-500 ${
                        step > num ? 'bg-[#D4AF37]' : 'bg-[#D4AF37]/20'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="relative bg-gradient-to-br from-[#2c2722] to-[#1e1a17] border border-[#D4AF37]/30 rounded-2xl p-8 sm:p-12 shadow-2xl overflow-hidden group hover:border-[#D4AF37]/50 transition-all duration-500 min-h-[500px]">
          <div className="absolute inset-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1711107762183-d99536fb7d6e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZWRpZXZhbCUyMHBhcmNobWVudCUyMHRleHR1cmUlMjBkYXJrfGVufDF8fHx8MTc3NTE0MTcyMXww&ixlib=rb-4.1.0&q=80&w=1080')] bg-cover mix-blend-overlay rounded-2xl" />

          <div className="relative z-10">
            {step === 1 && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6 text-center">
                  Шаг 1: Основная информация
                </h2>
                <div className="max-w-md mx-auto space-y-6">
                  <div>
                    <label className="block font-['Lora',serif] text-[#D4AF37] text-sm mb-2 tracking-wide">
                      Имя персонажа
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full px-4 py-3 bg-[#111]/80 backdrop-blur-sm border-2 border-[#D4AF37]/20 rounded-xl text-[#F4EBD0] placeholder-[#F4EBD0]/40 font-['Lora',serif] focus:outline-none focus:border-[#D4AF37]/60 focus:bg-[#1A1A1A]/90 focus:shadow-[0_0_30px_rgba(212,175,55,0.15)] transition-all"
                      placeholder="Введите имя героя"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6 text-center">
                  Шаг 2: Выберите расу
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {races.map((r) => (
                    <div
                      key={r.name}
                      onClick={() => setRace(r)}
                      className={`relative p-4 rounded-xl border-2 transition-all duration-300 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] text-left cursor-pointer group ${
                        race?.name === r.name
                          ? 'border-[#D4AF37] bg-[#D4AF37]/10 shadow-[0_0_20px_rgba(212,175,55,0.5)]'
                          : 'border-[#D4AF37]/20 bg-[#111]/50 hover:border-[#D4AF37]/50'
                      }`}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setInfoModalTitle(r.name);
                          setInfoModalDesc(r.description);
                          setInfoModalOpen(true);
                        }}
                        className="absolute top-4 right-4 text-[#D4AF37]/50 hover:text-[#D4AF37] transition-colors"
                        title="Подробнее"
                      >
                        <Info className="w-5 h-5" />
                      </button>
                      <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-lg mb-2 pr-8">
                        {r.name}
                      </h3>
                      <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm line-clamp-3 pr-2">
                        {r.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6 text-center">
                  Шаг 3: Выберите класс
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {classes.map((cls) => {
                    return (
                      <div
                        key={cls.name}
                        onClick={() => setClass(cls)}
                        className={`relative p-4 rounded-xl border-2 transition-all duration-300 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] text-left cursor-pointer group ${
                          characterClass?.name === cls.name
                            ? 'border-[#D4AF37] bg-[#D4AF37]/10 shadow-[0_0_20px_rgba(212,175,55,0.5)]'
                            : 'border-[#D4AF37]/20 bg-[#111]/50 hover:border-[#D4AF37]/50'
                        }`}
                      >
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setInfoModalTitle(cls.name);
                            setInfoModalDesc(cls.description);
                            setInfoModalOpen(true);
                          }}
                          className="absolute top-4 right-4 text-[#D4AF37]/50 hover:text-[#D4AF37] transition-colors"
                          title="Подробнее"
                        >
                          <Info className="w-5 h-5" />
                        </button>
                        <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-lg mb-2 pr-8">
                          {cls.name}
                        </h3>
                        <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm line-clamp-3 pr-2">
                          {cls.description}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6 text-center">
                  Шаг 4: Выберите предысторию
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {backgrounds.map((bg) => (
                    <div
                      key={bg.id || bg.name}
                      onClick={() => setBackground(bg)}
                      className={`relative p-4 rounded-xl border-2 transition-all duration-300 hover:shadow-[0_0_20px_rgba(212,175,55,0.3)] text-left cursor-pointer group ${
                        background?.name === bg.name
                          ? 'border-[#D4AF37] bg-[#D4AF37]/10 shadow-[0_0_20px_rgba(212,175,55,0.5)]'
                          : 'border-[#D4AF37]/20 bg-[#111]/50 hover:border-[#D4AF37]/50'
                      }`}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setInfoModalTitle(bg.name);
                          setInfoModalDesc(bg.description);
                          setInfoModalOpen(true);
                        }}
                        className="absolute top-4 right-4 text-[#D4AF37]/50 hover:text-[#D4AF37] transition-colors"
                        title="Подробнее"
                      >
                        <Info className="w-5 h-5" />
                      </button>
                      <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-lg mb-2 pr-8">
                        {bg.name}
                      </h3>
                      <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-sm line-clamp-3 pr-2">
                        {bg.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-2xl mb-6 text-center">
                  Шаг 5: Характеристики
                </h2>
                <div className="max-w-4xl mx-auto flex flex-col items-center">
                  
                  {/* Method Selector */}
                  <div className="flex flex-wrap justify-center gap-4 mb-8">
                    {[
                      { id: 'roll', label: 'Бросок кубиков', icon: Dices },
                      { id: 'standard', label: 'Стандартный набор', icon: List },
                      { id: 'pointbuy', label: 'Закупка (Point Buy)', icon: Calculator },
                      { id: 'manual', label: 'Произвольно', icon: Edit3 }
                    ].map((m) => {
                      const Icon = m.icon;
                      return (
                        <button
                          key={m.id}
                          onClick={() => handleMethodChange(m.id as GenMethod)}
                          className={`flex items-center gap-2 px-6 py-3 rounded-xl border-2 transition-all duration-300 font-['Lora',serif] font-bold text-sm ${
                            method === m.id
                              ? 'border-[#D4AF37] bg-[#D4AF37]/20 text-[#D4AF37] shadow-[0_0_15px_rgba(212,175,55,0.3)]'
                              : 'border-[#D4AF37]/30 bg-[#111]/50 text-[#F4EBD0]/70 hover:border-[#D4AF37]/60'
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          {m.label}
                        </button>
                      )
                    })}
                  </div>

                  {/* Method Content */}
                  <div className="w-full bg-[#111]/30 p-6 rounded-2xl border border-[#D4AF37]/20 mb-8">
                    
                    {method === 'roll' && !abilities && (
                      <div className="flex flex-col items-center justify-center py-6">
                        <button
                          onClick={handleRollAbilities}
                          disabled={isRolling}
                          className="px-8 py-3 font-['Cormorant_Garamond',serif] font-bold text-lg text-[#1A1A1A] bg-[#D4AF37] rounded-xl hover:bg-[#F4EBD0] transition-colors shadow-[0_0_20px_rgba(212,175,55,0.4)] disabled:opacity-50"
                        >
                          {isRolling ? 'Бросаем кубики...' : 'Бросить кубики (4d6)'}
                        </button>
                        <p className="text-[#F4EBD0]/50 mt-4 text-sm font-['Lora',serif]">Нажмите кнопку, чтобы сгенерировать 6 значений.</p>
                      </div>
                    )}

                    {method === 'pointbuy' && (
                      <div className="text-center mb-6">
                        <p className="font-['Cormorant_Garamond',serif] text-2xl text-[#D4AF37]">
                          Осталось очков: <span className="font-bold text-3xl">{pointsLeft()}</span> / 27
                        </p>
                      </div>
                    )}

                    {/* DND Pool for Roll and Standard */}
                    {(method === 'roll' || method === 'standard') && abilities && (
                      <div 
                        className="text-center mb-8 p-4 sm:p-6 border-2 border-dashed border-[#D4AF37]/30 rounded-2xl bg-[#1A1A1A]/50 min-h-[100px] sm:min-h-[140px] flex flex-col items-center justify-center transition-all"
                        onDrop={handleDropOnPool}
                        onDragOver={allowDrop}
                      >
                        <p className="font-['Lora',serif] text-[#F4EBD0]/70 mb-4 text-sm tracking-wide">
                          {unassignedValues.length > 0 
                            ? <>
                                <span className="hidden sm:inline">Резерв: перетащите эти значения в слоты характеристик ниже</span>
                                <span className="sm:hidden">Резерв: нажмите на значение в слоте характеристики, чтобы выбрать из этих чисел</span>
                              </>
                            : "Все значения распределены. Вы можете изменить, нажав на слот характеристики."}
                        </p>
                        {/* Desktop: draggable chips */}
                        <div className="hidden sm:flex flex-wrap justify-center gap-4 min-h-[50px] w-full items-center">
                          {unassignedValues.map((val, i) => (
                            <div 
                              key={`${i}-${val}`} 
                              draggable
                              onDragStart={(e) => handleDragStart(e, 'pool', val, i)}
                              className="px-5 py-3 rounded-xl bg-gradient-to-br from-[#D4AF37] to-[#B8962E] text-[#1A1A1A] font-bold text-3xl font-['Cormorant_Garamond',serif] cursor-grab active:cursor-grabbing shadow-[0_5px_15px_rgba(212,175,55,0.4)] flex items-center gap-2 hover:scale-110 transition-transform"
                            >
                              <GripHorizontal className="w-5 h-5 opacity-40" />
                              {val}
                            </div>
                          ))}
                        </div>
                        {/* Mobile: non-draggable chips (selection happens in stat slots) */}
                        <div className="sm:hidden flex flex-wrap justify-center gap-2 min-h-[40px] w-full items-center">
                          {unassignedValues.map((val, i) => (
                            <div 
                              key={`${i}-${val}`}
                              className="px-4 py-2 rounded-xl bg-gradient-to-br from-[#D4AF37] to-[#B8962E] text-[#1A1A1A] font-bold text-2xl font-['Cormorant_Garamond',serif] shadow-md"
                            >
                              {val}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Stats Grid */}
                    {abilities && (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 w-full mt-4">
                        {(Object.entries(abilities) as [keyof AbilityScores, number][]).map(([stat, value]) => (
                          <div 
                            key={stat} 
                            className={`text-center flex flex-col items-center justify-center gap-2 sm:gap-3 p-3 sm:p-5 rounded-2xl border transition-all duration-300 ${
                              (method === 'standard' || method === 'roll') && value === 0
                                ? "bg-[#1A1A1A]/80 border-dashed border-[#D4AF37]/50 opacity-80"
                                : "bg-[#111]/60 border-solid border-[#D4AF37]/20 shadow-inner"
                            }`}
                            onDrop={(e) => (method === 'standard' || method === 'roll') && handleDropOnStat(e, stat)}
                            onDragOver={(method === 'standard' || method === 'roll') ? allowDrop : undefined}
                          >
                            <label className="block font-['Lora',serif] text-[#D4AF37] text-xs sm:text-sm uppercase tracking-widest pointer-events-none">
                              {abilityNames[stat]}
                            </label>
                            
                            {(method === 'standard' || method === 'roll') ? (
                              <>
                                {/* Desktop: drag target */}
                                <div 
                                  draggable={value > 0}
                                  onDragStart={(e) => value > 0 && handleDragStart(e, stat, value)}
                                  className={`hidden sm:flex w-20 h-16 sm:w-24 sm:h-20 flex-col items-center justify-center rounded-xl transition-all ${
                                    value > 0 
                                      ? "bg-[#D4AF37]/10 border border-[#D4AF37]/40 text-[#F4EBD0] cursor-grab active:cursor-grabbing shadow-[0_0_15px_rgba(212,175,55,0.2)] hover:border-[#D4AF37]/80 hover:bg-[#D4AF37]/20"
                                      : "bg-[#1A1A1A] border border-dashed border-[#333] text-[#F4EBD0]/20"
                                  }`}
                                >
                                  {value > 0 ? (
                                    <span className="font-['Cormorant_Garamond',serif] font-bold text-4xl pointer-events-none">
                                      {value}
                                    </span>
                                  ) : (
                                    <span className="font-['Lora',serif] text-xs pointer-events-none text-center px-1">Перетащите сюда</span>
                                  )}
                                </div>
                                {/* Mobile: tap-to-assign button */}
                                <div className="sm:hidden flex flex-col items-center gap-1 w-full">
                                  {value > 0 ? (
                                    <button
                                      onClick={() => {
                                        const newPool = [...unassignedValues, value].sort((a,b) => b-a);
                                        setUnassignedValues(newPool);
                                        setAbilities({ ...abilities, [stat]: 0 });
                                      }}
                                      className="w-full py-2 rounded-xl bg-[#D4AF37]/10 border border-[#D4AF37]/40 text-[#F4EBD0] active:scale-95 transition-all"
                                    >
                                      <span className="font-['Cormorant_Garamond',serif] font-bold text-3xl">{value}</span>
                                      <span className="block text-[#D4AF37]/60 text-xs font-['Lora',serif]">нажмите для возврата</span>
                                    </button>
                                  ) : (
                                    <div className="w-full">
                                      {unassignedValues.length > 0 ? (
                                        <div className="flex flex-wrap gap-1 justify-center">
                                          {unassignedValues.map((val, i) => (
                                            <button
                                              key={`${i}-${val}`}
                                              onClick={() => {
                                                const newPool = [...unassignedValues];
                                                newPool.splice(i, 1);
                                                setUnassignedValues(newPool.sort((a,b) => b-a));
                                                setAbilities({ ...abilities, [stat]: val });
                                              }}
                                              className="px-3 py-1.5 rounded-lg bg-gradient-to-br from-[#D4AF37] to-[#B8962E] text-[#1A1A1A] font-bold text-lg font-['Cormorant_Garamond',serif] active:scale-95 transition-transform shadow-md"
                                            >
                                              {val}
                                            </button>
                                          ))}
                                        </div>
                                      ) : (
                                        <span className="text-[#F4EBD0]/30 font-['Lora',serif] text-xs">пусто</span>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </>
                            ) : (
                              <div className="flex items-center justify-center gap-3 mt-2">
                                <button
                                  onClick={() => updateStat(stat, -1)}
                                  disabled={
                                    (method === 'pointbuy' && value <= 8) || 
                                    (method === 'manual' && value <= 3)
                                  }
                                  className="w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center rounded-full bg-[#D4AF37]/10 hover:bg-[#D4AF37]/30 text-[#D4AF37] font-bold transition-colors disabled:opacity-30 disabled:cursor-not-allowed border border-[#D4AF37]/30 text-xl pb-1"
                                >
                                  -
                                </button>
                                <span className="w-10 sm:w-12 text-center font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-3xl sm:text-4xl">
                                  {value}
                                </span>
                                <button
                                  onClick={() => updateStat(stat, 1)}
                                  disabled={
                                    (method === 'pointbuy' && (value >= 15 || pointsLeft() < getPointBuyCost(value + 1) - getPointBuyCost(value))) ||
                                    (method === 'manual' && value >= 18)
                                  }
                                  className="w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center rounded-full bg-[#D4AF37]/10 hover:bg-[#D4AF37]/30 text-[#D4AF37] font-bold transition-colors disabled:opacity-30 disabled:cursor-not-allowed border border-[#D4AF37]/30 text-xl pb-1"
                                >
                                  +
                                </button>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {/* Summary Footer */}
                  <div className="text-center p-6 border border-[#D4AF37]/30 rounded-2xl bg-[#111]/40 w-full max-w-md">
                    <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-3xl mb-2">
                      {name || 'Безымянный герой'}
                    </h3>
                    <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-lg">
                      {race?.name} {characterClass?.name} • {background?.name || 'Без предыстории'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {step === 6 && characterClass?.is_spellcaster && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-3xl mb-4 text-center">
                  Шаг 6: Выберите заклинания и заговоры
                </h2>
                <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-center text-sm mb-8 max-w-2xl mx-auto">
                  Ваш класс обладает способностью творить заклинания. Выберите заговоры и заклинания 1-го уровня, которые знает ваш герой.
                </p>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Заговоры */}
                  <div className="border border-[#D4AF37]/20 rounded-2xl p-6 bg-[#111]/30">
                    <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-xl mb-4 pb-2 border-b border-[#D4AF37]/20 flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Zap className="w-5 h-5" />
                        Заговоры (Cantrips)
                      </span>
                      <span className={`text-sm ${cantrips.length === 3 ? 'text-[#D4AF37] font-bold' : 'text-[#F4EBD0]/60'}`}>
                        Выбрано: {cantrips.length} / 3
                      </span>
                    </h3>
                    <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2 custom-scrollbar">
                      {availableCantrips
                        .filter(c => {
                          const clsName = characterClass?.name?.toLowerCase() || '';
                          return c.Классы && c.Классы.toLowerCase().includes(clsName);
                        })
                        .map(c => {
                          const isSelected = cantrips.includes(c.name);
                          return (
                            <div
                              key={c.name}
                              onClick={() => {
                                if (isSelected) {
                                  setCantrips(cantrips.filter(name => name !== c.name));
                                } else {
                                  if (cantrips.length >= 3) {
                                    alert("Вы достигли лимита заговоров (максимум 3)!");
                                    return;
                                  }
                                  setCantrips([...cantrips, c.name]);
                                }
                              }}
                              className={`p-4 rounded-xl border-2 transition-all duration-300 cursor-pointer flex flex-col justify-between ${
                                isSelected
                                  ? 'border-[#D4AF37] bg-[#D4AF37]/10 shadow-[0_0_15px_rgba(212,175,55,0.2)]'
                                  : 'border-[#D4AF37]/20 bg-[#111]/50 hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5'
                              }`}
                            >
                              <div className="flex justify-between items-center mb-1">
                                <h4 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-lg">
                                  {c.name}
                                </h4>
                                {isSelected && (
                                  <span className="text-xs bg-[#D4AF37] text-[#111] px-2 py-0.5 rounded-full font-bold">
                                    Выбрано
                                  </span>
                                )}
                              </div>
                              <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-xs line-clamp-3">
                                {c.описание || c.информация || 'Описание отсутствует.'}
                              </p>
                            </div>
                          );
                        })}
                      {availableCantrips.filter(c => {
                        const clsName = characterClass?.name?.toLowerCase() || '';
                        return c.Классы && c.Классы.toLowerCase().includes(clsName);
                      }).length === 0 && (
                        <p className="text-center text-[#F4EBD0]/40 text-sm py-8 font-['Lora',serif]">
                          Нет доступных заговоров для этого класса.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Заклинания 1 уровня */}
                  <div className="border border-[#D4AF37]/20 rounded-2xl p-6 bg-[#111]/30">
                    <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-xl mb-4 pb-2 border-b border-[#D4AF37]/20 flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5" />
                        Заклинания 1-го уровня
                      </span>
                      <span className={`text-sm ${knownSpells.length === 2 ? 'text-[#D4AF37] font-bold' : 'text-[#F4EBD0]/60'}`}>
                        Выбрано: {knownSpells.length} / 2
                      </span>
                    </h3>
                    <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2 custom-scrollbar">
                      {availableSpells
                        .filter(s => {
                          const clsName = characterClass?.name?.toLowerCase() || '';
                          return s.Классы && s.Классы.toLowerCase().includes(clsName);
                        })
                        .map(s => {
                          const isSelected = knownSpells.includes(s.name);
                          return (
                            <div
                              key={s.name}
                              onClick={() => {
                                if (isSelected) {
                                  setKnownSpells(knownSpells.filter(name => name !== s.name));
                                } else {
                                  if (knownSpells.length >= 2) {
                                    alert("Вы можете выбрать не более 2 заклинаний 1-го уровня!");
                                    return;
                                  }
                                  setKnownSpells([...knownSpells, s.name]);
                                }
                              }}
                              className={`p-4 rounded-xl border-2 transition-all duration-300 cursor-pointer flex flex-col justify-between ${
                                isSelected
                                  ? 'border-[#D4AF37] bg-[#D4AF37]/10 shadow-[0_0_15px_rgba(212,175,55,0.2)]'
                                  : 'border-[#D4AF37]/20 bg-[#111]/50 hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5'
                              }`}
                            >
                              <div className="flex justify-between items-center mb-1">
                                <h4 className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-lg">
                                  {s.name}
                                </h4>
                                {isSelected && (
                                  <span className="text-xs bg-[#D4AF37] text-[#111] px-2 py-0.5 rounded-full font-bold">
                                    Выбрано
                                  </span>
                                )}
                              </div>
                              <p className="font-['Lora',serif] text-[#F4EBD0]/70 text-xs line-clamp-3">
                                {s.описание || s.информация || 'Описание отсутствует.'}
                              </p>
                            </div>
                          );
                        })}
                      {availableSpells.filter(s => {
                        const clsName = characterClass?.name?.toLowerCase() || '';
                        return s.Классы && s.Классы.toLowerCase().includes(clsName);
                      }).length === 0 && (
                        <p className="text-center text-[#F4EBD0]/40 text-sm py-8 font-['Lora',serif]">
                          Нет доступных заклинаний для этого класса.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {step === 7 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-500">
                <h2 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-3xl mb-4 text-center">
                  Шаг 7: Выберите снаряжение и проверьте героя
                </h2>
                
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                  {/* Левая колонка - Снаряжение */}
                  <div className="lg:col-span-5 border border-[#D4AF37]/20 rounded-2xl p-6 bg-[#111]/30">
                    {(() => {
                      const totalSpentGold = equipment.reduce((sum, itemName) => {
                        const item = availableEquipment.find(eq => eq.name === itemName);
                        return sum + parseCostToGold(item?.cost);
                      }, 0);
                      return (
                        <>
                          <h3 className="font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] text-xl mb-2 pb-2 border-b border-[#D4AF37]/20 flex items-center justify-between">
                            <span className="flex items-center gap-2">
                              <Sword className="w-5 h-5" />
                              Начальное снаряжение
                            </span>
                            <span className={`text-sm ${totalSpentGold > 180 ? 'text-[#ff4444] font-bold animate-pulse' : 'text-[#D4AF37]'}`}>
                              Потрачено: {totalSpentGold.toFixed(1).replace('.0', '')} / 200 зм
                            </span>
                          </h3>
                          {/* Progress Bar */}
                          <div className="w-full bg-[#111]/60 h-2 rounded-full overflow-hidden border border-[#D4AF37]/20 mb-4">
                            <div
                              className={`h-full transition-all duration-300 ${totalSpentGold > 180 ? 'bg-[#ff4444]' : 'bg-[#D4AF37]'}`}
                              style={{ width: `${Math.min(100, (totalSpentGold / 200) * 100)}%` }}
                            />
                          </div>
                          
                          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-2 custom-scrollbar">
                            {availableEquipment.map(item => {
                              const isSelected = equipment.includes(item.name);
                              return (
                                <div
                                  key={item.key}
                                  onClick={() => {
                                    if (isSelected) {
                                      setEquipment(equipment.filter(name => name !== item.name));
                                    } else {
                                      const itemCost = parseCostToGold(item.cost);
                                      if (totalSpentGold + itemCost > 200) {
                                        alert(`Этот предмет стоит ${item.cost}, что превышает ваш оставшийся бюджет в ${(200 - totalSpentGold).toFixed(1).replace('.0', '')} зм!`);
                                        return;
                                      }
                                      setEquipment([...equipment, item.name]);
                                    }
                                  }}
                                  className={`p-3 rounded-xl border transition-all duration-300 cursor-pointer flex flex-col justify-between ${
                                    isSelected
                                      ? 'border-[#D4AF37] bg-[#D4AF37]/10'
                                      : 'border-[#D4AF37]/20 bg-[#111]/50 hover:border-[#D4AF37]/50 hover:bg-[#D4AF37]/5'
                                  }`}
                                >
                                  <div className="flex justify-between items-center mb-1">
                                    <span className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-base">
                                      {item.name}
                                    </span>
                                    {item.cost && (
                                      <span className="text-[#D4AF37] text-xs font-bold font-['Lora',serif]">
                                        {item.cost}
                                      </span>
                                    )}
                                  </div>
                                  {item.description && (
                                    <span className="font-['Lora',serif] text-[#F4EBD0]/50 text-xs">
                                      {item.description}
                                    </span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </>
                      );
                    })()}
                  </div>

                  {/* Правая колонка - Карточка итогового обзора персонажа */}
                  <div className="lg:col-span-7 border border-[#D4AF37]/30 rounded-3xl p-8 bg-gradient-to-br from-[#221c18] to-[#120e0c] shadow-2xl relative overflow-hidden">
                    {/* Водяной знак дракона или герба на фоне */}
                    <div className="absolute -right-12 -bottom-12 w-64 h-64 opacity-5 pointer-events-none">
                      <Crown className="w-full h-full text-[#D4AF37]" />
                    </div>

                    <h3 className="font-['Cormorant_Garamond',serif] font-bold text-center text-2xl text-[#D4AF37] mb-6 border-b border-[#D4AF37]/30 pb-4">
                      Лист персонажа
                    </h3>

                    {/* Заголовок карточки */}
                    <div className="flex flex-col items-center mb-6">
                      <div className="w-16 h-16 rounded-full bg-[#D4AF37]/10 border border-[#D4AF37]/50 flex items-center justify-center text-[#D4AF37] mb-3 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
                        <User className="w-8 h-8" />
                      </div>
                      <span className="font-['Cormorant_Garamond',serif] font-bold text-2xl text-[#F4EBD0] tracking-wide">
                        {name || 'Безымянный герой'}
                      </span>
                      <span className="font-['Lora',serif] text-[#D4AF37] text-sm mt-1">
                        Уровень 1 • {race?.name} • {characterClass?.name}
                      </span>
                      <span className="font-['Lora',serif] text-[#F4EBD0]/50 text-xs">
                        Предыстория: {background?.name || 'Нет'}
                      </span>
                    </div>

                    {/* Сетка характеристик */}
                    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-6">
                      {abilities && Object.entries(abilities).map(([stat, val]) => {
                        const mod = Math.floor((val - 10) / 2);
                        return (
                          <div key={stat} className="flex flex-col items-center p-2 rounded-xl bg-[#111]/60 border border-[#D4AF37]/20">
                            <span className="text-[10px] text-[#F4EBD0]/50 uppercase font-bold">
                              {abilityNames[stat as keyof AbilityScores]?.slice(0, 3) || stat.slice(0, 3)}
                            </span>
                            <span className="font-['Cormorant_Garamond',serif] font-bold text-[#F4EBD0] text-xl my-0.5">
                              {val}
                            </span>
                            <span className="text-[#D4AF37] text-xs font-bold font-['Lora',serif]">
                              {mod >= 0 ? `+${mod}` : mod}
                            </span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Выбранные опции */}
                    <div className="space-y-4 font-['Lora',serif] text-[#F4EBD0]/80 text-sm">
                      {/* Снаряжение */}
                      <div>
                        <span className="text-[#D4AF37] font-bold block mb-1">Выбранное снаряжение:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {equipment.map(item => (
                            <span key={item} className="px-2.5 py-0.5 bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-xs rounded-full text-[#F4EBD0]/90">
                              {item}
                            </span>
                          ))}
                          {equipment.length === 0 && (
                            <span className="text-xs text-[#F4EBD0]/40 italic">Снаряжение не выбрано</span>
                          )}
                        </div>
                      </div>

                      {/* Заговоры и Заклинания (только для магов) */}
                      {characterClass?.is_spellcaster && (
                        <>
                          <div>
                            <span className="text-[#D4AF37] font-bold block mb-1">Изученные заговоры:</span>
                            <div className="flex flex-wrap gap-1.5">
                              {cantrips.map(spell => (
                                <span key={spell} className="px-2.5 py-0.5 bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-xs rounded-full text-[#F4EBD0]/90">
                                  {spell}
                                </span>
                              ))}
                              {cantrips.length === 0 && (
                                <span className="text-xs text-[#F4EBD0]/40 italic">Заговоры не выбраны</span>
                              )}
                            </div>
                          </div>
                          <div>
                            <span className="text-[#D4AF37] font-bold block mb-1">Изученные заклинания:</span>
                            <div className="flex flex-wrap gap-1.5">
                              {knownSpells.map(spell => (
                                <span key={spell} className="px-2.5 py-0.5 bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-xs rounded-full text-[#F4EBD0]/90">
                                  {spell}
                                </span>
                              ))}
                              {knownSpells.length === 0 && (
                                <span className="text-xs text-[#F4EBD0]/40 italic">Заклинания не выбраны</span>
                              )}
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Buttons — sticky on mobile */}
        <div className="sticky bottom-4 sm:static z-30 sm:z-auto mt-6 sm:mt-8 flex justify-between gap-3 bg-[#1A1A1A]/80 sm:bg-transparent backdrop-blur-sm sm:backdrop-blur-none rounded-xl sm:rounded-none p-3 sm:p-0 shadow-[0_-4px_20px_rgba(0,0,0,0.4)] sm:shadow-none border border-[#D4AF37]/20 sm:border-0">
          <button
            onClick={handlePrev}
            disabled={step === 1}
            className="flex-1 sm:flex-none px-4 sm:px-6 py-3 font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] border-2 border-[#D4AF37] rounded-xl hover:bg-[#D4AF37]/10 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Назад
          </button>

          {step < 7 ? (
            <button
              onClick={handleNext}
              disabled={
                (step === 1 && !name) ||
                (step === 2 && !race) ||
                (step === 3 && !characterClass) ||
                (step === 4 && !background) ||
                (step === 5 && (!abilities || Object.values(abilities).some(v => v === 0)))
              }
              className="flex-1 sm:flex-none px-4 sm:px-6 py-3 font-['Cormorant_Garamond',serif] font-bold text-[#D4AF37] border-2 border-[#D4AF37] rounded-xl hover:bg-[#D4AF37]/10 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Далее
            </button>
          ) : (
            <button
              onClick={handleSave}
              disabled={!abilities || isSubmitting || ((method === 'standard' || method === 'roll') && Object.values(abilities).some(v => v === 0))}
              className="flex-1 sm:flex-none relative group px-4 sm:px-8 py-3 font-['Cormorant_Garamond',serif] font-bold text-base sm:text-lg tracking-wide text-[#D4AF37] border-2 border-[#D4AF37] rounded-xl overflow-hidden transition-all duration-500 hover:shadow-[0_0_30px_rgba(212,175,55,0.5)] disabled:opacity-50"
            >
              <div className="absolute inset-0 bg-[#D4AF37] opacity-0 group-hover:opacity-10 transition-opacity duration-500" />
              <span className="relative flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5" />
                {isSubmitting ? 'Сохранение...' : 'Создать героя'}
              </span>
            </button>
          )}
        </div>
      </div>
      
      {/* Info Modal */}
      <InfoModal 
        isOpen={infoModalOpen} 
        onClose={() => setInfoModalOpen(false)} 
        title={infoModalTitle} 
        description={infoModalDesc} 
      />
    </div>
  );
}
