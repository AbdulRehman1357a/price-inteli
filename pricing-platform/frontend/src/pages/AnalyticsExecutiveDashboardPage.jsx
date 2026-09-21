import AttachMoneyIcon from "@mui/icons-material/AttachMoney";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import DevicesOtherIcon from "@mui/icons-material/DevicesOther";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import PriceChangeIcon from "@mui/icons-material/PriceChange";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";

import DashboardPageLayout from "../features/analytics/DashboardPageLayout";

const CARDS = [
  { metricKey: "revenue", icon: <AttachMoneyIcon />, color: "primary" },
  { metricKey: "gross_margin_pct", icon: <ShowChartIcon />, color: "success" },
  { metricKey: "price_changes_count", icon: <PriceChangeIcon />, color: "info" },
  { metricKey: "average_price_change", icon: <TrendingUpIcon />, color: "info" },
  { metricKey: "ai_recommendations_count", icon: <AutoAwesomeIcon />, color: "secondary" },
  { metricKey: "ai_approval_rate_pct", icon: <ThumbUpIcon />, color: "secondary" },
  { metricKey: "low_stock_count", icon: <TrendingDownIcon />, color: "warning" },
  { metricKey: "overstock_count", icon: <Inventory2Icon />, color: "warning" },
  { metricKey: "failed_device_updates_count", icon: <ErrorOutlineIcon />, color: "error" },
  { metricKey: "device_uptime_pct", icon: <DevicesOtherIcon />, color: "error" },
];

export default function AnalyticsExecutiveDashboardPage() {
  return (
    <DashboardPageLayout
      title="Executive Dashboard"
      description="A full overview across pricing, inventory, AI, and devices."
      cards={CARDS}
    />
  );
}
