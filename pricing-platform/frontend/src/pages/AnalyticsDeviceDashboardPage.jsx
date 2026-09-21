import DevicesOtherIcon from "@mui/icons-material/DevicesOther";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";

import DashboardPageLayout from "../features/analytics/DashboardPageLayout";

const CARDS = [
  { metricKey: "failed_device_updates_count", icon: <ErrorOutlineIcon />, color: "error" },
  { metricKey: "device_uptime_pct", icon: <DevicesOtherIcon />, color: "success" },
];

export default function AnalyticsDeviceDashboardPage() {
  return (
    <DashboardPageLayout
      title="Device Dashboard"
      description="ESL device sync reliability — failed updates and overall uptime."
      cards={CARDS}
    />
  );
}
