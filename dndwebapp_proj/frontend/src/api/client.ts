import axios from 'axios';
import { ReferenceListResponse, ReferenceItem, AbilityScores, CharacterCreationRequest } from '../types/api';

// Создаем инстанс axios с базовым URL, который будет перехвачен прокси Vite
export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Функции для работы со справочниками
export const api = {
  reference: {
    getRaces: async (): Promise<{items: ReferenceItem[]}> => {
      const response = await apiClient.get<{items: ReferenceItem[]}>('/reference/races');
      return response.data;
    },
    getClasses: async (): Promise<{items: ReferenceItem[]}> => {
      const response = await apiClient.get<{items: ReferenceItem[]}>('/reference/classes');
      return response.data;
    },
    getBackgrounds: async (): Promise<{items: ReferenceItem[]}> => {
      const response = await apiClient.get<{items: ReferenceItem[]}>('/reference/backgrounds');
      return response.data;
    },
    getSpells: async (level: string): Promise<{items: any}> => {
      const response = await apiClient.get(`/reference/spells/${level}`);
      return response.data;
    },
    getItems: async (): Promise<any> => {
      const response = await apiClient.get('/reference/items');
      return response.data;
    }
  },
  characters: {
    getUserCharacters: async (userId: number): Promise<any[]> => {
      const response = await apiClient.get<any[]>(`/characters/${userId}`);
      return response.data;
    },
    addExperience: async (userId: number, charId: string, xp: number): Promise<any> => {
      const response = await apiClient.post(`/characters/${userId}/${charId}/add-xp`, { xp });
      return response.data;
    },
    rollAbilities: async (): Promise<number[]> => {
      const response = await apiClient.get<{rolls: number[]}>('/characters/tools/roll-abilities');
      return response.data.rolls;
    },
    getStandardArray: async (): Promise<number[]> => {
      const response = await apiClient.get<{array: number[]}>('/characters/tools/standard-array');
      return response.data.array;
    },
    createCharacter: async (data: CharacterCreationRequest): Promise<any> => {
      const response = await apiClient.post('/characters/create', data);
      return response.data;
    }
  },
  ai: {
    ask: async (question: string, section_name: string = 'general', userId: number = 1, chatId?: string): Promise<{ answer: string, chat_id: string, title: string }> => {
      const response = await apiClient.post('/ai/ask', {
        question,
        section_name,
        user_id: userId,
        chat_id: chatId
      });
      return response.data;
    },
    getChats: async (userId: number): Promise<any[]> => {
      const response = await apiClient.get<any[]>(`/ai/chats/${userId}`);
      return response.data;
    },
    getChatSession: async (userId: number, chatId: string): Promise<any> => {
      const response = await apiClient.get<any>(`/ai/chats/${userId}/${chatId}`);
      return response.data;
    }
  }
};
