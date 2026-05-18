import React, { useEffect, useState } from 'react';
import { api } from '../../../api/client';
import { ReferenceItem } from '../../../types/api';
import { useCharacterStore } from '../../../store/characterStore';

interface Props {
  onNext: () => void;
  onPrev: () => void;
}

export const Step2ClassSelection: React.FC<Props> = ({ onNext, onPrev }) => {
  const [classes, setClasses] = useState<ReferenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const { characterClass: selectedClass, setClass } = useCharacterStore();

  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const data = await api.reference.getClasses();
        setClasses(data.items);
      } catch (error) {
        console.error('Failed to fetch classes:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchClasses();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-64 text-slate-400">Загрузка классов...</div>;
  }

  return (
    <div className="animate-in fade-in slide-in-from-right-4 duration-500">
      <h2 className="text-2xl font-semibold mb-6 text-slate-200">Выберите класс</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {classes.map((cls) => (
          <div
            key={cls.key || cls.name}
            onClick={() => setClass(cls)}
            className={`p-4 rounded-lg cursor-pointer border-2 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 ${
              selectedClass?.name === cls.name
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-slate-600 bg-slate-700/50 hover:border-slate-500'
            }`}
          >
            <h3 className="text-xl font-bold text-indigo-400 mb-2">{cls.name}</h3>
            <p className="text-slate-300 text-sm line-clamp-3">{cls.description}</p>
          </div>
        ))}
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
          disabled={!selectedClass}
          className="px-6 py-2 bg-orange-600 hover:bg-orange-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-colors"
        >
          Далее
        </button>
      </div>
    </div>
  );
};
