import React, { useEffect, useState } from 'react';
import { api } from '../../../api/client';
import { ReferenceItem } from '../../../types/api';
import { useCharacterStore } from '../../../store/characterStore';

interface Props {
  onNext: () => void;
}

export const Step1RaceSelection: React.FC<Props> = ({ onNext }) => {
  const [races, setRaces] = useState<ReferenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const { race: selectedRace, setRace } = useCharacterStore();

  useEffect(() => {
    const fetchRaces = async () => {
      try {
        const data = await api.reference.getRaces();
        setRaces(data.items);
      } catch (error) {
        console.error('Failed to fetch races:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchRaces();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-64 text-slate-400">Загрузка рас...</div>;
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <h2 className="text-2xl font-semibold mb-6 text-slate-200">Выберите расу</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {races.map((race) => (
          <div
            key={race.key || race.name}
            onClick={() => setRace(race)}
            className={`p-4 rounded-lg cursor-pointer border-2 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 ${
              selectedRace?.name === race.name
                ? 'border-orange-500 bg-orange-500/10'
                : 'border-slate-600 bg-slate-700/50 hover:border-slate-500'
            }`}
          >
            <h3 className="text-xl font-bold text-amber-500 mb-2">{race.name}</h3>
            <p className="text-slate-300 text-sm line-clamp-3">{race.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 flex justify-end">
        <button
          onClick={onNext}
          disabled={!selectedRace}
          className="px-6 py-2 bg-orange-600 hover:bg-orange-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-colors"
        >
          Далее
        </button>
      </div>
    </div>
  );
};
