import React, { useState } from 'react';
import { api } from '../../../api/client';
import { useCharacterStore } from '../../../store/characterStore';
import { AbilityScores } from '../../../types/api';

interface Props {
  onNext: () => void;
  onPrev: () => void;
}

const abilityNames: Record<keyof AbilityScores, string> = {
  strength: 'Сила',
  dexterity: 'Ловкость',
  constitution: 'Телосложение',
  intelligence: 'Интеллект',
  wisdom: 'Мудрость',
  charisma: 'Харизма'
};

export const Step3Abilities: React.FC<Props> = ({ onNext, onPrev }) => {
  const { abilities, setAbilities } = useCharacterStore();
  const [isRolling, setIsRolling] = useState(false);

  const handleRoll = async () => {
    setIsRolling(true);
    try {
      const result = await api.characters.rollAbilities();
      setAbilities(result);
    } catch (error) {
      console.error('Failed to roll abilities:', error);
      // Fallback на случай, если эндпоинт броска кубиков еще не готов
      setAbilities({
        strength: Math.floor(Math.random() * 10) + 8,
        dexterity: Math.floor(Math.random() * 10) + 8,
        constitution: Math.floor(Math.random() * 10) + 8,
        intelligence: Math.floor(Math.random() * 10) + 8,
        wisdom: Math.floor(Math.random() * 10) + 8,
        charisma: Math.floor(Math.random() * 10) + 8,
      });
    } finally {
      setIsRolling(false);
    }
  };

  return (
    <div className="animate-in fade-in slide-in-from-right-4 duration-500">
      <h2 className="text-2xl font-semibold mb-6 text-slate-200">Бросок Характеристик</h2>
      
      <div className="flex flex-col items-center justify-center py-8">
        {!abilities && (
          <p className="text-slate-400 mb-6 text-center">
            Нажмите кнопку ниже, чтобы сгенерировать базовые характеристики вашего персонажа (4d6 drop lowest).
          </p>
        )}

        <button
          onClick={handleRoll}
          disabled={isRolling}
          className={`px-8 py-4 rounded-xl font-bold text-lg shadow-lg transition-all duration-300 ${
            isRolling 
              ? 'bg-emerald-700 text-emerald-200 cursor-not-allowed scale-95'
              : 'bg-emerald-600 hover:bg-emerald-500 hover:-translate-y-1 hover:shadow-emerald-500/50 text-white'
          }`}
        >
          {isRolling ? 'Бросаем кубики...' : abilities ? 'Перебросить кубики' : 'Бросить кубики!'}
        </button>

        {abilities && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6 w-full mt-12 animate-in fade-in zoom-in-95 duration-500">
            {(Object.entries(abilities) as [keyof AbilityScores, number][]).map(([key, value]) => (
              <div key={key} className="bg-slate-700/50 rounded-lg p-6 flex flex-col items-center border border-slate-600 shadow-inner">
                <span className="text-slate-400 text-sm uppercase tracking-wider mb-2 font-semibold">
                  {abilityNames[key]}
                </span>
                <span className="text-4xl font-bold text-emerald-400 font-mono">
                  {value}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8 flex justify-between">
        <button
          onClick={onPrev}
          className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition-colors"
        >
          Назад
        </button>
        <button
          onClick={onNext}
          disabled={!abilities || isRolling}
          className="px-6 py-2 bg-orange-600 hover:bg-orange-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-colors"
        >
          Далее
        </button>
      </div>
    </div>
  );
};
