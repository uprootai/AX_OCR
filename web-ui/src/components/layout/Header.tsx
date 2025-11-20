import { Link } from 'react-router-dom';
import { Moon, Sun, Menu, Languages } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useUIStore } from '../../store/uiStore';

export default function Header() {
  const { theme, toggleTheme, toggleSidebar } = useUIStore();
  const { t, i18n } = useTranslation();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ko' ? 'en' : 'ko';
    i18n.changeLanguage(newLang);
  };

  return (
    <header className="border-b bg-card">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-accent rounded-md"
          >
            <Menu className="h-5 w-5" />
          </button>
          <Link to="/dashboard" className="text-xl font-bold">
            {t('header.title')}
          </Link>
        </div>

        <nav className="flex items-center gap-2">
          <button
            onClick={toggleLanguage}
            className="p-2 hover:bg-accent rounded-md"
            title={i18n.language === 'ko' ? '한국어' : 'English'}
          >
            <Languages className="h-5 w-5" />
          </button>

          <button
            onClick={toggleTheme}
            className="p-2 hover:bg-accent rounded-md"
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </button>
        </nav>
      </div>
    </header>
  );
}
