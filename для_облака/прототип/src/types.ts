// Типы данных прототипа. Названия полей — как в JSON (по-русски), чтобы не было перевода туда-обратно.

export type NicheCode = 'svyaz' | 'pribory';

export interface Badge {
  код: 'svoy' | 'natreg' | 'few' | 'match';
  текст: string;
  почему: string;
}

export interface CustomerHistory {
  закупок_в_выгрузке: number;
  'медиана_снижения_%': number | null;
  медиана_участников: number | null;
  'доля_с_одним_участником_%': number | null;
  без_снижения: number;
  n_со_снижением: number;
}

/** Закупка из выгрузки Тендерплана (лист «Завершенные закупки»), после scripts/prepare_data.py */
export interface Tender {
  id: string;
  предмет: string;
  ниша: NicheCode;
  закон: string;
  способ: string;
  способ_полностью: string;
  статус: string;
  нмц: number | null;
  обеспечение_заявки: number | null;
  обеспечение_контракта: number | null;
  регион: string | null;
  дата_окончания: string;
  'снижение_%': number | null;
  участников: number | null;
  цена_победителя: number | null;
  заказчик: string;
  инн_заказчика: string;
  история_заказчика: CustomerHistory | null;
  бейджи: Badge[];
  риски: string[];
}

// ---- Формат «G → F» (ПОТОКИ.md): результат сверки техзадания с каталогом ----

export type Условие = '>=' | '<=' | '=' | 'диапазон' | 'из_списка' | 'текст' | string;

export interface Характеристика {
  имя: string;
  условие: Условие;
  значение: string;
  единица: string;
  эквивалент_допускается: boolean;
}

export type СтатусСверки = 'подходит' | 'почти' | 'нет';

export interface Расхождение {
  характеристика: string;
  требуется: string;
  у_товара: string;
}

export interface Позиция {
  '№': number;
  наименование: string;
  ктру: string;
  окпд2: string;
  количество: number;
  единица: string;
  характеристики: Характеристика[];
  сверка: {
    статус: СтатусСверки;
    товар_из_каталога: string;
    артикул: string;
    расхождения: Расхождение[];
    /** Одна строка от движка: почему такой статус */
    причина?: string;
    /** Что движок не смог проверить сам — смотреть вручную */
    проверить?: string[];
  };
}

export interface Sverka {
  закупка: {
    номер: string;
    предмет: string;
    заказчик: string;
    инн_заказчика: string;
    закон: string;
    способ: string;
    нмц: number;
    регион: string;
    дата_окончания: string;
    ссылка: string;
    источник_документа: string;
    нацрежим_в_извещении?: boolean | null;
    разобрано?: string;
  };
  позиции: Позиция[];
  итог: { подходит: number; почти: number; нет: number };
  режим: 'демо' | 'живой' | string;
}

/** Формат «H → F»: ожидаемое снижение цены */
export interface PriceRow {
  ниша: string;
  закон: string;
  способ: string;
  участников: string;
  'медиана_снижения_%': number;
  'p25_%': number;
  'p75_%': number;
  n: number;
}

/** Позиция ассортимента поставщика (после разбора прайса) */
export interface CatalogItem {
  артикул: string;
  наименование: string;
  категория: string;
  производитель: string;
  модель: string;
  характеристики: Record<string, string>;
  характеристики_текст: string;
  страна: string;
  цена: number | null;
  остаток: number | null;
  /** Только у демо-каталога движка */
  реестр?: string;
  окпд2?: string;
  источник_url?: string;
  примечание?: string;
}

export interface MarketNiche {
  код: NicheCode;
  название: string;
  период: string | null;
  закупок_за_период: number | null;
  сумма_за_период: string | null;
  'среднее_снижение_%': number | null;
  среднее_участников: number | null;
  'медиана_снижения_%_выгрузка': number | null;
  'доля_с_одним_участником_%_выгрузка': number | null;
  'доля_чистой_поставки_%_выгрузка': number | null;
  медиана_нмц_чистой_поставки: number | null;
  строк_в_выгрузке: number;
}

/** Единая «карточка» для экрана: реальная закупка из выгрузки или закупка с готовой сверкой */
export interface TenderView {
  key: string; // для адреса страницы
  kind: 'выгрузка' | 'сверка';
  предмет: string;
  заказчик: string;
  инн_заказчика: string;
  ниша: NicheCode;
  закон: string;
  способ: string;
  статус: string;
  нмц: number | null;
  обеспечение_заявки: number | null;
  обеспечение_контракта: number | null;
  регион: string;
  дата_окончания: string;
  'снижение_%': number | null;
  участников: number | null;
  цена_победителя: number | null;
  история_заказчика: CustomerHistory | null;
  бейджи: Badge[];
  риски: string[];
  номер?: string;
  sverka?: Sverka;
  ссылка?: string; // страница извещения в ЕИС, если есть в данных
  источник_документа?: string;
  источник: string; // откуда данные — показываем на экране
}
