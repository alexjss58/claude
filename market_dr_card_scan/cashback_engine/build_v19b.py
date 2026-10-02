"""v19.1 (01.10.2026): processing -> card technology (row 60); separate paid-card shares for the Bank PnL bridge (rows 116-123)."""
import sys
from xmlbook import N, S, X, Book
IN, OUT = sys.argv[1:3]
book = Book(IN)
P = book.parts
p = book.sheet('Bank PnL')
CP = "'Cards PnL all tiers'"
T4 = "'4 tiers model (to be lineup)'"
OFF = [0, 77, 154, 231]
TIERS = ['Free', 'Black', 'Premium', 'Elite']
VS, PCT_IN, PCT = p.style('AX97'), '811', p.style('AH6') or '1118'


def clear(ref):
    c = p.get(ref)
    if c is not None:
        for ch in list(c):
            c.remove(ch)
        for a in ('t', 'cm', 'vm'):
            c.attrib.pop(a, None)


# processing -> card technology
for c in ('AX37', 'AY37', 'BC37', 'BD37', 'BE37', 'BF37', 'BC36', 'BD36', 'BE36'):
    clear(c)
for col in ('AX', 'AY'):
    p.f(f'{col}60', f'-{col}106-{col}101-{col}100', p.style(f'{col}60'))
p.t('BF60', 'Card processing (ArCa, Visa / Mastercard) + card production for new cards + card database', '1060')

# paid-card shares for the Bank PnL only
p.t('C116', "SHARE OF PAID CARDS FOR THE BANK P&L – inputs, this sheet only (default = cards model; the cards model keeps its own on the Control panel)",
    p.style('C96'))
for col, h in (('AX', '2027'), ('AY', '2028'), ('AZ', 'Model 2027'), ('BA', 'Model 2028')):
    p.t(f'{col}116', h, p.style('AX96'))
for k, (tier, o) in enumerate(zip(TIERS, OFF)):
    r = 117 + k
    p.t(f'C{r}', f'   {tier}', '1060')
    p.f(f'AX{r}', f'{T4}!I{15 + o}', PCT_IN)
    p.f(f'AY{r}', f'{T4}!J{15 + o}', PCT_IN)
    p.f(f'AZ{r}', f'{T4}!I{15 + o}', PCT)
    p.f(f'BA{r}', f'{T4}!J{15 + o}', PCT)
p.t('BF117', 'Overwrite AX:AY with your rates; they change only the service-fee line (row 27) of this sheet', '1060')
p.t('C121', 'Service fees at these shares (row 27)', '1060')
p.t('C122', '   service fees in the cards model', '1060')
p.t('C123', '   difference vs the cards model', '1060')
for col, pc, yc in (('AX', 'E', 'I'), ('AY', 'F', 'J')):
    terms = '+'.join(f"{CP}!{pc}{24 + k}*{T4}!{yc}{14 + o}*12*{col}{117 + k}" for k, o in enumerate(OFF))
    p.f(f'{col}121', f'({terms})/1000', VS)
    p.f(f'{col}122', f'{CP}!{pc}44*1000', VS)
    p.f(f'{col}123', f'{col}121-{col}122', VS)
    p.f(f'{col}27', f'{col}121', p.style(f'{col}27'))
    p.f(f'{col}114', f'{col}113-{col}112-{col}102-{col}123', p.style(f'{col}114'))
p.t('C114', '   check: bank structure − cards model − allocated fixed OPEX − service-fee difference (should be 0)', '1060')
p.t('BF27', 'Service fees at the paid-card shares in rows 117–120 (default = cards model)', '1060')
p.root.find(N + 'dimension').set('ref', 'B2:BF123')
p.save()
wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT)
