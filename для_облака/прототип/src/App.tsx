import Landing from './pages/Landing';
import CabinetLayout from './pages/cabinet/Layout';
import Assortment from './pages/cabinet/Assortment';
import Tenders from './pages/cabinet/Tenders';
import TenderCard from './pages/cabinet/TenderCard';
import Draft from './pages/cabinet/Draft';
import Timeline from './pages/cabinet/Timeline';
import { ArticleList, ArticlePage, FaqPage } from './pages/Articles';
import { useRoute } from './router';

export default function App() {
  const { parts } = useRoute();
  if (parts[0] === 'stati') return parts[1] ? <ArticlePage key={parts[1]} slug={parts[1]} /> : <ArticleList />;
  if (parts[0] === 'voprosy') return <FaqPage />;
  if (parts[0] !== 'demo') return <Landing />; // «#/» — лендинг, «#/pilot» — лендинг, прокрученный к форме пилота
  const [, section = 'assortiment', id] = parts;
  switch (section) {
    case 'tendery':
      return <CabinetLayout section="tendery"><Tenders /></CabinetLayout>;
    case 'tender':
      return <CabinetLayout section="tender" tenderId={id}><TenderCard key={id} id={id} /></CabinetLayout>;
    case 'zayavka':
      return <CabinetLayout section="zayavka" tenderId={id}><Draft key={id} id={id} /></CabinetLayout>;
    case 'sroki':
      return <CabinetLayout section="sroki" tenderId={id}><Timeline key={id} id={id} /></CabinetLayout>;
    default:
      return <CabinetLayout section="assortiment"><Assortment /></CabinetLayout>;
  }
}
