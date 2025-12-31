import { useTranslation } from 'react-i18next';
import { Menu, X, ChevronRight } from 'lucide-react';
import {
  useGuideScroll,
  sections,
  OverviewSection,
  ArchitectureSection,
  PipelineSection,
  ServicesSection,
  QuickstartSection,
  APIDevSection,
  SpecRefSection,
  TestingSection,
  DocsSection,
  BlueprintFlowSection,
} from './guide';

export default function Guide() {
  const { t } = useTranslation();
  const {
    activeSection,
    sidebarOpen,
    sectionRefs,
    scrollToSection,
    setSidebarOpen,
  } = useGuideScroll();

  return (
    <div className="flex min-h-screen">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-20 left-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700"
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Sub-sidebar */}
      <aside className={`
        fixed lg:sticky top-16 left-0 h-[calc(100vh-4rem)] w-64
        bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700
        transform transition-transform duration-300 ease-in-out z-40
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        overflow-y-auto
      `}>
        <div className="p-4">
          <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
            Table of Contents
          </h2>
          <nav className="space-y-1">
            {sections.map((section) => {
              const Icon = section.icon;
              const isActive = activeSection === section.id;
              return (
                <button
                  key={section.id}
                  onClick={() => scrollToSection(section.id)}
                  className={`
                    w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors
                    ${isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }
                  `}
                >
                  <Icon className={`w-4 h-4 mr-3 ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`} />
                  <span className="truncate">{section.label}</span>
                  {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
                </button>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Overlay (mobile) */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 lg:ml-0 min-w-0">
        <div className="container mx-auto px-4 py-8 max-w-5xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
              {t('guide.title')}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {t('guide.subtitle')}
            </p>
          </div>

          {/* Section 1: Project Overview */}
          <OverviewSection
            sectionRef={(el) => { sectionRefs.current['overview'] = el; }}
          />

          {/* Section 2: System Architecture */}
          <ArchitectureSection
            sectionRef={(el) => { sectionRefs.current['architecture'] = el; }}
          />

          {/* Section 3: BlueprintFlow Pipeline */}
          <PipelineSection
            sectionRef={(el) => { sectionRefs.current['pipeline'] = el; }}
          />

          {/* Section 4: Service Roles */}
          <ServicesSection
            sectionRef={(el) => { sectionRefs.current['services'] = el; }}
          />

          {/* Section 5: Quick Start */}
          <QuickstartSection
            sectionRef={(el) => { sectionRefs.current['quickstart'] = el; }}
          />

          {/* Section 6: API Development Guide */}
          <APIDevSection
            sectionRef={(el) => { sectionRefs.current['apidev'] = el; }}
          />

          {/* Section 7: Spec Reference */}
          <SpecRefSection
            sectionRef={(el) => { sectionRefs.current['specref'] = el; }}
          />

          {/* Section 8: Testing Guide */}
          <TestingSection
            sectionRef={(el) => { sectionRefs.current['testing'] = el; }}
          />

          {/* Section 9: Documentation */}
          <DocsSection
            sectionRef={(el) => { sectionRefs.current['docs'] = el; }}
          />

          {/* Section 10: BlueprintFlow Detail */}
          <BlueprintFlowSection
            sectionRef={(el) => { sectionRefs.current['blueprintflow'] = el; }}
          />

        </div>
      </main>
    </div>
  );
}
