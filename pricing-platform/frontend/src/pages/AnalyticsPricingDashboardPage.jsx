import AttachMoneyIcon from "@mui/icons-material/AttachMoney";
import PriceChangeIcon from "@mui/icons-material/PriceChange";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";

import DashboardPageLayout from "../features/analytics/DashboardPageLayout";

const CARDS = [
  { metricKey: "revenue", icon: <AttachMoneyIcon />, color: "primary" },
  { metricKey: "gross_margin_pct", icon: <ShowChartIcon />, color: "success" },
  { metricKey: "price_changes_count", icon: <PriceChangeIcon />, color: "info" },
  { metricKey: "average_price_change", icon: <TrendingUpIcon />, color: "info" },
];

export default function AnalyticsPricingDashboardPage() {
  return (
    <DashboardPageLayout
      title="Pricing Dashboard"
      description="Revenue, margin, and how often — and by how much — prices are changing."
      cards={CARDS}
    />
  );
}
