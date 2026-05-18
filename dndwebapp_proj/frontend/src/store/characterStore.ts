import { create } from 'zustand';
import { AbilityScores, ReferenceItem } from '../types/api';

interface CharacterState {
  // Выбранные данные
  name: string;
  race: ReferenceItem | null;
  characterClass: ReferenceItem | null;
  background: ReferenceItem | null;
  abilities: AbilityScores | null;
  cantrips: string[];
  knownSpells: string[];
  equipment: string[];

  // Экшены для изменения состояния
  setName: (name: string) => void;
  setRace: (race: ReferenceItem) => void;
  setClass: (characterClass: ReferenceItem) => void;
  setBackground: (bg: ReferenceItem) => void;
  setAbilities: (abilities: AbilityScores) => void;
  setCantrips: (cantrips: string[]) => void;
  setKnownSpells: (spells: string[]) => void;
  setEquipment: (equipment: string[]) => void;
  reset: () => void;
}

export const useCharacterStore = create<CharacterState>((set) => ({
  name: '',
  race: null,
  characterClass: null,
  background: null,
  abilities: null,
  cantrips: [],
  knownSpells: [],
  equipment: [],

  setName: (name) => set({ name }),
  setRace: (race) => set({ race }),
  setClass: (characterClass) => set({ characterClass }),
  setBackground: (bg) => set({ background: bg }),
  setAbilities: (abilities) => set({ abilities }),
  setCantrips: (cantrips) => set({ cantrips }),
  setKnownSpells: (knownSpells) => set({ knownSpells }),
  setEquipment: (equipment) => set({ equipment }),
  reset: () => set({ 
    name: '', race: null, characterClass: null, background: null, 
    abilities: null, cantrips: [], knownSpells: [], equipment: [] 
  }),
}));
