# Техническое задание (ТЗ) на интеграцию Фронтенда с Backend API

Данный документ описывает архитектуру, правила взаимодействия и контракты между фронтендом (React/Vite) и новым бекендом (FastAPI). Бекенд был полностью отрефакторен: он больше не хранит промежуточные состояния (Stateless) и общается исключительно через REST API JSON-контракты.

---

## 1. Настройка Vite (Proxy & CORS)
Поскольку фронтенд и бекенд работают на разных портах (например, `5173` и `8000`), возможны ошибки CORS. 
В `vite.config.ts` необходимо настроить проксирование:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Адрес вашего FastAPI
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
```
*Совет: Создайте файл `src/api/client.ts` и используйте `axios` с `baseURL: '/api/v1'`.*

---

## 2. Управление состоянием (State Management)
**КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ:** Бекенд больше не запоминает, на каком шаге создания персонажа находится пользователь. 

Фронтенд **обязан** реализовать "Wizard" (многошаговую форму) и хранить состояние самостоятельно (с помощью `Zustand`, `Redux` или `React Context`).

**Примерный флоу создания персонажа на фронтенде:**
1. Шаг 1: `GET /api/v1/reference/races` -> Пользователь выбирает расу. Фронтенд сохраняет `race_name` в стейт.
2. Шаг 2: `GET /api/v1/reference/classes` -> Пользователь выбирает класс. Фронтенд сохраняет `class_id` в стейт.
3. Шаг 3: `GET /api/v1/characters/tools/roll-abilities` -> Пользователь получает кубики. Фронтенд сохраняет объект `abilities`.
4. Шаг 4 (Финал): Фронтенд собирает все данные из стейта и отправляет **один** `POST /api/v1/characters/create`.

---

## 3. Контракты API (Endpoints)

### 3.1 Справочники (Reference)
Все GET-запросы к справочникам возвращают стандартизированный ответ вида `{"total": int, "items": [...]}` или конкретный объект.

* `GET /api/v1/reference/races` — получить список рас.
* `GET /api/v1/reference/races/{name}` — получить детальное описание конкретной расы.
* `GET /api/v1/reference/classes` — получить список классов.
* `GET /api/v1/reference/classes/{class_id}` — получить детали класса.

### 3.2 Персонажи (Characters)
* `GET /api/v1/characters/{user_id}` — получить список всех созданных персонажей пользователя (для экрана "Мои персонажи").
* `GET /api/v1/characters/{user_id}/{char_id}` — получить весь лист персонажа.
* `DELETE /api/v1/characters/{user_id}/{char_id}` — удалить персонажа.

**Создание персонажа:**
* `POST /api/v1/characters/create`
**Тело запроса (Body):**
```json
{
  "user_id": 12345,
  "name": "Гендальф",
  "race_name": "Эльф",
  "class_id": "wizard",
  "background_id": "sage",
  "abilities": {
    "strength": 8, "dexterity": 14, "constitution": 12, 
    "intelligence": 15, "wisdom": 13, "charisma": 10
  }
}
```
*Бекенд сам посчитает модификаторы, добавит расовые бонусы к статам, вычислит HP и вернет готовый объект персонажа.*

### 3.3 ИИ Ассистент (RAG Orchestrator)
ИИ работает через контекстный поиск (RAG).
* `POST /api/v1/ai/ask`
**Тело запроса:**
```json
{
  "question": "Как работает скрытная атака?",
  "section_name": "combat", 
  "section_content": "Опционально: текст страницы, на которой сейчас находится юзер"
}
```
**Ответ:** `{"answer": "Скрытная атака работает так..."}` (Ответ может содержать базовые HTML теги `<b>`, `<i>`, `<br>`, которые фронтенд должен отрендерить через `dangerouslySetInnerHTML`).

---

## 4. Рекомендуемые TypeScript Интерфейсы

Для удобства фронтендера, вот основные типы, которые стоит добавить в `src/types/api.ts`:

```typescript
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
}

export interface ReferenceItem {
  id?: string;
  key?: string;
  name: string;
  description: string;
}

export interface ReferenceListResponse {
  total: number;
  items: ReferenceItem[];
}
```

---
## 5. Ближайшие шаги для разработчика
1. Инициализировать React (если еще не сделано).
2. Установить `axios` и `zustand` (или аналог для стейта).
3. Создать API-клиент и перенести туда все маршруты из пункта 3.
4. Начать верстку экрана "Выбор расы", получая данные с бекенда.
