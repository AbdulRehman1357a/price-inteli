import Inventory2Icon from "@mui/icons-material/Inventory2";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";

import DashboardPageLayout from "../features/analytics/DashboardPageLayout";

const CARDS = [
  { metricKey: "low_stock_count", icon: <TrendingDownIcon />, color: "warning" },
  { metricKey: "overstock_count", icon: <Inventory2Icon />, color: "info" },
];

export default function AnalyticsInventoryDashboardPage() {
  return (
    <DashboardPageLayout
      title="Inventory Dashboard"
      description="Stock health across every store — what's running low and what's overstocked."
      cards={CARDS}
    />
  );
}
