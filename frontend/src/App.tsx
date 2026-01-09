import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import { Analytics } from "./pages/Analytics";
import { Collaboration } from "./pages/Collaboration";
import { GraphViz } from "./pages/GraphViz";
import { GlobalStateProvider } from "./context/GlobalStateContext";

function App() {
  return (
    <GlobalStateProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/collaboration" element={<Collaboration />} />
            <Route path="/graph" element={<GraphViz />} />
          </Routes>
        </Layout>
      </Router>
    </GlobalStateProvider>
  );
}

export default App;
