import React, { createContext, useContext, useState, ReactNode } from 'react';

// Define shapes for the state we want to persist
interface HomeState {
  query: string;
  result: any;
  llmModel: string;
  enableSearch: boolean;
}

interface AnalyticsState {
  stats: any;
  fundingData: any[];
  trendsData: any[];
  grants: any[];
  
  // UI/Filter State
  activeTrendTab: "total" | "median";
  filterOptions: any;
  filters: {
    institution: string;
    start_year: string;
    grant_type: string;
    broad_research_area: string;
    field_of_research: string;
    funding_body: string;
  };
  showColumnConfig: boolean;
  searchTerm: string;
  debouncedSearch: string;
  sortConfig: { key: string; direction: string };
  columns: any[];
  columnFilters: Record<string, string>;
  debouncedColumnFilters: Record<string, string>;
  activeFilterCol: string | null;
  
  isLoaded: boolean;
}

interface GlobalStateContextType {
  homeState: HomeState;
  setHomeState: React.Dispatch<React.SetStateAction<HomeState>>;
  analyticsState: AnalyticsState;
  setAnalyticsState: React.Dispatch<React.SetStateAction<AnalyticsState>>;
}

// Initial States
const initialHomeState: HomeState = {
  query: "",
  result: null,
  llmModel: "claude-4-5-sonnet",
  enableSearch: false
};

const initialAnalyticsState: AnalyticsState = {
  stats: null,
  fundingData: [],
  trendsData: [],
  grants: [],
  
  activeTrendTab: "total",
  filterOptions: null,
  filters: {
    institution: "",
    start_year: "",
    grant_type: "",
    broad_research_area: "",
    field_of_research: "",
    funding_body: ""
  },
  showColumnConfig: false,
  searchTerm: "",
  debouncedSearch: "",
  sortConfig: { key: "start_year", direction: "DESC" },
  columns: [
    { id: "title", label: "Grant Title", visible: true, width: 250 },
    { id: "pi_name", label: "Researcher Name", visible: true, width: 180 },
    { id: "institution_name", label: "Institution Name", visible: true, width: 180 },
    { id: "grant_status", label: "Status", visible: true, width: 120 },
    { id: "amount", label: "Amount", visible: true, width: 120 },
    { id: "description", label: "Description", visible: false, width: 300 },
    { id: "start_year", label: "Start Year", visible: true, width: 100 },
    { id: "grant_type", label: "Grant Type", visible: false, width: 150 },
    { id: "funding_body", label: "Funding Body", visible: true, width: 120 },
    { id: "field_of_research", label: "Field of Research", visible: false, width: 200 },
    { id: "application_id", label: "Application ID", visible: true, width: 130 },
  ],
  columnFilters: {},
  debouncedColumnFilters: {},
  activeFilterCol: null,
  
  isLoaded: false
};

const STORAGE_KEY = 'biotech_app_state_v1';

const GlobalStateContext = createContext<GlobalStateContextType | undefined>(undefined);

export const GlobalStateProvider = ({ children }: { children: ReactNode }) => {
  // Load initial state from localStorage if available
  const getInitialState = <T,>(key: string, fallback: T): T => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed[key]) return parsed[key];
      }
    } catch (e) {
      console.error(`Error loading state ${key}`, e);
    }
    return fallback;
  };

  const [homeState, setHomeState] = useState<HomeState>(() => 
    getInitialState('home', initialHomeState)
  );
  
  const [analyticsState, setAnalyticsState] = useState<AnalyticsState>(() => {
    const saved = getInitialState<AnalyticsState>('analytics', initialAnalyticsState);
    // Don't mark as loaded initially so it can check for fresh data from server
    return { ...saved, isLoaded: false };
  });

  // Save state to localStorage whenever it changes
  React.useEffect(() => {
    try {
      const stateToSave = {
        home: homeState,
        analytics: {
            ...analyticsState,
            // We might want to keep the data in memory but not persist huge arrays if they exceed quota
            // For now, let's try persisting everything but be ready to clear if quota hit
            isLoaded: false // Always force revalidation on next full reload
        }
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
    } catch (e) {
      console.error("Error saving state to localStorage", e);
      // If quota exceeded, maybe clear old data
      if ((e as any).name === 'QuotaExceededError') {
          // Fallback: don't save the heavy arrays
          const safeAnalytics = { ...analyticsState, grants: [], fundingData: [], trendsData: [] };
          localStorage.setItem(STORAGE_KEY, JSON.stringify({ home: homeState, analytics: safeAnalytics }));
      }
    }
  }, [homeState, analyticsState]);

  return (
    <GlobalStateContext.Provider value={{
      homeState,
      setHomeState,
      analyticsState,
      setAnalyticsState
    }}>
      {children}
    </GlobalStateContext.Provider>
  );
};

export const useGlobalState = () => {
  const context = useContext(GlobalStateContext);
  if (context === undefined) {
    throw new Error('useGlobalState must be used within a GlobalStateProvider');
  }
  return context;
};
