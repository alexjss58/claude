// «Сроки и деньги»: от подачи заявки до оплаты. Сроки — ориентиры, их нужно сверять
// с извещением и проектом контракта. Не юридическая консультация.
// Праздники в прототипе не учитываются, только выходные (суббота и воскресенье).

export function addWorkDays(d: Date, n: number): Date {
  const r = new Date(d);
  let left = n;
  while (left > 0) {
    r.setDate(r.getDate() + 1);
    const wd = r.getDay();
    if (wd !== 0 && wd !== 6) left--;
  }
  return r;
}

export function addDays(d: Date, n: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

export function daysBetween(a: Date, b: Date): number {
  return Math.round((b.getTime() - a.getTime()) / 86400000);
}

export interface TimelineInput {
  start: Date; // окончание подачи заявок
  law: string;
  method: string;
  deliveryDays: number; // срок поставки по контракту, календарные дни
  acceptanceWorkDays: number; // приёмка, рабочие дни
  paymentWorkDays: number; // оплата после приёмки, рабочие дни
  price: number; // цена контракта (наша цена)
  cost: number; // себестоимость товара
  bidSecurity: number; // обеспечение заявки, ₽
  contractSecurity: number; // обеспечение контракта, ₽
  guaranteeRate: number; // стоимость банковской гарантии, % годовых (пример)
  useGuarantee: boolean;
}

export interface Step {
  key: string;
  title: string;
  date: Date;
  note: string;
  money?: { amount: number; dir: 'out' | 'in' | 'hold' | 'release'; label: string };
}

export function buildTimeline(i: TimelineInput): { steps: Step[]; gap: number; gapDays: number; profit: number; guaranteeCost: number } {
  const is44 = i.law.includes('44');
  const quick = /котиров|цен/i.test(i.method);
  const resultsWd = quick ? 1 : 2;
  const results = addWorkDays(i.start, resultsWd);
  // 44-ФЗ: контракт заключают не ранее чем через 10 дней после протокола (для котировок — 5); берём ориентир.
  const signDelay = is44 ? (quick ? 5 : 10) : 10;
  const sign = addWorkDays(addDays(results, signDelay), 1);
  const delivery = addDays(sign, i.deliveryDays);
  const acceptance = addWorkDays(delivery, i.acceptanceWorkDays);
  const payment = addWorkDays(acceptance, i.paymentWorkDays);
  const guaranteeDays = Math.max(30, daysBetween(sign, payment) + 30); // гарантия должна покрывать срок контракта + запас
  const guaranteeCost = i.useGuarantee ? (i.contractSecurity * i.guaranteeRate / 100) * (guaranteeDays / 365) : 0;

  const steps: Step[] = [
    {
      key: 'submit', title: 'Подача заявки', date: i.start,
      note: 'Последний день подачи по извещению. Заявку подписывает электронная подпись руководителя или сотрудника по доверенности.',
      money: i.bidSecurity > 0 ? { amount: i.bidSecurity, dir: 'hold', label: 'обеспечение заявки блокируется на спецсчёте' } : undefined,
    },
    {
      key: 'results', title: 'Итоги', date: results,
      note: `Протокол подведения итогов — ориентир ${resultsWd} раб. ${resultsWd === 1 ? 'день' : 'дня'} после окончания подачи (${quick ? 'котировки, запрос цен' : 'аукцион, конкурс'}).`,
      money: i.bidSecurity > 0 ? { amount: i.bidSecurity, dir: 'release', label: 'обеспечение заявки разблокируют (если не победили) или зачтут' } : undefined,
    },
    {
      key: 'sign', title: 'Подписание контракта', date: sign,
      note: is44
        ? `По 44-ФЗ контракт заключают не ранее чем через ${signDelay} дней после протокола — ориентир, проверить по способу закупки.`
        : 'По 223-ФЗ сроки — в положении о закупке заказчика и документации. Ориентир: около 10 дней.',
    },
    {
      key: 'security', title: i.useGuarantee ? 'Банковская гарантия' : 'Обеспечение контракта', date: sign,
      note: i.useGuarantee
        ? 'Гарантию оформляют до подписания. Стоимость считается от суммы обеспечения и срока — ставка здесь условная, уточните в банке.'
        : 'Обеспечение деньгами: сумму переводят заказчику до подписания и получают обратно после исполнения контракта.',
      money: i.contractSecurity > 0
        ? (i.useGuarantee
          ? { amount: guaranteeCost, dir: 'out', label: `комиссия за гарантию на ${i.contractSecurity.toLocaleString('ru-RU')} ₽` }
          : { amount: i.contractSecurity, dir: 'hold', label: 'деньги у заказчика до конца контракта' })
        : undefined,
    },
    {
      key: 'delivery', title: 'Поставка', date: delivery,
      note: `Срок поставки по контракту: ${i.deliveryDays} календ. дней (введите свой). Товар закупаете до поставки.`,
      money: { amount: i.cost, dir: 'out', label: 'закупка товара у дистрибьютора' },
    },
    {
      key: 'acceptance', title: 'Приёмка', date: acceptance,
      note: `Заказчик принимает товар и подписывает документ о приёмке (в 44-ФЗ — электронный, через ЕИС). Здесь ${i.acceptanceWorkDays} раб. дней — проверьте срок в контракте.`,
    },
    {
      key: 'payment', title: 'Оплата', date: payment,
      note: is44
        ? `По 44-ФЗ срок оплаты — не более 7 рабочих дней после подписания документа о приёмке, если контракт не даёт меньше. Здесь: ${i.paymentWorkDays}.`
        : `По 223-ФЗ для закупок у малого бизнеса — обычно не более 7 рабочих дней; общий срок — в договоре. Здесь: ${i.paymentWorkDays}.`,
      money: { amount: i.price, dir: 'in', label: 'оплата по контракту' + (i.contractSecurity > 0 && !i.useGuarantee ? ' + возврат обеспечения позже' : '') },
    },
  ];
  const outBeforePay = i.cost + (i.useGuarantee ? guaranteeCost : i.contractSecurity);
  const gapDays = daysBetween(delivery, payment);
  const profit = i.price - i.cost - guaranteeCost;
  return { steps, gap: outBeforePay, gapDays, profit, guaranteeCost };
}
