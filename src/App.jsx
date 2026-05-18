import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';
import MainContent from './components/MainContent.jsx';

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar activeItem="Dashboard" />
      <div className="flex flex-col flex-1 overflow-y-auto">
        <Header />
        <MainContent />
      </div>
    </div>
  );
}
