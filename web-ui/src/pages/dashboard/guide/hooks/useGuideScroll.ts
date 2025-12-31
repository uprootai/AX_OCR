import { useState, useEffect, useRef, useCallback } from 'react';
import {
  BookOpen, Layers, Code, Server,
  Rocket, FileText, FolderOpen,
  Wrench, TestTube2, Terminal
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface GuideSection {
  id: string;
  label: string;
  icon: LucideIcon;
}

// Section definitions
export const sections: GuideSection[] = [
  { id: 'overview', label: 'Project Overview', icon: BookOpen },
  { id: 'architecture', label: 'System Architecture', icon: Layers },
  { id: 'pipeline', label: 'BlueprintFlow Pipeline', icon: Code },
  { id: 'services', label: 'Service Roles', icon: Server },
  { id: 'quickstart', label: 'Quick Start', icon: Rocket },
  { id: 'apidev', label: 'API Dev Guide', icon: Wrench },
  { id: 'specref', label: 'Spec Reference', icon: Terminal },
  { id: 'testing', label: 'Testing Guide', icon: TestTube2 },
  { id: 'docs', label: 'Documentation', icon: FileText },
  { id: 'blueprintflow', label: 'BlueprintFlow Detail', icon: FolderOpen },
];

export interface UseGuideScrollReturn {
  activeSection: string;
  sidebarOpen: boolean;
  sectionRefs: React.MutableRefObject<{ [key: string]: HTMLElement | null }>;
  scrollToSection: (sectionId: string) => void;
  setSidebarOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export function useGuideScroll(): UseGuideScrollReturn {
  const [activeSection, setActiveSection] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sectionRefs = useRef<{ [key: string]: HTMLElement | null }>({});

  // Detect current section on scroll
  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 100;

      for (const section of sections) {
        const element = sectionRefs.current[section.id];
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(section.id);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Scroll to section
  const scrollToSection = useCallback((sectionId: string) => {
    const element = sectionRefs.current[sectionId];
    if (element) {
      const yOffset = -80;
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
      setActiveSection(sectionId);
      setSidebarOpen(false);
    }
  }, []);

  return {
    activeSection,
    sidebarOpen,
    sectionRefs,
    scrollToSection,
    setSidebarOpen,
  };
}
