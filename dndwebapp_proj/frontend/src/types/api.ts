export interface AbilityScores {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface CharacterCreationRequest {
  user_id: number;
  name: string;
  race_name: string;
  class_id: string;
  background_id?: string;
  abilities: AbilityScores;
  cantrips?: string[];
  known_spells?: string[];
  equipment?: string[];
}

export interface ReferenceItem {
  id?: string;
  key?: string;
  name: string;
  description: string;
  is_spellcaster?: boolean;
}

export interface ReferenceListResponse {
  total: number;
  items: ReferenceItem[];
}
