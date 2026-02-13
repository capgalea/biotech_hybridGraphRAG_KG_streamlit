import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { MessageSquare, BarChart2, Users, Share2, Menu, X, Database } from "lucide-react";
import clsx from "clsx";

const SidebarItem = ({
  to,
  icon: Icon,
  label,
  active,
}: {
  to: string;
  icon: any;
  label: string;
  active: boolean;
}) => (
  <Link
    to={to}
    className={clsx(
      "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
      active
        ? "bg-blue-600 text-white"
        : "text-gray-300 hover:bg-gray-800 hover:text-white"
    )}
  >
    <Icon size={20} />
    <span className="font-medium">{label}</span>
  </Link>
);

export const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const navItems = [
    { path: "/", icon: MessageSquare, label: "Query & Chat" },
    { path: "/analytics", icon: BarChart2, label: "Analytics" },
    { path: "/collaboration", icon: Users, label: "Collaboration" },
    { path: "/graph", icon: Share2, label: "Graph Viz" },
    { path: "/grant-retrieval", icon: Database, label: "Grant Retrieval" },
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={clsx(
          "bg-gray-900 text-white transition-all duration-300 flex flex-col",
          isSidebarOpen ? "w-64" : "w-20"
        )}
      >
        <div className="p-4 flex items-center justify-between border-b border-gray-800">
          {isSidebarOpen && (
            <h1 className="font-bold text-xl truncate">Biotech GraphRAG</h1>
          )}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-gray-800 rounded-lg"
          >
            {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <SidebarItem
              key={item.path}
              to={item.path}
              icon={item.icon}
              label={isSidebarOpen ? item.label : ""}
              active={location.pathname === item.path}
            />
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
          {isSidebarOpen && <p>© 2025 Biotech GraphRAG</p>}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
};
