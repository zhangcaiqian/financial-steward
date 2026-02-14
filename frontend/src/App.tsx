import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Funds from "./pages/Funds";
import AgentChat from "./pages/AgentChat";
import RebalancePlans from "./pages/RebalancePlans";
import CycleTargets from "./pages/CycleTargets";
import Settings from "./pages/Settings";
import Prompts from "./pages/Prompts";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="funds" element={<Funds />} />
          <Route path="holdings" element={<AgentChat />} />
          <Route path="rebalance" element={<RebalancePlans />} />
          <Route path="cycle-targets" element={<CycleTargets />} />
          <Route path="settings" element={<Settings />} />
          <Route path="prompts" element={<Prompts />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
