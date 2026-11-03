export interface Spec { имя: string; условие: string; значение: string; единица: string }
export interface Position {
  '№': number; наименование: string; окпд2: string; ктру?: string; количество: number; единица: string;
  цена_за_ед: number | null; характеристики: Spec[];
}
export interface Tender {
  номер: string; закон: string; способ: string; предмет: string; заказчик: string; инн_заказчика?: string;
  регион_код: number | null; регион: string; нмц: number;
  обеспечение_заявки_проц?: number | null; обеспечение_контракта_проц?: number | null;
  опубликовано?: string; окончание_подачи: string; окпд2: string[]; ктру?: string[];
  ниша: string; тип: string; флаги: string[]; ссылка: string; позиции: Position[] | null;
}
export interface Snapshot { пример?: boolean; снято: string; источник: string; ниши: string[]; тендеры: Tender[] }
export interface Region { код: number; название: string; фо: string }

/** Товар из ассортимента поставщика */
export interface Item {
  id: string;
  name: string;
  brand: string;
  model: string;
  category: string;
  price: number | null;
  specs: Record<string, string>;
  note: string;
}

export type Status = 'подходит' | 'почти' | 'нет';

export interface PosResult {
  no: number;
  name: string;
  qty: number;
  unit: string;
  status: Status;
  item: Item | null;
  /** чем отличается */
  diffs: string[];
  /** что проверить */
  check: string[];
  comment: string;
}

export interface TenderResult {
  number: string;
  mode: 'правила' | 'ИИ';
  noPositions: boolean;
  positions: PosResult[];
  closed: number;
  almost: number;
  total: number;
  aiNote?: string;
}
