import React, { useState } from 'react';
import { Step1RaceSelection } from './Step1RaceSelection';
import { Step2ClassSelection } from './Step2ClassSelection';
import { Step3Abilities } from './Step3Abilities';
import { Step4Summary } from './Step4Summary';

export const CharacterCreationWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);

  const nextStep = () => setCurrentStep((prev) => Math.min(prev + 1, 4));
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 1));

  return (
    <div className="max-w-4xl mx-auto p-6 bg-slate-900 min-h-screen text-slate-100 font-sans">
      <div className="mb-8 border-b border-slate-700 pb-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
          Создание Персонажа
        </h1>
        <div className="flex gap-2 mt-4">
          {[1, 2, 3, 4].map((step) => (
            <div
              key={step}
              className={`h-2 flex-1 rounded-full transition-colors duration-300 ${
                step <= currentStep ? 'bg-orange-500' : 'bg-slate-700'
              }`}
            />
          ))}
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6 shadow-2xl border border-slate-700 min-h-[400px]">
        {currentStep === 1 && <Step1RaceSelection onNext={nextStep} />}
        {currentStep === 2 && <Step2ClassSelection onNext={nextStep} onPrev={prevStep} />}
        {currentStep === 3 && <Step3Abilities onNext={nextStep} onPrev={prevStep} />}
        {currentStep === 4 && <Step4Summary onPrev={prevStep} />}
      </div>
    </div>
  );
};
