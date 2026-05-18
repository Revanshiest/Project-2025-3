import React, { useState } from 'react';
import { api } from '../../../api/client';
import { useCharacterStore } from '../../../store/characterStore';
import { AbilityScores, CharacterCreationRequest } from '../../../types/api';

interface Props {
  onPrev: () => void;
}

const abilityNames: Record<keyof AbilityScores, string> = {
  strength: 'СИЛ',
  dexterity: 'ЛОВ',
  constitution: 'ТЕЛ',
  intelligence: 'ИНТ',
  wisdom: 'МУД',
  charisma: 'ХАР'
};

export const Step4Summary: React.FC<Props> = ({ onPrev }) => {
  const { name, race, characterClass, abilities, setName, reset } = useCharacterStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    if (!name || !race || !characterClass || !abilities) return;

    setIsSubmitting(true);
    try {
      const requestData: CharacterCreationRequest = {
        user_id: 1, // Заглушка, в будущем можно брать из контекста авторизации
        name: name,
        race_name: race.name,
        class_id: characterClass.key || characterClass.name,
        abilities: abilities,
      };

      await api.characters.createCharacter(requestData);
      setSuccess(true);
      // Сбросить форму можно, но пока покажем сообщение об успехе
    } catch (error) {
      console.error('Failed to create character:', error);
      alert('Ошибка при сохранении персонажа!');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="flex flex-col items-center justify-center py-16 animate-in fade-in zoom-in duration-500 text-center">
        <div className="w-20 h-20 bg-emerald-500 rounded-full flex items-center justify-center mb-6 shadow-lg shadow-emerald-500/50">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-3xl font-bold text-white mb-2">Персонаж создан!</h2>
        <p className="text-slate-400 mb-8">Вы успешно создали нового героя.</p>
        <button
          onClick={() => {
            reset();
            window.location.reload(); // Простой способ вернуться в начало
          }}
          className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition-colors"
        >
          Создать еще одного
        </button>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in slide-in-from-right-4 duration-500">
      <h2 className="text-2xl font-semibold mb-6 text-slate-200">Подтверждение</h2>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-2">
            Имя персонажа
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Введите имя..."
            className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
          />
        </div>

        <div className="bg-slate-700/30 rounded-xl p-6 border border-slate-600/50">
          <h3 className="text-lg font-semibold text-white mb-4">Сводка</h3>
          
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <span className="text-slate-400 text-sm block">Раса</span>
              <span className="text-orange-400 font-semibold text-lg">{race?.name}</span>
            </div>
            <div>
              <span className="text-slate-400 text-sm block">Класс</span>
              <span className="text-indigo-400 font-semibold text-lg">{characterClass?.name}</span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-600/50">
            <span className="text-slate-400 text-sm block mb-3">Характеристики</span>
            <div className="flex flex-wrap gap-3">
              {abilities && (Object.entries(abilities) as [keyof AbilityScores, number][]).map(([key, val]) => (
                <div key={key} className="bg-slate-800 px-3 py-1.5 rounded-md flex items-center gap-2 border border-slate-600">
                  <span className="text-slate-500 text-xs font-bold">{abilityNames[key]}</span>
                  <span className="text-white font-mono">{val}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 flex justify-between">
        <button
          onClick={onPrev}
          className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition-colors"
        >
          Назад
        </button>
        <button
          onClick={handleSubmit}
          disabled={!name || name.trim() === '' || isSubmitting}
          className="px-8 py-2 bg-orange-600 hover:bg-orange-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-bold shadow-lg transition-all"
        >
          {isSubmitting ? 'Сохранение...' : 'Создать персонажа'}
        </button>
      </div>
    </div>
  );
};
